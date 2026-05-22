---
name: gemma4-math
description: Use Gemma 4 with the calculator tool for exact arithmetic via api-lm.tr-dev.work.
---

# Gemma 4 Math — Calculator Tool

Set `GEMMA4_API_KEY`. Use the hosted API with the `calculator` tool for arithmetic.

| Setting | Value |
|---|---|
| Base URL | `https://api-lm.tr-dev.work/v1` |
| Model | `RedHatAI/gemma-4-26B-A4B-it-FP8-Dynamic` |
| `temperature` | `0` |
| `max_tokens` | `512` |

## Calculator tool

```json
{
  "type": "function",
  "function": {
    "name": "calculator",
    "description": "Exact arithmetic: add, subtract, multiply, divide, power, percent_of (a% of b).",
    "parameters": {
      "type": "object",
      "properties": {
        "op": {"type": "string", "enum": ["add","subtract","multiply","divide","power","percent_of"]},
        "a": {"type": "number"},
        "b": {"type": "number"}
      },
      "required": ["op", "a", "b"]
    }
  }
}
```

## Two-turn workflow (strict)

The runtime executes **one** calculator round only.

1. **First message:** call `calculator` once with the needed operation.
2. **Second message:** reply with **only the final integer** — no tool calls, no words, no `<|channel>` tags.

**Never call `calculator` twice.** After the tool result, finish any remaining step mentally and output digits only.

### Multi-step problems

When the problem has two steps, use **one** tool call with the combined operands:

| Problem | Tool call | Final reply |
|---|---|---|
| `(48+12)×3` | `multiply(60, 3)` — add 48+12 mentally first | `180` |
| `100−25×2` | `multiply(25, 2)` → 50, then 100−50 mentally | `50` |

### Simple problems

| Problem | Tool call | Final reply |
|---|---|---|
| `125+89` | `add(125, 89)` | `214` |
| `20% of 150` | `percent_of(20, 150)` | `30` |
| `2^10` | `power(2, 10)` | `1024` |

Do not commit API keys to git.
