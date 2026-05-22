---
name: gemma4-math
description: Use Gemma 4 with the calculator tool for exact arithmetic via api-lm.tr-dev.work.
---

# Gemma 4 Math — Calculator Tool Workflow

Use the hosted Gemma 4 API with the **`calculator` tool** for every arithmetic step. Set `GEMMA4_API_KEY` in your environment.

## API settings (math)

| Setting | Value |
|---|---|
| Base URL | `https://api-lm.tr-dev.work/v1` |
| Model | `RedHatAI/gemma-4-26B-A4B-it-FP8-Dynamic` |
| `temperature` | `0` |
| `max_tokens` | `512` (tool calls need headroom) |
| `tool_choice` | `"auto"` |

## Calculator tool schema

Register this tool on every math request:

```json
{
  "type": "function",
  "function": {
    "name": "calculator",
    "description": "Perform exact arithmetic. ops: add, subtract, multiply, divide, power, percent_of (percent_of computes a percent of b, e.g. a=20 b=150 -> 30).",
    "parameters": {
      "type": "object",
      "properties": {
        "op": {
          "type": "string",
          "enum": ["add", "subtract", "multiply", "divide", "power", "percent_of"]
        },
        "a": {"type": "number"},
        "b": {"type": "number"}
      },
      "required": ["op", "a", "b"]
    }
  }
}
```

### Operations

| `op` | Meaning | Example args | Result |
|---|---|---|---|
| `add` | a + b | `{"op":"add","a":125,"b":89}` | 214 |
| `subtract` | a − b | `{"op":"subtract","a":1000,"b":378}` | 622 |
| `multiply` | a × b | `{"op":"multiply","a":17,"b":43}` | 731 |
| `divide` | a ÷ b | `{"op":"divide","a":144,"b":12}` | 12 |
| `power` | a^b | `{"op":"power","a":2,"b":10}` | 1024 |
| `percent_of` | a% of b | `{"op":"percent_of","a":20,"b":150}` | 30 |

## Two-turn workflow (required)

1. **Turn 1 — tool call:** Read the user problem. Call `calculator` with the **first** arithmetic step (or the only step for simple problems). Do not guess; use the tool.
2. **Turn 2 — final answer:** Read the tool result from the `tool` message. If one more step remains, apply it mentally from the tool result, **or** combine operands into a single follow-up calculation you can state directly. Reply with **only the final integer** — no words, no units, no explanation.

**Critical rules:**
- After tool results arrive, your **final message content must be only the integer** (e.g. `214`, not `The answer is 214`).
- For **multi-step** problems (order of operations, chained ops): use the calculator for the **hardest** step (usually multiply/divide), then finish the remaining step from the tool result in your head before replying.
- Never emit a second `tool_calls` block on the final turn — finish with plain numeric content.

## Worked examples

### Simple addition

User: `Compute 125 + 89.`

Turn 1 tool call: `{"op":"add","a":125,"b":89}` → tool returns `214`

Turn 2 reply: `214`

### Word problem (addition)

User: `Alice has 15 apples and buys 8 more. How many apples?`

Turn 1: `{"op":"add","a":15,"b":8}` → `23`

Turn 2: `23`

### Percent

User: `What is 20 percent of 150?`

Turn 1: `{"op":"percent_of","a":20,"b":150}` → `30`

Turn 2: `30`

### Order of operations — `(48 + 12) × 3`

User asks to add then multiply.

Turn 1: `{"op":"add","a":48,"b":12}` → tool returns `60`

Turn 2: compute 60 × 3 = 180 mentally, reply: `180`

### Order of operations — `100 − 25×2`

Do multiplication first.

Turn 1: `{"op":"multiply","a":25,"b":2}` → tool returns `50`

Turn 2: compute 100 − 50 = 50 mentally, reply: `50`

### Fraction of a number — three fourths of 80

Turn 1: `{"op":"multiply","a":0.75,"b":80}` → `60`

Turn 2: `60`

## Request template

```bash
curl -sS https://api-lm.tr-dev.work/v1/chat/completions \
  -H "Authorization: Bearer ${GEMMA4_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "RedHatAI/gemma-4-26B-A4B-it-FP8-Dynamic",
    "messages": [{"role": "user", "content": "Compute 17 multiplied by 43."}],
    "tools": [<calculator schema above>],
    "tool_choice": "auto",
    "temperature": 0,
    "max_tokens": 512
  }'
```

Do not commit API keys to git.
