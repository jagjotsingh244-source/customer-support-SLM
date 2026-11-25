"""What the judge sees: one reply of Nova's, the customer message it answers, the conversation before it, and
the evidence Nova had when it wrote it (every tool call and result so far in the chat).

A unit is identified as <run>/<case>/<turn>, e.g. 2026-11-25_golden-sft2a/ord-012/1. Units are built from saved
traces, so any reply of any run can be judged or labelled without calling a model.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "evals" / "runs"
TODAY = "Friday 20 November 2026"


@dataclass
class Unit:
    id: str                  # run/case/turn
    run: str
    case: str
    turn: int                # 1-based customer turn
    customer: str            # the message this reply answers
    reply: str
    history: list[dict]      # earlier customer messages and Nova replies: [{"role", "content"}]
    evidence: list[dict]     # every tool call so far: {"tool", "args", "result"}
    customer_name: str


def _name(system: str) -> str:
    """The signed-in customer's name, from the system prompt Nova was given."""
    m = re.search(r"The signed-in customer is ([^.\n]+)\.", system)
    return m.group(1).strip() if m else ""


def units_of(run: str, trace: dict) -> list[Unit]:
    """One unit per customer turn: the final reply of that turn and the evidence before it."""
    if "error" in trace:
        return []
    msgs = trace["messages"]
    results = {m["tool_call_id"]: m.get("content") for m in msgs if m.get("role") == "tool"}
    out, history, evidence, turn = [], [], [], 0
    customer = ""
    for m in msgs[1:]:
        role = m.get("role")
        if role == "user":
            turn += 1
            customer = m.get("content") or ""
        elif role == "assistant" and m.get("tool_calls"):
            for c in m["tool_calls"]:
                res = results.get(c["id"])
                try:
                    res = json.loads(res)
                except (TypeError, json.JSONDecodeError):
                    pass
                try:
                    args = json.loads(c["function"]["arguments"])
                except (TypeError, json.JSONDecodeError):
                    args = c["function"]["arguments"]
                evidence.append({"tool": c["function"]["name"], "args": args, "result": res})
        elif role == "assistant":
            reply = m.get("content") or ""
            out.append(Unit(f"{run}/{trace['id']}/{turn}", run, trace["id"], turn, customer, reply,
                            list(history), list(evidence), _name(msgs[0].get("content") or "")))
            history += [{"role": "customer", "content": customer}, {"role": "nova", "content": reply}]
    return out


def load_units(run: str) -> dict[str, Unit]:
    path = RUNS / run / "traces.jsonl"
    units = {}
    for line in path.read_text().splitlines():
        for u in units_of(run, json.loads(line)):
            units[u.id] = u
    return units


def get_unit(uid: str) -> Unit:
    run = uid.split("/")[0]
    return load_units(run)[uid]


def evidence_text(u: Unit) -> str:
    """The evidence block shown to the judge and in the label sheet."""
    lines = [f"Known to Nova without a lookup: today is {TODAY}; the signed-in customer is "
             f"{u.customer_name or 'named in its instructions'}."]
    if not u.evidence:
        lines.append("No tool was called before this reply.")
    for e in u.evidence:
        args = json.dumps(e["args"], ensure_ascii=False) if not isinstance(e["args"], str) else e["args"]
        res = json.dumps(e["result"], ensure_ascii=False, default=str) if not isinstance(e["result"], str) else e["result"]
        lines.append(f"- {e['tool']}({args}) returned: {res}")
    return "\n".join(lines)


def _date(s) -> "date | None":
    from datetime import date
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def _ago(d) -> str:
    from config import now
    n = (now().date() - d).days
    return "today" if n == 0 else (f"{n} day{'s' if abs(n) != 1 else ''} before today" if n > 0
                                   else f"in {-n} day{'s' if n != -1 else ''} (after today)")


def date_facts(u: Unit) -> str:
    """Date arithmetic done by code, so the judge never has to count days: every estimated delivery date, last
    scan and delivery in the tracking results, relative to today. Order dates are labelled as such, since they
    are often taken for delivery dates."""
    lines, seen = [], set()
    for e in u.evidence:
        r = e["result"] if isinstance(e["result"], dict) else {}
        for s in r.get("shipments", []) or []:
            key = (s.get("tracking_no"), s.get("status"))
            if key in seen:
                continue
            seen.add(key)
            what = f"Shipment {s.get('tracking_no')} ({s.get('items')}), status {s.get('status')}"
            parts = []
            if (d := _date(s.get("delivered_at"))):
                parts.append(f"delivered {d:%d %b %Y}, {_ago(d)}")
            if (d := _date(s.get("eta"))):
                late = (s.get("status") != "delivered") and d < __import__("config").now().date()
                parts.append(f"estimated delivery {d:%d %b %Y}, {_ago(d)}" + (" (past, not delivered)" if late else ""))
            if (d := _date(s.get("last_scan_at"))):
                parts.append(f"last scan {d:%d %b %Y}, {_ago(d)}")
            lines.append(f"- {what}: " + "; ".join(parts) if parts else f"- {what}: no dates")
        if e["tool"] == "get_order_status" and (d := _date(r.get("placed_at"))) and r.get("order_id") not in seen:
            seen.add(r.get("order_id"))
            lines.append(f"- Order {r.get('order_id')} was placed (ordered) {d:%d %b %Y}, {_ago(d)}; this is not "
                         "a shipping or delivery date.")
        if e["tool"] == "propose_return" and r.get("delivered_on") and (d := _date(r["delivered_on"])):
            lines.append(f"- Order {r.get('order_id')} line {r.get('line_no')} was delivered {d:%d %b %Y}, {_ago(d)}.")
    return "\n".join(lines) if lines else "(no dates in the evidence)"


def history_text(u: Unit, limit: int = 6) -> str:
    h = u.history[-limit:]
    if not h:
        return "(this is the first message of the chat)"
    return "\n".join(f"{'Customer' if x['role'] == 'customer' else 'Nova'}: {x['content']}" for x in h)
