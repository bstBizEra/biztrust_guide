---
id: decisions
title: Decisions and Authority
order: 50
kind: governance
status: CURRENT
owner: architecture-authority
updated: 2026-09-03
source: https://github.com/bstBizEra/biztrust_guide/issues/32
summary: Proposed decisions, their decision rights and the evidence still required for acceptance.
---

## Control-room decisions

| ID | Decision | Status | Accepting authority | Evidence |
|---|---|---|---|---|
| `CR-D001` | Markdown files are the control-room content source of truth | `PROPOSED` | Guide owner | Drift test and review |
| `CR-D002` | Generate escaped static HTML at build time; no runtime Markdown library | `PROPOSED` | Guide owner + security | Generator tests and final-SHA CI |
| `CR-D003` | Exactly one section declares the primary action | `PROPOSED` | Orchestrator authority | Negative test for a second primary |
| `CR-D004` | Dated operational snapshots visibly expire | `PROPOSED` | Operations owner | Timezone validation and browser behavior |
| `CR-D005` | GitHub Issues remain the human ledger; the page is a governed projection | `PROPOSED` | Repository owner | Trace links and ownership review |
| `CR-D006` | Live GitHub synchronization is deferred | `PROPOSED` | Repository owner | Risk/complexity review |

## Decision-right rule

An implementing agent may recommend and produce evidence. It cannot change a
row to `ACCEPTED` unless the named authority records that decision against the
final source revision.

## Architecture decisions

ADR-001 through ADR-020 remain draft or blocked as recorded in the
[ADR register](https://github.com/bstBizEra/biztrust_guide/blob/main/docs/architecture/ADR_REGISTER.md).
This control room summarizes status; it does not replace or accept an ADR.
