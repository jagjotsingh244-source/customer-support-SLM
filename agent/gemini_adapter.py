"""Let the agent loop talk to Gemini on Vertex AI as if it were an OpenAI-style server.

agent/loop.py speaks the OpenAI chat format, because vLLM serves the 2B model
that way. A Vertex AI express-mode API key only reaches Gemini through Google's
own generateContent API, so this adapter translates, and nothing else changes:
the same system prompt, the same six tool schemas and the same loop.

    client = GeminiChatClient(api_key=os.environ["VERTEX_API_KEY"],
                              project=os.environ["VERTEX_PROJECT"], location="global")
    run_turn(client, "gemini-4-hydrogen", messages, TOOLS, REGISTRY, session)

The key is tied to one Google Cloud project; without project and location the
SDK sends requests to the project's home region, where Gemini is not served.

A Gemini Developer API key (AI Studio) works too, with vertexai=False: the
same models, reached without a Cloud project.

What it translates, and the differences that remain:
- system message -> system_instruction; user turns -> user contents;
  assistant tool calls -> functionCall parts; tool results -> functionResponse parts.
- Gemini's own reply is kept verbatim in the assistant message
  ("gemini_content") and sent back unchanged on the next request. Gemini
  checks signatures on its earlier function calls, so a rebuilt copy could fail.
- Temperature is passed through (0.2, same as the 2B). Gemini 2.5 Pro always
  thinks before answering and its thinking counts against max_output_tokens,
  so the loop's 512-token cap is raised to MIN_OUTPUT_TOKENS here; the visible
  reply is still limited by the prompt ("under 80 words").
- Gemini may not return call ids; ids are made up here (call_0, call_1, ...)
  and mapped back to function names for the results.
"""

import json
import time
from types import SimpleNamespace

from google import genai
from google.genai import errors, types
from openai.types.chat import ChatCompletion

MIN_OUTPUT_TOKENS = 8192
RETRY_CODES = {429, 500, 503}          # rate limit (free tier: requests per minute) and transient server errors
RETRY_WAITS = (10, 20, 40, 60, 60)     # seconds; about 3 minutes in all before giving up
FINISH = {"STOP": "stop", "MAX_TOKENS": "length", "SAFETY": "content_filter"}


def _declarations(tools: list[dict]) -> list[types.Tool]:
    return [types.Tool(function_declarations=[
        types.FunctionDeclaration(name=t["function"]["name"], description=t["function"]["description"],
                                  parameters_json_schema=t["function"]["parameters"])
        for t in tools])]


def _contents(messages: list[dict]) -> tuple[str | None, list[types.Content]]:
    """OpenAI-format messages -> (system instruction, Gemini contents)."""
    system, contents, names = None, [], {}
    for m in messages:
        role = m["role"]
        if role == "system":
            system = m["content"]
        elif role == "user":
            contents.append(types.Content(role="user", parts=[types.Part(text=m["content"])]))
        elif role == "assistant":
            for c in m.get("tool_calls") or []:
                names[c["id"]] = c["function"]["name"]
            if "gemini_content" in m:                      # Gemini's own turn: replay it unchanged
                contents.append(types.Content.model_validate(m["gemini_content"]))
            else:                                          # e.g. the loop's fallback hand-off text
                contents.append(types.Content(role="model", parts=[types.Part(text=m.get("content") or "")]))
        elif role == "tool":
            result = json.loads(m["content"])
            part = types.Part.from_function_response(
                name=names[m["tool_call_id"]],
                response=result if isinstance(result, dict) else {"result": result})
            if contents and contents[-1].role == "user" and contents[-1].parts[0].function_response:
                contents[-1].parts.append(part)            # all results of one turn in one content
            else:
                contents.append(types.Content(role="user", parts=[part]))
    return system, contents


def _completion(resp, model: str) -> ChatCompletion:
    """Gemini response -> an OpenAI ChatCompletion the loop already understands."""
    cand = resp.candidates[0]
    parts = cand.content.parts or []
    text = "".join(p.text for p in parts if p.text and not p.thought) or None
    calls = [{"id": f"call_{i}", "type": "function",
              "function": {"name": p.function_call.name, "arguments": json.dumps(p.function_call.args or {})}}
             for i, p in enumerate(p for p in parts if p.function_call)]
    u = resp.usage_metadata
    finish = "tool_calls" if calls else FINISH.get(str(cand.finish_reason).split(".")[-1], "stop")
    return ChatCompletion.model_validate({
        # the model Google says served the reply, so every trace records it, not just what was asked for
        "id": resp.response_id or "gemini", "object": "chat.completion", "created": 0,
        "model": resp.model_version or model,
        "usage": {"prompt_tokens": u.prompt_token_count or 0,
                  # visible output + thinking, so token budgets compare like for like
                  "completion_tokens": (u.candidates_token_count or 0) + (u.thoughts_token_count or 0),
                  "total_tokens": u.total_token_count or 0},
        "choices": [{"index": 0, "finish_reason": finish,
                     "message": {"role": "assistant", "content": text, "tool_calls": calls or None,
                                 "gemini_content": cand.content.model_dump(exclude_none=True)}}]})


class GeminiChatClient:
    """Exposes client.chat.completions.create(...), the one call agent/loop.py makes."""

    def __init__(self, api_key: str | None = None, project: str | None = None,
                 location: str = "global", genai_client=None, vertexai: bool = True):
        """vertexai=False uses a Gemini Developer API (AI Studio) key: no project or location."""
        if genai_client is None:
            genai_client = (genai.Client(vertexai=True, api_key=api_key, project=project, location=location)
                            if vertexai else genai.Client(api_key=api_key))
        self._genai = genai_client
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, *, model, messages, tools, temperature, max_tokens, **_):
        """One model call. Sampling settings other than temperature are ignored (vLLM-only).

        Rate-limit and server errors are retried with waits; the waiting counts in the
        call's measured latency, so ceiling latency is an upper bound on a free tier.
        """
        system, contents = _contents(messages)
        config = types.GenerateContentConfig(
            system_instruction=system, tools=_declarations(tools), temperature=temperature,
            max_output_tokens=max(max_tokens, MIN_OUTPUT_TOKENS),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True))
        for wait in (*RETRY_WAITS, None):
            try:
                resp = self._genai.models.generate_content(model=model, contents=contents, config=config)
                return _completion(resp, model)
            except errors.APIError as e:
                if wait is None or e.code not in RETRY_CODES:
                    raise
                time.sleep(wait)
