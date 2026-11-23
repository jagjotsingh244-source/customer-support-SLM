"""Conversation state and the context budget: a short, predictable prompt on every turn.

A 2B model does best with a context that is short and always laid out the same way, so the prompt is
treated like memory in an embedded system: a fixed budget, split into fixed parts, enforced by code before
every model call (numbers measured in DESIGN.md, "Budgets"):

    system prompt      fixed, written once (agent/prompts.py)
    tool schemas       fixed (agent/tools_v2.py)
    state block        rebuilt every turn from tool results: the order in focus, facts already
                       confirmed, any open return proposal
    recent history     the last two turns as the customer said them and as Nova answered (their tool
                       calls and results are left out: the state holds those facts); older turns dropped
    this turn          in full: the customer's message, every tool call and result so far
    the reply          max_tokens on the request

The state carries what the dropped history used to carry. Code builds it from tool results; the model
never writes it ("summarise the conversation so far" from a 2B model drifts; a tool result does not).
It goes at the end of the system prompt, so the model finds it in the same place on every turn.

fit() takes no model and no tokenizer, only a counting function, so the training-data pipeline can apply
exactly the same trimming to the conversations it trains on.
"""

import json
from dataclasses import dataclass, field
from functools import cache

PROMPT_BUDGET = 4_200   # tokens sent to the model per call, before the reply; see DESIGN.md "Budgets"
KEEP_TURNS = 3          # customer turns sent: this one in full, the two before it as message and reply
MAX_CALLS_PER_STEP = 2  # parallel tool calls run per model step; the rest are answered "skipped"


class ContextOverflow(Exception):
    """Even the current turn alone does not fit the budget."""


# The state ----------------------------------------------------------------------------------------------

def _boxes(result: dict) -> str:
    boxes = result.get("shipments", [])
    parts = []
    for b in boxes:
        s = b["status"].replace("_", " ")
        if len(boxes) > 1:                                     # which box is which matters only when split
            s = f"{b.get('items', 'box')}: {s}"
        if b.get("tracking_no"):
            s += f", tracking {b['carrier']} {b['tracking_no']}"
        if b.get("eta") and b["status"] != "delivered":
            s += f", ETA {b['eta']}"
        if b.get("last_scan_location"):
            s += f", last scan {b['last_scan_location']} {str(b.get('last_scan_at', ''))[:10]}"
        parts.append(s)
    return "; ".join(parts)


def one_line(tool: str, result: dict) -> str | None:
    """One line of fact from a successful tool result, or None if the result adds no fact about an order.
    Item names are not repeated here: they head the order's line in the state (State.render)."""
    if tool == "get_tracking":
        return _boxes(result) if result.get("shipped") else result.get("note")
    if tool == "get_order_status":
        line = f"{result['status'].replace('_', ' ')}, total ₹{result.get('total_inr')}"
        if isinstance(result.get("returns"), list):
            line += "; return " + ", ".join(r["status"] for r in result["returns"])
        if isinstance(result.get("refunds"), list):
            line += "; refund " + ", ".join(f"{f['status']} ₹{f['amount_inr']}" for f in result["refunds"])
        return line
    if tool == "propose_return" and not result.get("eligible"):
        return f"{result['item']} cannot be returned: {result['reason'].replace('_', ' ')}"
    return None


def items_in(tool: str, result: dict) -> str | None:
    """The order's item names, from whichever result lists them."""
    if tool == "get_order_status" and result.get("items"):
        return ", ".join(i["name"] for i in result["items"])
    if tool == "get_tracking" and result.get("shipments"):
        return ", ".join(b["items"] for b in result["shipments"] if b.get("items"))
    if tool == "propose_return" and result.get("item"):
        return result["item"]
    return None


