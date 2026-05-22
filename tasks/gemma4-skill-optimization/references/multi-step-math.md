# Multi-step math — one tool call, then integer reply

The API runs **exactly one** calculator round. After you receive a tool result, you **must not** call `calculator` again.

## Worked example: `100 − 25×2`

User: *"Compute 100 minus the product of 25 and 2."*

1. Tool: `multiply(25, 2)` → `50`
2. Mental: 100 − 50 = 50
3. Final reply: `50` (never call `subtract` on turn 2)

Forbidden on turn 2: `tool_calls`, `<|channel>thought`, or any text besides the integer.
