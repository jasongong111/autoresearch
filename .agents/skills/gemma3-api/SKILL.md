---
name: gemma3-api
description: Calls the hosted Gemma 3 270M OpenAI-compatible HTTPS API at api-lm-gemma3.tr-dev.work. Use when configuring Gemma 3, google/gemma-3-270m-it, curl chat completions, streaming, LangChain, the React app chat API, local vLLM dev stack, or troubleshooting the gemma3 deployment.
---

# Gemma 3 270M Online API Access

This document explains how to call the hosted **Gemma 3 270M** service (`google/gemma-3-270m-it`) through its public HTTPS API. The API is OpenAI-compatible for chat. Tool calling and image upload are disabled for this model size.

**Authentication:** Set `GEMMA3_API_KEY` in your environment before calling the API (same value as `OPENAI_API_KEY` on the server). Do not commit the key to git.

---

## 1. Service URLs

| Purpose | URL |
|---|---|
| Web frontend | `https://lm-gemma3.tr-dev.work` |
| API base | `https://api-lm-gemma3.tr-dev.work/v1` |
| Health check | `https://api-lm-gemma3.tr-dev.work/api/health` |
| Chat completions | `https://api-lm-gemma3.tr-dev.work/v1/chat/completions` |
| App chat (multipart) | `https://api-lm-gemma3.tr-dev.work/api/chat` |
| Swagger | `https://api-lm-gemma3.tr-dev.work/docs` |

Use the API base URL, not the frontend URL, when configuring SDKs, agents, or OpenAI-compatible clients.

**Local dev** (after `./launch_all.sh -m dev` in the Gemma 3 repo):

| Service | URL |
|---|---|
| vLLM (internal) | `http://127.0.0.1:8000` |
| API | `http://127.0.0.1:12053` |
| Frontend | `http://127.0.0.1:12052` |

Nginx snippets: `conf/dev/api-lm-gemma3-dev.conf`, `conf/dev/lm-gemma3-dev.conf`.

---

## 2. API Basics

| Property | Value |
|---|---|
| Protocol | OpenAI-compatible Chat Completions |
| Base URL | `https://api-lm-gemma3.tr-dev.work/v1` |
| Auth header | `Authorization: Bearer ${GEMMA3_API_KEY}` |
| Model ID | `google/gemma-3-270m-it` |
| Context window | `8192` tokens |
| Tool calling | Not enabled (`GEMMA3_ENABLE_AUTO_TOOL_CHOICE=0`) |
| Multimodal | Not supported (text only) |
| Streaming | Supported through SSE with `stream: true` on `/v1/chat/completions` |
| Recommended output limit | `16` to `512` tokens per request |

Obtain the API key from your team's secret store and export it locally. The server `.env` uses `OPENAI_API_KEY` with the same value.

---

## 3. Quick Start

Set the API key once in your shell:

```bash
export GEMMA3_API_KEY="your-key-here"
```

Check service health:

```bash
curl -sS https://api-lm-gemma3.tr-dev.work/api/health
```

Send a basic chat request:

```bash
curl -sS https://api-lm-gemma3.tr-dev.work/v1/chat/completions \
  -H "Authorization: Bearer ${GEMMA3_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-3-270m-it",
    "messages": [
      {"role": "user", "content": "Reply with exactly: PONG"}
    ],
    "max_tokens": 16
  }'
```

Expected result: `choices[0].message.content` contains `PONG`.

App chat (form API used by the React UI):

```bash
curl -sS -X POST https://api-lm-gemma3.tr-dev.work/api/chat \
  -F "session_id=demo-1" \
  -F "agent_id=agent1" \
  -F "message=Hello"
```

Smoke script (from the Gemma 3 repo root):

```bash
./venv/bin/python test/openai_gateway_smoke.py \
  --base-url https://api-lm-gemma3.tr-dev.work/v1
```

---

## 4. Request Examples

### 4.1 Chat Completions

