"""Grounding checks run on every reply Nova sends.

A reply is grounded when every number in it and every help-center citation can
be traced to tool results Nova was given earlier in the same conversation.

- Numbers: each number in the reply must appear among the numbers of those tool
  results (order lookups and help-center results alike), so an order number or
  a date taken from a tool counts. A number that is merely true, or that sits
  somewhere else in the help center, or that the customer typed, does not.
- Citations: each [kb:<id>] must be the id of a section a help-center search
  returned in this conversation.

The agent loop records the issues in the trace, and the eval scorer recomputes
them from saved messages, so old runs can be checked too. Violations are logged,
never fixed silently.
"""

import json
import re

NUM = re.compile(r"\d+(?:[.,]\d+)*")
CITE = re.compile(r"\[kb:([a-z0-9\-#]+)\]")


def _num(token: str) -> str:
    """'1,299' and '1299.00' -> '1299'; '2.5' stays '2.5'. Commas are thousands separators."""
    t = token.replace(",", "")
    if "." in t:
        t = t.rstrip("0").rstrip(".")
    return t.lstrip("0") or "0"


def numbers(text: str) -> set[str]:
    return {_num(n) for n in NUM.findall(text)}


def retrieved_ids(tool_contents: list[str]) -> set[str]:
    """Section ids from help-center results: the new tool's results[].id and the first tool's section_id."""
    ids = set()
    for content in tool_contents:
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, dict) and isinstance(data.get("results"), list):
            ids |= {r["id"] for r in data["results"] if isinstance(r, dict) and "id" in r}
        elif isinstance(data, list):
            ids |= {r["section_id"] for r in data if isinstance(r, dict) and "section_id" in r}
    return ids


def grounding_issues(reply: str, tool_contents: list[str]) -> list[str]:
    reply = reply or ""
    cited = CITE.findall(reply)
    known = retrieved_ids(tool_contents)
    evidence = set().union(*(numbers(c) for c in tool_contents)) if tool_contents else set()
    bare = CITE.sub(" ", reply)  # the digits inside a citation id are not claims
    issues = [f"number {n} not in tool results" for n in sorted(numbers(bare)) if n not in evidence]
    issues += [f"cites {c}, not retrieved" for c in dict.fromkeys(cited) if c not in known]
    return issues


def _plain(content: str) -> str:
    """Tool results as the model should read them: older runs saved JSON with \\u escapes."""
    try:
        return json.dumps(json.loads(content), ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        return content or ""


def tool_contents_before(messages: list[dict], end: int) -> list[str]:
    return [_plain(m.get("content")) for m in messages[:end] if m.get("role") == "tool"]


def check_conversation(messages: list[dict]) -> list[dict]:
    """Every final reply in a saved conversation with its issues and citations."""
    out = []
    for i, m in enumerate(messages):
        if m.get("role") == "assistant" and not m.get("tool_calls"):
            tools = tool_contents_before(messages, i)
            out.append({"reply": m.get("content") or "", "issues": grounding_issues(m.get("content"), tools),
                        "cited": list(dict.fromkeys(CITE.findall(m.get("content") or ""))),
                        "retrieved": sorted(retrieved_ids(tools))})
    return out
