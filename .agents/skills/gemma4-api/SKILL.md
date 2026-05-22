---
name: gemma4-api
description: Calls the hosted Gemma 4 OpenAI-compatible HTTPS API at api-lm.tr-dev.work. Use when configuring Gemma 4, trend-gemma-vllm, OpenClaw, curl chat completions, streaming, tool calling, LangChain, or troubleshooting RedHatAI/gemma-4-26B-A4B-it-FP8-Dynamic.
---

# Gemma 4 Online API Access

This document explains how to call the hosted Gemma 4 service through its public HTTPS API. The API is OpenAI-compatible, so most tools that support a custom OpenAI base URL can use it directly.

**Authentication:** Set `GEMMA4_API_KEY` in your environment before calling the API. Do not commit the key to git.

---

## 1. Service URLs

| Purpose | URL |
|---|---|
| Web frontend | `https://lm.tr-dev.work` |
| API base | `https://api-lm.tr-dev.work/v1` |
| Health check | `https://api-lm.tr-dev.work/api/health` |
| Chat completions | `https://api-lm.tr-dev.work/v1/chat/completions` |
| Models | `https://api-lm.tr-dev.work/v1/models` |

Use the API base URL, not the frontend URL, when configuring SDKs, agents, or OpenAI-compatible clients.

---

## 2. API Basics

| Property | Value |
|---|---|
| Protocol | OpenAI-compatible Chat Completions |
| Base URL | `https://api-lm.tr-dev.work/v1` |
| Auth header | `Authorization: Bearer ${GEMMA4_API_KEY}` |
| Model ID | `RedHatAI/gemma-4-26B-A4B-it-FP8-Dynamic` |
| Context window | `65536` tokens |
| Tool calling | Supported with `tool_choice: "auto"` and `"required"` |
| Streaming | Supported through SSE with `stream: true` |
| Recommended output limit | `512` to `4096` tokens per request |

Obtain the API key from your team's secret store and export it locally.

---

## 3. Quick Start

Set the API key once in your shell:

```bash
export GEMMA4_API_KEY="your-key-here"
```

Check service health:

```bash
curl -sS https://api-lm.tr-dev.work/api/health
```

Expected response:

```json
{"ok": true}
```

List available models:

```bash
curl -sS https://api-lm.tr-dev.work/v1/models \
  -H "Authorization: Bearer ${GEMMA4_API_KEY}"
```

Send a basic chat request:

```bash
curl -sS https://api-lm.tr-dev.work/v1/chat/completions \
  -H "Authorization: Bearer ${GEMMA4_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "RedHatAI/gemma-4-26B-A4B-it-FP8-Dynamic",
    "messages": [
      {"role": "user", "content": "Reply with exactly: PONG"}
    ],
    "max_tokens": 8
  }'
```

Expected result: `choices[0].message.content` contains `PONG`.

---

## 4. Request Examples

### 4.1 Chat Completions

```bash
curl -sS https://api-lm.tr-dev.work/v1/chat/completions \
  -H "Authorization: Bearer ${GEMMA4_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "RedHatAI/gemma-4-26B-A4B-it-FP8-Dynamic",
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
curl -N https://api-lm.tr-dev.work/v1/chat/completions \
  -H "Authorization: Bearer ${GEMMA4_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "RedHatAI/gemma-4-26B-A4B-it-FP8-Dynamic",
    "messages": [
      {"role": "user", "content": "Count from 1 to 5."}
    ],
    "stream": true,
    "max_tokens": 64
  }'
```

Streaming responses are sent as Server-Sent Events and end with `data: [DONE]`.

### 4.3 Tool Calling

```bash
curl -sS https://api-lm.tr-dev.work/v1/chat/completions \
  -H "Authorization: Bearer ${GEMMA4_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "RedHatAI/gemma-4-26B-A4B-it-FP8-Dynamic",
    "messages": [
      {"role": "user", "content": "What is 17 multiplied by 43? Use the calculator tool."}
    ],
    "tools": [{
      "type": "function",
      "function": {
        "name": "calculator",
        "description": "Multiply two numbers",
        "parameters": {
          "type": "object",
          "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"}
          },
          "required": ["a", "b"]
        }
      }
    }],
    "tool_choice": "auto",
    "max_tokens": 512
  }'
```

Expected result: `finish_reason` is `tool_calls` and the response contains a `tool_calls` array.

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
    base_url="https://api-lm.tr-dev.work/v1",
    api_key=os.environ["GEMMA4_API_KEY"],
)

