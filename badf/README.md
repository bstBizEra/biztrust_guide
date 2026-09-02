# BADF Continuity Surface

This directory is the machine-readable operational entry point for agents.

- `current-state.json` — exactly one authoritative active state
- `next-actions.json` — ordered, owned and bounded actions
- `decision-log.jsonl` — append-only decision records

### NS ids are point-in-time

`next-actions.json` allocates NS ids as a rolling counter and re-uses them across work packages. **An id is meaningful only against the revision of `next-actions.json` that issued it.** A checkpoint recording `next_action_id: "NS-011"` was correct when written; that id now names different work, and older ids such as NS-015 and NS-016 have been retired entirely. To resolve one, read the revision of this file's sibling that was current at the checkpoint's `created_at` — `git log -p badf/next-actions.json`.

`docs/NEXT_STEPS.md` uses the same `NS-nnn` form for a frozen 2026-09-02 roadmap. **The two namespaces are unrelated above NS-003.** The validator cannot detect a mismatch: `checkpoint:linked` resolves only the *latest* checkpoint's id against current state, so every older checkpoint's id is unchecked.

Agents must validate these files before mutating repository content. Chat context may help interpretation but cannot override repository state or grant authority.

