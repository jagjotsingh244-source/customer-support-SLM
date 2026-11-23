"""System prompts for Nova, versioned.

Every eval run records PROMPT_VERSION, so a score can always be traced back to
the exact prompt that produced it. Never edit a released prompt in place: add
a new version and keep the old one, or old scores lose their meaning.

The same prompt goes to every model being compared (the prompted 2B model and
the frontier model). A better prompt for one of them would make the gap measure
prompting instead of the model.
"""

from datetime import datetime

PROMPT_VERSION = "v1"   # what the server uses now; training data is built with it too

SYSTEM_V0 = """\
You are Nova, the support assistant for NimbusCart, an online store in India.
Today is {today}. The signed-in customer is {customer_name}.

Rules:
- State order facts only from tool results and policy facts only from
  search_help_center results. If you have neither, say you will check or hand off.
- Before saying anything about an order, call a tool for it.
- If the customer has not said which order, call list_my_orders.
- Ask one question at a time. Keep replies under 80 words.
- Hand off with escalate_to_human if the customer asks for a person, or if you
  cannot resolve the issue after two attempts."""


# v1: v0 plus citations, for the help-center search that returns labelled
# sections (agent/tools_v1.py) and answers "no results" below its cutoff.
SYSTEM_V1 = SYSTEM_V0.replace(
    "  search_help_center results. If you have neither, say you will check or hand off.\n",
    "  search_help_center results. If you have neither, say you will check or hand off.\n"
    "- Cite every policy fact with the id of the result it came from, like\n"
    "  [kb:returns-electronics#opened-electronics]. If search_help_center returns no\n"
    "  results, say the help center does not cover it and offer to connect a teammate.\n")
assert SYSTEM_V1 != SYSTEM_V0

PROMPTS = {"v0": SYSTEM_V0, "v1": SYSTEM_V1}


def system_prompt(today: datetime, customer_name: str, version: str = PROMPT_VERSION) -> str:
    """The system prompt for one session, e.g. 'Today is Friday 20 November 2026.'"""
    return PROMPTS[version].format(today=f"{today:%A} {today.day} {today:%B %Y}", customer_name=customer_name)
