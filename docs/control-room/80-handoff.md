---
id: handoff
title: Handoff and Recovery
order: 80
kind: continuity
status: READY
owner: receiving-agent
updated: 2026-09-03
source: https://github.com/bstBizEra/biztrust_guide/issues/32
summary: The exact recovery path a new agent follows without access to earlier conversation history.
---

## Read in this order

1. Repository `AGENTS.md`.
2. Continuity correction [PR #30](https://github.com/bstBizEra/biztrust_guide/pull/30); until composed or merged, it explains why baseline `NS-026` is stale and `NS-001` is current.
3. `badf/current-state.json` and `badf/next-actions.json` at the checked-out revision, reconciled against PR #30.
4. Work Package [Issue #32](https://github.com/bstBizEra/biztrust_guide/issues/32).
5. Base architecture [PR #28](https://github.com/bstBizEra/biztrust_guide/pull/28) and its final head.
6. `docs/control-room/README.md` and these Markdown sources.
7. The latest checkpoint for the active Work Package.
8. Current branch, HEAD, worktree, remote divergence and overlapping PR files.

## First safe commands

```text
git status --short --branch
python3 -m unittest discover -s tests -v
python3 scripts/validate_continuity.py
python3 scripts/build_control_room.py --check
```

## Resume decision

Return exactly one of `CONTINUE`, `BLOCKED`, `WAIT_FOR_AUTHORITY`,
`RECOVERY_REQUIRED` or `COMPLETE` before editing.

## Stop conditions

- More than one source declares `primary: true`.
- Generated HTML differs from the Markdown build.
- The active issue, branch or authority cannot be identified.
- Another PR owns a file this slice must modify and no coordination record exists.
- A source link or evidence points to a different revision than the reviewed result.
- The baseline still emits `NS-026` and PR #30 is missing, closed without replacement or materially changed.
- A confidential document would need to enter the public repository.

> Chat history may explain intent, but it is never the recovery source of truth.
