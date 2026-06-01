# agent_core — Gemma 4 skill agent (OpenAI Agents SDK)
# Build from repo root:
#   docker build -f agent_core/Dockerfile -t agent-core .
# Run:
#   docker run --rm -p 8766:8766 -e GEMMA4_API_KEY=... agent-core
#
# For development with live skill reloading, mount skill roots as volumes:
#   docker run --rm -p 8766:8766 -e GEMMA4_API_KEY=... \
#     -v $(pwd)/.agents/skills:/app/.agents/skills:ro \
#     -v $(pwd)/.claude/skills:/app/.claude/skills:ro \
#     -v $(pwd)/tasks:/app/tasks:ro \
#     agent-core

FROM python:3.12-slim AS runtime
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY agent_core/requirements.txt ./agent_core/requirements.txt
RUN pip install --no-cache-dir -r agent_core/requirements.txt

COPY agent_core/ ./agent_core/
COPY .agents/skills ./.agents/skills
COPY .claude/skills ./.claude/skills

ENV PYTHONPATH=/app \
    GEMMA4_MODEL_ID="google/gemma-4-E2B-it" \
    GEMMA4_BASE_URL="https://api-lm.tr-dev.work/v1"

EXPOSE 8766

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8766/api/health', timeout=3)"

ENTRYPOINT ["python", "-m", "agent_core"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8766"]
