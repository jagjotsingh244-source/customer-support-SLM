# What a tool call is, token by token

A tool call is text in a format the model was trained to write. Nothing runs inside the model:

1. The chat template renders the tool definitions into the prompt as text.
2. The model writes a tool-call block instead of an answer.
3. The server's parser (vLLM `--tool-call-parser qwen3_coder`) turns that text into `tool_calls` in the response.
4. `agent/loop.py` checks the arguments and runs the function.
5. The result goes back as a `tool` message, rendered as a tool response, and the model is called again.
6. Repeat until the model replies with text.

So a call can fail in three places: the **model** (wrong tool, wrong arguments, or no call), the **parser** (a call
it cannot read stays as text in `content`), or **our code** (validation or the function itself).

Files:
- `render_round_trip.py` → `round_trip.txt`: one full round trip (Nova's system prompt v1, the six real tools,
  "Where is my order 11904?", the `get_tracking` call and its real result from the local database) rendered by
  Qwen3.5-2B's template, split into marked parts with token counts. Tokenizer only, runs on the laptop.
- `serving/raw_tool_response.py` and `serving/notebooks/tool-call-parser.ipynb`: the same request sent to vLLM on a
  T4, once with the parser and once without, raw response JSON kept (`vllm_with_parser.json`,
  `vllm_without_parser.json`).

## Findings from the render (2026-11-23)

1. **The tool definitions come first, before Nova's own prompt.** The template opens the system turn with
   `# Tools`, the six schemas (one JSON object per line inside `<tools>`), the call-format example and an
   `<IMPORTANT>` reminder; Nova's system prompt is appended after them in the same turn. The model reads 780 tokens
   of tool text before the first word of Nova's rules.
2. **The tool result is a user turn.** There is no tool role in the rendered prompt: the result is
   `<|im_start|>user` + `<tool_response>` … `</tool_response>`. The model tells a result from a customer message only
   by that wrapper. This is also where an injected instruction inside a tool result would sit.
3. **Which markers are single tokens.** `<tool_call>`, `</tool_call>`, `<tool_response>`, `</tool_response>`,
   `<think>`, `</think>`, `<|im_start|>`, `<|im_end|>` are one token each. `<function=`, `<parameter=`,
   `</function>`, `</parameter>`, `<tools>` and `<IMPORTANT>` are three ordinary tokens each, so the model can
   misspell them; a misspelt or unclosed call is exactly what the parser cannot read.
4. **The template rewrites history.** While the tool round trip is the latest exchange, the assistant turn that made
   the call keeps an empty `<think></think>` block. Once the customer sends another message, earlier assistant turns
   are rendered without it. So the prompt for turn two is not turn one's prompt plus new text, and training
   conversations must be rendered by the same template, turn by turn, not concatenated.
5. **Cost of one round trip:** first model pass 1,020 tokens; the second pass adds the call (39 tokens) and the
   result (159 tokens; the JSON alone is 150) for 1,218. Tool text is 780 of the 1,020, over the 700 allotted in
   `DESIGN.md`.

## The loop's check for an unread call

`agent/loop.py` now looks for tool-call markup (`<tool_call>` or `<function=`) in every reply's text. If the server
returned no parsed call but the text holds one, it is a **format error**, not a reply: it is counted in
`trace["format_errors"]`, kept in `trace["raw_reply"]`, never shown to the customer, and the turn ends with the
hand-off reply. A reply with no text and no call counts the same way (see the vLLM result below). Eval reports print
the count. None of the saved runs so far had either (all 11 trace files searched).
Tests: `tests/test_tool_markup.py`.

## vLLM with and without the parser

Kaggle T4, vLLM 0.34.0, 2026-11-23. Same request each time: Nova's prompt, the six tools, "Where is my order
11904?", greedy. Raw responses: `vllm_with_parser.json`, `vllm_without_parser.json`.

| Server | `tool_choice` | HTTP | `content` | `tool_calls` | Completion tokens |
|---|---|---|---|---|---|
| parser on (serving flags) | `auto` | 200 | null | `get_tracking({"order_id": 11904})` | 31 |
| parser on | `none` | 200 | null | null | 31 |
| parser off | `auto` | 400 | — | — | — |
| parser off | `none` | 200 | the raw `<tool_call>…</tool_call>` text | null | 31 |

1. **With the parser, the call arrives structured.** `finish_reason` is `tool_calls`, `content` is null, and the
   arguments are a JSON string with `order_id` already an integer: the parser converted `11904` using the tool's
   schema. vLLM gives the call its own id (`chatcmpl-tool-…`), which the loop sends back with the result.
2. **Without the parser, the call stays as text.** vLLM refuses `tool_choice="auto"` outright (HTTP 400: "auto"
   tool choice requires `--enable-auto-tool-choice` and `--tool-call-parser`). With `"none"` the tools are still in
   the prompt, the model writes the same 31-token call, and it comes back as plain text in `content` with
   `finish_reason: stop`. To code that only reads `content`, it looks like a reply. This is what the loop's markup
   check catches.
3. **The surprise: parser on plus `tool_choice="none"` loses the call.** The model still generated 31 tokens, but
   the response has no text and no call. Nothing is wrong with the HTTP status, so the failure is silent: the old
   loop would have handed the customer an empty reply. The loop never sends `"none"`, but an empty reply with no
   call is now a format error too.
4. **The laptop render matches the server.** vLLM counted 1,020 prompt tokens, exactly the first-pass count from
   `round_trip.txt`. The template vLLM applies is the one rendered here, so token budgets measured on the laptop
   hold on the server.

Server logs (not kept, about 57 KB each, mostly weight-loading warnings) showed one expected error line on the T4:
FlashAttention 2 needs compute capability 8.0 or higher, so vLLM uses another attention backend.