```bash
curl -sS https://api-lm-gemma3.tr-dev.work/v1/chat/completions \
  -H "Authorization: Bearer ${GEMMA3_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-3-270m-it",
    "messages": [
      {"role": "system", "content": "You are a concise assistant."},
      {"role": "user", "content": "Explain what an API gateway does in one paragraph."}
    ],
    "temperature": 0.2,
    "max_tokens": 256
  }'
```

### 4.2 Streaming

```bash
curl -N https://api-lm-gemma3.tr-dev.work/v1/chat/completions \
  -H "Authorization: Bearer ${GEMMA3_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-3-270m-it",
    "messages": [
      {"role": "user", "content": "Count from 1 to 5."}
    ],
    "stream": true,
    "max_tokens": 64
  }'
```

Streaming responses are sent as Server-Sent Events and end with `data: [DONE]`.

**Tool calling is not supported** on this deployment. Do not send `tools` or `tool_choice`; use Gemma 4 (`gemma4-api` skill) for tool use.

---

## 5. SDK Examples

### 5.1 Python

Install the OpenAI SDK:

```bash
pip install openai
```

Call the API:

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api-lm-gemma3.tr-dev.work/v1",
    api_key=os.environ["GEMMA3_API_KEY"],
)

response = client.chat.completions.create(
    model="google/gemma-3-270m-it",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=64,
)

print(response.choices[0].message.content)
```

### 5.2 Node.js

Install the OpenAI SDK:

```bash
npm install openai
```

Call the API:

```js
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://api-lm-gemma3.tr-dev.work/v1",
  apiKey: process.env.GEMMA3_API_KEY,
});

const response = await client.chat.completions.create({
  model: "google/gemma-3-270m-it",
  messages: [{ role: "user", content: "Hello" }],
  max_tokens: 64,
});

console.log(response.choices[0].message.content);
```

### 5.3 LangChain Python

```python
import os
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="https://api-lm-gemma3.tr-dev.work/v1",
    api_key=os.environ["GEMMA3_API_KEY"],
    model="google/gemma-3-270m-it",
    max_tokens=512,
)

print(llm.invoke("Hello").content)
```

---

## 6. OpenClaw Configuration

Edit or create `~/.openclaw/openclaw.json` on the host that runs OpenClaw.

Use only the API base URL in `baseUrl`. Do not append `/chat/completions`; OpenClaw builds the full path itself.

Set `apiKey` from your local secret (for example, copy the value of `GEMMA3_API_KEY`). Do not commit this file with a real key.

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "trend-gemma3-vllm": {
        "baseUrl": "https://api-lm-gemma3.tr-dev.work/v1",
        "apiKey": "your-key-here",
        "api": "openai-completions",
        "models": [{
          "id": "google/gemma-3-270m-it",
          "name": "Gemma 3 270M",
          "reasoning": false,
          "input": ["text"],
          "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 },
          "contextWindow": 8192,
          "maxTokens": 512
        }]
      }
    }
  }
}
```

Important fields:

- `mode: "merge"` preserves existing OpenClaw providers.
- `baseUrl` must be `https://api-lm-gemma3.tr-dev.work/v1`.
- `api` must be `openai-completions`.
- `models[].id` must exactly match the served model ID.
- `reasoning` should stay `false`.
- Do not enable tool calling for this model.

Apply and verify:

```bash
openclaw gateway config.apply --file ~/.openclaw/openclaw.json
openclaw models list
```

---

## 7. Limits and Behavior

| Limit | Value | Notes |
|---|---|---|
| Max prompt plus output tokens | `8192` | Requests above this return a context length error |
| Recommended `max_tokens` | `16`–`512` | Small model; keep outputs short for low latency |
| Tool calling | Disabled | Use Gemma 4 stack for agents that need tools |
| Multimodal | Disabled | Text-only messages |
| Streaming timeout | Supported on `/v1/chat/completions` | Client-side timeouts may need adjustment |

Keep prompt size plus `max_tokens` below the context window.

---

## 8. Running the Stack (operators)

From the Gemma 3 deployment repository:

```bash
./setup_venv.sh          # once: Python venv + vLLM 0.18 (CUDA 12.x)
./launch_all.sh -m dev   # vLLM :8000, API :12053, UI :12052
```

