---
name: agent-core
register: product
---

# Agent Core Frontend

## Product

A single-page chat UI for interacting with the Gemma 4 skill agent. Users send prompts, watch the agent think and call tools in real time, inspect discovered skills, and switch between research tasks.

## Users

ML engineers and researchers running autonomous agent experiments. They spend focused sessions inside the interface: sending prompts, reading trace logs, verifying skill behavior. The UI must stay out of the way during long runs.

## Tone

Calm, technical, dense. No marketing copy. Every pixel serves observability.

## Anti-references

- ChatGPT-style conversational UI (too airy, no density)
- SaaS dashboard card grids (we have one surface, not a dashboard)
- Neon/cyberpunk dark themes (tired cliche for AI tools)

## Principles

- Dark mode only (extended monitoring sessions)
- Restrained color: one indigo accent for interactivity, everything else is cool slate
- Density: logs, skills, and chat share the same viewport without modal switching
- Motion conveys state only: typing indicator, streaming tokens, new log entries
