---
id: evidence
title: Evidence and Assurance
order: 70
kind: assurance
status: VALIDATING
owner: independent-verifier
updated: 2026-09-03
source: https://github.com/bstBizEra/biztrust_guide/pull/28
summary: Reproducible checks, revision binding and declared non-coverage for the current control surface.
---

## Evidence register

| Evidence | Revision / subject | Result | Durable record |
|---|---|---|---|
| Architecture pack CI | PR #28 head `d8a83ef` | `SUCCESS` | Actions run `33753511805` and PR conversation |
| Complete repository suite | Current WP-018 worktree | `43 PASS` | 27 baseline + 16 control-room tests; final CI required |
| Control-room generation | 10 Markdown sources + fixed template | `PASS` | `python3 scripts/build_control_room.py --check` |
| HTML safety contract | Raw HTML, unsafe links, malformed tables | `PASS` | Negative-first unit tests reject each mutation |
| Source/display drift | Hand-edited or stale generated page | `PASS` | Negative control exits non-zero with `CONTROL_ROOM_BUILD=FAIL` |
| Static-site continuity | 11 HTML pages, 235 IDs, 332 references | `PASS` | `python3 scripts/validate_continuity.py` |
| Local HTTP path | `/stages/control-room.html` on port 8080 | `200 OK` | Python 3.12 `http.server` smoke test |
| Publication | Final WP-018 head | `PENDING` | At least one GitHub Actions run required |

## Required final checks

```text
python3 scripts/build_control_room.py --check
python3 -m unittest discover -s tests -v
python3 scripts/validate_continuity.py
node --check script.js
sed -n '/^  <script>$/,/^  <\\/script>$/p' stages/control-room.html | sed '1d;$d' | node --check -
git diff --check
```

## Evidence quality rule

“Passed” is not sufficient. Record the exact source revision, command or
workflow identity, environment, terminal outcome, verifier, coverage and known
non-coverage.

## Declared non-coverage

- No architecture or ADR is accepted by control-room validation.
- No Lao PDR legal, regulatory or accounting conclusion is proved.
- No production BizTrust application, database or tenant isolation control exists here.
- No live GitHub synchronization or mutable workflow is tested.
- Browser rendering remains a presentation check, not proof that source facts are current.
