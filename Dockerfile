# Nova's backend (api/app.py): the agent loop, tools, guardrails and the confirm route, on a small CPU host.
# Configured only by environment variables at deploy time (see api/app.py); no secrets in the image.
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir uv==0.12.17
COPY pyproject.toml uv.lock ./
# The locked dependencies for the api and rag groups, with torch's CPU build in place of the CUDA one
# (the backend only embeds short queries; the GPU is the model server's).
RUN uv export --group api --group rag --no-dev --frozen --no-hashes --no-emit-project \
      | grep -v -E "^(torch|triton|nvidia-)" > /tmp/requirements.txt \
 && uv pip install --system --no-cache torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu \
 && uv pip install --system --no-cache -r /tmp/requirements.txt
# Bake in the embedding model and the tokenizer that counts prompt tokens, so a cold start downloads nothing.
ENV HF_HOME=/app/hf
RUN python -c "from huggingface_hub import snapshot_download as d; \
d('BAAI/bge-small-en-v1.5'); \
d('Qwen/Qwen3.5-2B', allow_patterns=['tokenizer*', 'vocab.json', 'merges.txt', 'chat_template.jinja', 'config.json'])"
ENV HF_HUB_OFFLINE=1 NOW_MODE=real PORT=8080
COPY config.py ./
COPY agent agent
COPY api api
COPY db db
COPY rag rag
COPY kb kb
CMD ["sh", "-c", "uvicorn api.app:app --host 0.0.0.0 --port $PORT"]