Logs: `logs/dev/vllm.log`, `logs/dev/api-stderr.log`, `logs/dev/frontend-stderr.log`, `logs/dev/lifecycle.log`.

**Requirements:** NVIDIA GPU with CUDA 12.x, Node.js 18+ for Vite, `HF_TOKEN` in `.env` for Hugging Face download.

**Notable env vars** (`GEMMA3_*` in `.env`):

| Variable | Default | Notes |
|---|---|---|
| `GEMMA3_MODEL_ID` | `google/gemma-3-270m-it` | Served model |
| `GEMMA3_MAX_MODEL_LEN` | `8192` | vLLM context |
| `GEMMA3_GPU_MEMORY_UTILIZATION` | `0.35` | Fraction of GPU memory |
| `GEMMA3_ENFORCE_EAGER` | `1` | Avoids torch.compile issues |
| `VITE_API_BASE` | `https://api-lm-gemma3.tr-dev.work` | Frontend → API URL |
| `WEB_API_PORT` / `FRONTEND_PORT` | `12053` / `12052` | Dev ports |

---

## 9. Migration from Gemma 4

This deployment replaces Gemma 4 26B in the same repo pattern:

- Scripts: `run_gemma3.sh`, `run_gemma3.py` (replaced `run_gemma4.*`).
- Env prefix: `GEMMA3_*` (was `GEMMA4_*`).
- Public hostnames: **`lm-gemma3`** / **`api-lm-gemma3`** (Gemma 4 remains on `lm.tr-dev.work` / `api-lm.tr-dev.work`).
- vLLM pinned to **0.18.0** (CUDA 12.x).

For Gemma 4 API access, use the `gemma4-api` skill. Legacy docs: `docs/access_gemma4.md`, `docs/lan-access-openclaw.md`.

---

## 10. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `HTTP 401` | Missing or incorrect API key | Set `GEMMA3_API_KEY` and send `Authorization: Bearer ${GEMMA3_API_KEY}` |
| `HTTP 404` | Wrong URL path | Use `https://api-lm-gemma3.tr-dev.work/v1/chat/completions` |
| `HTTP 400 maximum context length` | Prompt plus output exceeds 8192 | Shorten the prompt or lower `max_tokens` |
| Empty or bad tool calls | Tool calling disabled on this model | Use Gemma 4 API or remove `tools` from the request |
| UI calls wrong API | `VITE_API_BASE` mismatch | Set `VITE_API_BASE` in `.env` and restart `./launch_all.sh` |
| Vite: host not allowed | Hostname not in `allowedHosts` | Add hostname under `frontend/vite.config.js` `server.allowedHosts` (`.tr-dev.work` covers `*.tr-dev.work`) |
| `502` from nginx | API not listening locally | Run `./launch_all.sh -m dev`; check `curl http://127.0.0.1:12053/api/health` |
| vLLM flashinfer errors | cubin version mismatch | `pip install 'flashinfer-cubin==0.6.6'` in venv |
| vLLM torch.compile / FakeTensorMode | compile enabled | Keep `GEMMA3_ENFORCE_EAGER=1` (default) |
| Browser opens UI but API fails | Client uses frontend URL as API base | Use `https://api-lm-gemma3.tr-dev.work/v1` for API clients |

For a fast API check:

```bash
curl -sS -o /dev/null -w "HTTP %{http_code}\n" \
  https://api-lm-gemma3.tr-dev.work/api/health
```

See also `docs/PORT-ALLOCATION.md` in the Gemma 3 repo.

---

## 11. Security Notes

- Treat the API key as a shared internal secret and do not copy it outside the approved environment.
- Prefer loading the key from `GEMMA3_API_KEY` (or `OPENAI_API_KEY` on the server) in scripts and local tools.
- Use HTTPS only for external access.
- The public frontend is `https://lm-gemma3.tr-dev.work`; programmatic clients should call `https://api-lm-gemma3.tr-dev.work/v1`.
- Rotate keys when a key is shared too broadly or exposed outside the intended client environment.
