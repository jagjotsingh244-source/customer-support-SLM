# Generating conversations with a coding agent as the teacher

When no GPU is available for the teacher model, a coding agent can play both sides instead: Nova (the support
assistant) and the simulated customer. Everything else stays the same as a GPU run: the generator
(`synth/generate.py`) picks the situation and a real customer, **runs every tool call against the real database
and help center**, records the student's view of each step, sends weak replies back for a rewrite, and the
conversations go through the same checks (`synth/verify.py`). Only who writes each message changes.

`synth/agent_server.py` is a "mailbox" that looks like a model server to the generator: each request waits in
`data/synthetic/agent-queue/inbox/` until the agent answers it.

## Which model may be the teacher

The conversations become training data for another model, so the teacher must be a model whose terms allow
that. Use an **open-weights model** (for example Qwen or gpt-oss under Apache-2.0) if the agent offers one: its
output can be trained on freely. A provider's model may come with terms that limit training other models on its
output, and heavy automated use can get an account restricted. To keep that risk low:

- keep runs small (the plan here is 60 conversations) and use two or three agents, not more;
- the adversarial customers (prompt injection, pretending to be staff, asking for the system prompt) are left out
  of this plan (`synth/agent_plan_adversarial.json`): they are generated with the open-weights teacher instead;
- stop at the first warning, rate limit or policy message, and do not retry around it.

Record the agent and model in `--teacher`; it is stored in every conversation, so these can be told apart later.

## Setup (once)

```bash
docker compose up -d                      # the orders database (port 5433)
uv sync --group rag --group local-model --group data
```

## Run

Terminal 1, the mailbox:

```bash
uv run python -m synth.agent_server serve --teacher "antigravity / gemini-4-hydrogen (low)"
```

Terminal 2, the generator. `--workers` is how many conversations run at once: use one per agent (2-3 agents, 2-3
workers); it waits as long as the agents need:

```bash
TEACHER_URL=http://127.0.0.1:8765 TEACHER_API_KEY=local uv run --group rag --group local-model --group data \
  python -m synth.generate --cells-file synth/agent_plan.json --label agent-r1 --workers 3 --stall-s 3600
```

`synth/agent_plan.json` lists the scenario x persona cells that still have fewer than three kept conversations,
and how many to make for each (60 in all; the adversarial cells are in a separate plan).

## The agent's loop

Run several agents in parallel, each with its own name (`a1`, `a2`, ...). `next` claims a request, so two agents
never answer the same one. Each agent repeats until the generator in terminal 2 prints its summary:

1. `uv run python -m synth.agent_server next --agent a1`. It shows who to play (NOVA or CUSTOMER), the
   instructions for that role (in full the first time, then only the lines that changed; `--full` shows all again)
   and the conversation so far, including every tool result.
2. Write the next message as that role, following the instructions exactly:
   - as **NOVA**: call a tool when the answer needs order or policy facts,
     `uv run python -m synth.agent_server answer <id> --call get_tracking '{"order_id": 11904}'`,
     otherwise reply, `... answer <id> --say "..."`. State only what tool results say. Short and plain: no
     lists, no closing offers, no promised times;
   - as **CUSTOMER**: `... answer <id> --say "..."`, in the persona's style, revealing only what the brief says
     the customer knows, and ending with the marker the instructions give when the goal is met or given up.
3. If `next` says "nothing waiting", wait a few seconds: the generator is running a tool or starting the next
   conversation.

Never edit files in `data/synthetic/raw/` by hand, and never answer a request with facts that no tool result in
it shows.

## After the run

```bash
uv run --group data python -m synth.verify data/synthetic/raw/agent-r1.jsonl --report   # code checks
```

The tone and fact-check judges run later on the teacher's GPU server (`synth/judge.py`); a conversation enters
the training data only after passing them, as every other run does.
