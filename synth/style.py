"""Style rules a reply can be checked against with code: no model, no judgement calls.

Used twice: the generator asks the teacher to rewrite a reply that breaks one (synth/generate.py), and the
filtering step rejects conversations that still break one. Each rule comes from counting the first teacher
conversations (synth/teacher_rules.py, r2).
"""

import re

MAX_WORDS = 70
# A closing question that offers more help instead of answering. Offers of a teammate are allowed here: when
# Nova cannot do what is asked, offering a person is right, and whether it was right is the escalation check's job.
CLOSING_OFFER = re.compile(
    r"(would you like (me )?to|do you want me to|shall i|can i help|is there anything else|anything else i can)"
    r"[^.?!]*\?\s*$", re.I)
TEAMMATE = re.compile(r"teammate|someone|a person|human|support team|agent", re.I)
# Things Nova must not promise unless a tool or the help center mentioned them.
PROCESS_WORDS = ("email", "sms", "text message", "label", "link", "login", "log in", "password", "otp",
                 "notification")


def style_problems(reply: str, sources: str) -> list[str]:
    """What is wrong with this reply, in words the teacher can act on. `sources` is every tool result and
    search result the conversation has had, as text."""
    out = []
    text = reply.strip()
    if m := CLOSING_OFFER.search(text):
        if not TEAMMATE.search(m.group(0)):
            out.append("it ends with an offer of more help; end with the answer itself")
    if "\n" in text:
        out.append("it has several paragraphs; write one")
    if (n := len(text.split())) > MAX_WORDS:
        out.append(f"it has {n} words; use at most {MAX_WORDS}")
    if "**" in text or re.search(r"^\s*([-*•]|\d+\.)\s", text, re.M):
        out.append("it uses bold or a list; write plain sentences")
    low, src = text.lower(), sources.lower()
    invented = [w for w in PROCESS_WORDS if re.search(rf"\b{w}s?\b", low) and not re.search(rf"\b{w}", src)]
    if invented:
        out.append(f"it mentions {', '.join(invented)}, which no tool or help-center result mentioned; "
                   "leave out what you were not told")
    return out


REWRITE_NOTE = ("(Note from your supervisor, not from the customer: rewrite your last reply to the customer. "
                "Keep the same facts and citations, call no tools, and fix this: {problems}. Write only the "
                "rewritten reply.)")
