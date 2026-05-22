# Multi-step math — one tool call, then integer reply

The API runs **exactly one** calculator round. After you receive a tool result, you **must not** call `calculator` again.

## Required pattern

1. **First assistant message:** one `calculator` tool call for the primary operation (usually multiply, divide, power, percent_of, or the first add/subtract).
2. **Second assistant message:** plain text containing **only the final integer**. No tool calls. No `<|channel>`, no reasoning tags, no words.

## Multi-step examples

### `(48 + 12) × 3` → `180`

- Tool call: `{"op":"multiply","a":60,"b":3}` (compute 48+12=60 mentally, then multiply in one call)
- Final reply: `180`

### `100 − 25×2` → `50`

- Tool call: `{"op":"multiply","a":25,"b":2}` → result 50
- Final reply: `50` (compute 100−50 mentally)

## Rules

- **Never** emit `tool_calls` on your second message.
- **Never** output thought/reasoning channels — only digits in the final message.
- If a tool result gives you the final answer directly, reply with that number.
