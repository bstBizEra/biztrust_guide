# BizTrust Delivery Control Room Sources

This directory is the authoritative content source for `stages/control-room.html`.
The HTML page is generated display output and must not be edited directly.

## Registered views

| Order | File | Operating question |
|---:|---|---|
| 10 | `10-session.md` | What state are we in, and how will the next design decision be run? |
| 20 | `20-today.md` | What is the one primary action today? |
| 30 | `30-plan.md` | What is now, next and later, and what gates the transitions? |
| 40 | `40-backlog.md` | Which work is ready, blocked or queued by dependency? |
| 50 | `50-decisions.md` | Which decisions exist, who may accept them and what remains proposed? |
| 60 | `60-risks.md` | What can invalidate the plan or evidence? |
| 70 | `70-evidence.md` | What has been proved, against which revision, and what is not covered? |
| 80 | `80-handoff.md` | Can a new agent recover without conversation history? |
| 90 | `90-scorecard.md` | Which control and delivery indicators require attention? |
| 100 | `100-research.md` | Which unanswered questions block responsible design? |

## Source contract

Every registered Markdown file starts with frontmatter containing:

```text
---
id: stable-section-id
title: Human-readable title
order: 10
kind: execution
status: CURRENT
owner: accountable-role
updated: 2026-09-03
source: https://github.com/...
---
```

Exactly one file must also declare `primary: true` and `primary_action`.
Optional `snapshot_at` and `refresh_by` values must be timezone-aware RFC 3339
timestamps. The browser visibly marks expired snapshots; it never upgrades or
changes repository state.

Allowed kinds are `execution`, `planning`, `governance`, `assurance`,
`continuity` and `research`. Allowed statuses are enforced by the generator.

## Update protocol

1. Verify the relevant GitHub Issue, branch, authority and dependencies.
2. Change the smallest owning Markdown file.
3. Run `python3 scripts/build_control_room.py`.
4. Review both the Markdown and generated HTML diffs.
5. Run `python3 scripts/build_control_room.py --check` and the full test suite.
6. Bind review and CI evidence to the final commit SHA.

Never copy confidential licences, agreements, bank details, personal data or
legal advice into this public control surface. Use approved evidence metadata
and secure references.
