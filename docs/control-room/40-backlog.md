---
id: backlog
title: Dependency Backlog
order: 40
kind: planning
status: CURRENT
owner: chief-orchestrator
updated: 2026-09-03
source: https://github.com/bstBizEra/biztrust_guide/issues
summary: An ordered queue that separates ready work from blocked and intentionally deferred work.
snapshot_at: 2026-09-03T19:00:00+07:00
refresh_by: 2026-09-04T00:00:00+07:00
---

## Portfolio queue

| Priority | Work | State | Owner | Dependency / blocker |
|---:|---|---|---|---|
| 1 | `NS-001` Enable GitHub Pages | `WAIT_FOR_AUTHORITY` | Repository administrator | Admin access and public-content approval |
| 2 | `NS-029` Review open PRs | `READY` | Human reviewers | CI success on each final head SHA |
| 3 | `WP-018` Delivery Control Room | `IN_REVIEW` | Documentation engineering | PR #28 base and independent review |
| 4 | `NS-024 / S01` Authority profile | `WAIT_FOR_AUTHORITY` | Business + domain + legal + finance + architecture | Operative agreements and qualified reviewers |
| 5 | `S02` Glossary and authority taxonomy | `QUEUED` | Domain + architecture | S01 accepted |
| 6 | `S03–S11` Remaining architecture | `QUEUED` | Architecture authority | Each predecessor accepted in order |
| 7 | `WP-P0-001` Tenant isolation proof | `QUEUED` | Platform + security | `BT-G0` accepted and implementation authority granted |

## Intake rule

A backlog row may move to `READY` only when its outcome, owner, dependencies,
acceptance criteria, authority and evidence requirements are explicit. Priority
does not override a blocker.

## Ageing and escalation

- A blocked item must name a human owner and resolution condition.
- A time-sensitive dependency must carry an explicit date, not “soon”.
- A queued architecture slice is not opened merely to show activity.
- A stale snapshot is an observation gap; it must not be treated as zero backlog.
