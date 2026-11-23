"""The simulated customer: a model role-playing a NimbusCart shopper with a hidden goal and limited knowledge.

It sees only what a customer would see: Nova's replies, never tool calls or results. It runs at a higher
temperature than the teacher, so the two do not settle into one polite voice. It ends a conversation with
###DONE### when its goal is met or ###GAVE_UP### after two unhelpful replies; the markers are stripped before
anything is recorded, and the closing line before them is kept as the customer's last message, so Nova also
learns to answer "thanks, that's all" without calling a tool.
"""

import re

from synth.scenarios import Scenario

DONE, GAVE_UP = "###DONE###", "###GAVE_UP###"
MARKER = re.compile(r"\s*###(DONE|GAVE_UP)###\s*")

PROMPT = """\
You are role-playing a NimbusCart customer chatting with the store's support assistant. NimbusCart is an online \
store in India.
Persona: {persona}
Your hidden goal: {goal}
What you know:
{knowledge}
What you do NOT know: order numbers unless listed above, carrier names, tracking numbers, store policies, \
delivery estimates.
Style rules: {style}

- Write only the customer's next message: plain chat text, no quotes, no labels, no stage directions.
- Never describe your goal or say that you have one. Never invent facts that are not in what you know.
- Reveal information only when asked for it, one piece at a time.
- When your goal is met, reply with a short closing line, then {done}.
- If support fails to help you twice, reply with a frustrated line, then {gave_up}.
- If support hands you to a person or opens a ticket for you, that counts as your goal being met."""

DEFAULT_PERSONA = {"name": "plain", "description": "An ordinary shopper.",
                   "style": "Short, casual messages, like a chat on a phone. Lowercase is fine."}


class CustomerSimulator:
    def __init__(self, client, model: str, scenario: Scenario, persona: dict | None = None,
                 temperature: float = 1.0, sampling: dict | None = None):
        self.client, self.model, self.temperature = client, model, temperature
        self.sampling = sampling or {}
        p = persona or DEFAULT_PERSONA
        self.system = PROMPT.format(persona=p["description"], goal=scenario.goal, style=p["style"],
                                    knowledge="\n".join(f"- {k}" for k in scenario.knowledge),
                                    done=DONE, gave_up=GAVE_UP)
        # The simulator's own chat: Nova's replies are its "user" turns, its messages are its "assistant" turns.
        self.history: list[dict] = []
        self.ended: str | None = None          # "done" or "gave_up" once a marker appears
        self.usage = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0}

    def _ask(self, cue: str) -> str:
        msgs = [{"role": "system", "content": self.system}, *self.history, {"role": "user", "content": cue}]
        r = self.client.chat.completions.create(model=self.model, messages=msgs, temperature=self.temperature,
                                                max_tokens=200, **self.sampling)
        self.usage["calls"] += 1
        if r.usage:
            self.usage["prompt_tokens"] += r.usage.prompt_tokens
            self.usage["completion_tokens"] += r.usage.completion_tokens
        text = (r.choices[0].message.content or "").strip()
        if m := MARKER.search(text):
            self.ended = "done" if m.group(1) == "DONE" else "gave_up"
            text = text[:m.start()].strip()
        return text

    def opening(self) -> str:
        cue = "(The chat window has opened. Write your first message to support.)"
        text = self._ask(cue)
        self.history += [{"role": "user", "content": cue}, {"role": "assistant", "content": text}]
        return text

    def respond(self, nova_reply: str) -> str | None:
        """The customer's next message, or None when there is nothing more to say (a marker with no closing line)."""
        text = self._ask(nova_reply)
        self.history += [{"role": "user", "content": nova_reply}, {"role": "assistant", "content": text}]
        return text or None
