---
id: scorecard
title: Delivery Scorecard
order: 90
kind: assurance
status: CURRENT
owner: portfolio-owner
updated: 2026-09-03
source: https://github.com/bstBizEra/biztrust_guide/issues/32
summary: Decision-oriented indicators with definitions, owners and escalation triggers.
---

## Current indicators

| Indicator | Current | Target | Owner | Escalation trigger |
|---|---|---|---|---|
| Primary actions | `1` | Exactly `1` | Orchestrator | Zero or more than one |
| Active architecture slices | `1` | At most `1` | Architecture owner | Parallel unaccepted slices |
| Control-room Markdown views | `10` | `10` registered | Guide owner | Missing or duplicate ID/order |
| Repository tests | `43 PASS` | All pass on final SHA | Quality owner | Any failure or skipped protected check |
| GitHub Pages availability | `BLOCKED` | Published and verified | Repository administrator | NS-001 remains open |
| Architecture gate | `WAIT_FOR_AUTHORITY` | Evidence-backed `BT-G0` decision | Architecture authority | Design proceeds without S01 |
| Critical architecture inputs | `UNKNOWN` | Zero unowned critical unknowns | Business/legal/finance | Unknown encoded as default |

## KPI design rules

- Every metric has a business or control decision attached to it.
- A count without a target and escalation threshold is information, not a KPI.
- Green presentation never overrides failed evidence or missing authority.
- Snapshot metrics carry an observed date and visibly expire.

## Recommended next metrics

- Backlog age by owner and blocker class.
- Decision lead time from proposal to attributable acceptance.
- Evidence durability: percentage retained independently of expiring run URLs.
- Rework from late architecture decisions.
- Gate escape rate and severity.
- Tenant-isolation negative-test coverage after P0 begins.
