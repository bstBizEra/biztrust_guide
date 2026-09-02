# BADF Continuity Surface

This directory is the machine-readable operational entry point for agents.

- `current-state.json` — exactly one authoritative active state
- `next-actions.json` — ordered, owned and bounded actions
- `decision-log.jsonl` — append-only decision records

Agents must validate these files before mutating repository content. Chat context may help interpretation but cannot override repository state or grant authority.