@dataclass
class State:
    """What the conversation has established, built only from tool results.

    Each order is labelled by its items ("1080p webcam = order 11904"), because customers name orders by
    what is in them. Tried on the 15-turn chat with the real 2B model (evals/long_chat.py): a bare
    "Order in focus: 10689" line made it look up 10689 when the customer said "going back to the webcam
    order" (9 of 14 turns right); dropping the focus line, 11 of 14; this layout, 14 of 14.
    """
    focus_order: int | None = None
    # order_id -> {tool: one line}; orders most recent last. One line per kind of lookup, so a status
    # lookup does not wipe the tracking number found earlier.
    facts: dict[int, dict[str, str]] = field(default_factory=dict)
    items: dict[int, str] = field(default_factory=dict)       # order_id -> its item names
    open_proposal: str | None = None
    # Set by a successful escalate_to_human. Without it, a follow-up after the hand-off ("so I just wait?")
    # reached a model that no longer saw the hand-off, which then looked the order up and opened a second ticket.
    handoff: str | None = None

    def update(self, tool: str, args: dict | None, result: dict) -> None:
        """Called by the loop after every tool call, with the call's arguments and its result."""
        if tool == "escalate_to_human" and isinstance(result, dict) and result.get("handed_off"):
            reason = (args or {}).get("reason", "other").replace("_", " ")
            self.handoff = f"ticket {result['ticket_id']} ({reason})"
            return
        if not isinstance(result, dict) or "error" in result or not args or "order_id" not in args:
            return
        oid = args["order_id"]
        self.focus_order = oid
        if names := items_in(tool, result):
            self.items.setdefault(oid, names)
        if tool == "propose_return" and result.get("eligible"):
            self.open_proposal = f"#{result['proposal_id']}: {result['item']} from order {oid}"
        line = one_line(tool, result)
        known = self.facts.pop(oid, {})                        # re-insert: most recent last
        if line:
            known[tool] = line
        self.facts[oid] = known

    def label(self, oid: int) -> str:
        return f"{self.items[oid]} = order {oid}" if oid in self.items else f"order {oid}"

    def render(self, max_orders: int = 4) -> str:
        lines = ["Conversation state (from tool results earlier in this chat):"]
        for oid, known in list(self.facts.items())[-max_orders:]:
            lines.append(f"- {self.label(oid)}" + (": " + "; ".join(known.values()) if known else ""))
        if self.focus_order:
            names = f" ({self.items[self.focus_order]})" if self.focus_order in self.items else ""
            lines.append(f"Last order looked up: {self.focus_order}{names}. "
                         "If the customer names another item, use that item's order.")
        else:
            lines.append("No order looked up yet.")
        if self.open_proposal:
            lines.append(f"Return waiting for the customer's Confirm: {self.open_proposal}")
        if self.handoff:
            lines.append(f"Already handed to the support team: {self.handoff}. A teammate will reply; "
                         "do not open another ticket for it.")
        return "\n".join(lines)


# The trimmer ----------------------------------------------------------------------------------------------

def condense(turn: list[dict]) -> list[dict]:
    """An earlier turn as the customer and Nova saw it: the customer's message and Nova's last reply.

    Tool calls and results are dropped together (never one without the other), and so is any text written
    alongside a call. The facts those results held are in the state block. A turn that ended without a
    reply (the loop's fallback is a reply, so this is rare) keeps only the customer's message."""
    replies = [m for m in turn[1:] if m["role"] == "assistant" and m.get("content") and not m.get("tool_calls")]
    return turn[:1] + replies[-1:]


def fit(messages: list[dict], budget: int, count_tokens, keep_turns: int = KEEP_TURNS) -> list[dict]:
    """The system message, the current turn in full, and as many earlier turns as fit, condensed.

    A turn starts at a customer message. The current turn (the last one) is sent whole: the model must see
    every call and result it has made for this message. Up to `keep_turns - 1` earlier turns are sent as
    condense() leaves them, so Nova always sees what it last told the customer, however many tool calls
    that took. Measured on teacher conversations: counting messages instead (at most 6) hid every earlier
    reply in half of the later model calls, because one lookup turn alone is 6 messages. The oldest turns
    are dropped first until the prompt fits; if the current turn alone does not fit, ContextOverflow.
    """
    head, rest = messages[:1], messages[1:]
    starts = [i for i, m in enumerate(rest) if m["role"] == "user"]
    if not starts:
        raise ValueError("no customer message to answer")
    turns = [rest[a:b] for a, b in zip(starts, starts[1:] + [len(rest)])]
    current, earlier = turns[-1], [condense(t) for t in turns[:-1]][-(keep_turns - 1):] if keep_turns > 1 else []
    while earlier and count_tokens(head + [m for t in earlier for m in t] + current) > budget:
        earlier = earlier[1:]
    out = head + [m for t in earlier for m in t] + current
    if (n := count_tokens(out)) > budget:
        raise ContextOverflow(f"{n} tokens for the current turn alone, budget {budget}")
    return out


# Counting with the model's own tokenizer, on the rendered template ------------------------------------------

@cache
def _tokenizer(model_id: str):
    from transformers import AutoTokenizer       # only where prompts are counted, not on import
    return AutoTokenizer.from_pretrained(model_id)


def token_counter(tools: list[dict], model_id: str = "Qwen/Qwen3.5-2B"):
    """count(messages) -> tokens of the prompt exactly as the server builds it: the chat template applied with
    the tool schemas and the generation cue. Never len(text) / 4."""
    from agent.chat_template import for_template
    tok = _tokenizer(model_id)

    def count(messages: list[dict]) -> int:
        return len(tok.apply_chat_template(for_template(messages), tools=tools, add_generation_prompt=True,
                                           tokenize=True, return_dict=True)["input_ids"])
    return count


@dataclass
class Context:
    """Everything the loop needs to build each request: the state, the budget and a counter."""
    count_tokens: object
    budget: int = PROMPT_BUDGET
    keep_turns: int = KEEP_TURNS
    state: State = field(default_factory=State)

    def prepare(self, messages: list[dict]) -> list[dict]:
        """What is sent: the system prompt with the state block appended, then the fitted history.
        `messages` itself (the full conversation, kept for traces) is not changed."""
        system = {"role": "system", "content": messages[0]["content"] + "\n\n" + self.state.render()}
        return fit([system] + messages[1:], self.budget, self.count_tokens, self.keep_turns)


def parse_args(raw: str | None) -> dict | None:
    try:
        args = json.loads(raw or "")
    except (json.JSONDecodeError, TypeError):
        return None
    return args if isinstance(args, dict) else None