response = client.chat.completions.create(
    model="RedHatAI/gemma-4-26B-A4B-it-FP8-Dynamic",
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
  baseURL: "https://api-lm.tr-dev.work/v1",
  apiKey: process.env.GEMMA4_API_KEY,
});

const response = await client.chat.completions.create({
  model: "RedHatAI/gemma-4-26B-A4B-it-FP8-Dynamic",
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
    base_url="https://api-lm.tr-dev.work/v1",
    api_key=os.environ["GEMMA4_API_KEY"],
    model="RedHatAI/gemma-4-26B-A4B-it-FP8-Dynamic",
    max_tokens=512,
)

print(llm.invoke("Hello").content)
```

---

## 6. OpenClaw Configuration

Edit or create `~/.openclaw/openclaw.json` on the host that runs OpenClaw.

Use only the API base URL in `baseUrl`. Do not append `/chat/completions`; OpenClaw builds the full path itself.

Set `apiKey` from your local secret (for example, copy the value of `GEMMA4_API_KEY`). Do not commit this file with a real key.

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "trend-gemma-vllm": {
        "baseUrl": "https://api-lm.tr-dev.work/v1",
        "apiKey": "your-key-here",
        "api": "openai-completions",
        "models": [{
          "id": "RedHatAI/gemma-4-26B-A4B-it-FP8-Dynamic",
          "name": "Gemma 4 26B",
          "reasoning": false,
          "input": ["text"],
          "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 },
          "contextWindow": 65536,
          "maxTokens": 4096
        }]
      }
    }
  }
}
```

Important fields:

- `mode: "merge"` preserves existing OpenClaw providers.
- `baseUrl` must be `https://api-lm.tr-dev.work/v1`.
- `api` must be `openai-completions`.
- `models[].id` must exactly match the model returned by `/v1/models`.
- `reasoning` should stay `false`; this model is not exposed as a reasoning model.

Apply and verify:

```bash
openclaw gateway config.apply --file ~/.openclaw/openclaw.json
openclaw models list
```

The model list should include:

```text
trend-gemma-vllm/RedHatAI/gemma-4-26B-A4B-it-FP8-Dynamic
```

---

## 7. Limits and Behavior

| Limit | Value | Notes |
|---|---|---|
| Max prompt plus output tokens | `65536` | Requests above this return a context length error |
| Recommended `max_tokens` | `512` for chat, up to `4096` for longer generations | Higher values increase latency |
| Tool call output budget | At least `512` tokens | Lower limits can truncate tool calls |
| Streaming timeout | Long-running generations are supported | Client-side timeouts may need adjustment |

Keep prompt size plus `max_tokens` below the context window. For large prompts, reduce `max_tokens` or split the task into smaller requests.

---

## 8. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `HTTP 401` | Missing or incorrect API key | Set `GEMMA4_API_KEY` and send `Authorization: Bearer ${GEMMA4_API_KEY}` |
| `HTTP 404` | Wrong URL path | Use `https://api-lm.tr-dev.work/v1/chat/completions` |
| `HTTP 400 maximum context length` | Prompt plus output is too large | Shorten the prompt or lower `max_tokens` |
| `finish_reason == "length"` | Output limit was too low | Increase `max_tokens` |
| Empty `tool_calls` | Tool schema or tool choice is invalid | Validate the `tools` object and use `tool_choice: "auto"` |
| OpenClaw model does not appear | Config was not applied or model ID is wrong | Re-apply config and copy the model ID from `/v1/models` |
| Browser can open frontend but API calls fail | Client is using `lm.tr-dev.work` as the API base | Use `https://api-lm.tr-dev.work/v1` for API clients |

For a fast API check, run:

```bash
curl -sS -o /dev/null -w "HTTP %{http_code}\n" \
  https://api-lm.tr-dev.work/v1/models \
  -H "Authorization: Bearer ${GEMMA4_API_KEY}"
```

Expected result: `HTTP 200`.

---

## 9. Security Notes

- Treat the API key as a shared internal secret and do not copy it outside the approved environment.
- Prefer loading the key from `GEMMA4_API_KEY` in scripts and local tools.
- Use HTTPS only for external access.
- The public frontend is `https://lm.tr-dev.work`; programmatic clients should call `https://api-lm.tr-dev.work/v1`.
- Rotate keys when a key is shared too broadly or exposed outside the intended client environment.
