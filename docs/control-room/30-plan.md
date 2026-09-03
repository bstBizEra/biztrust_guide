---
id: plan
title: Plan and Milestones
order: 30
kind: planning
status: CURRENT
owner: chief-orchestrator
updated: 2026-09-03
source: https://github.com/bstBizEra/biztrust_guide/issues/27
summary: Now, next and later outcomes connected by explicit evidence and authority gates.
---

## Now — make the control plane trustworthy

1. Review and merge independent guide corrections without overwriting their owners.
2. Enable GitHub Pages and prove the public delivery path.
3. Land PR #28 and this stacked control-room slice only after final-SHA review.
4. Keep one global primary action and one active architecture slice.

**Exit:** published guide, current continuity ledger, green final-SHA CI and no
unresolved shared-file collision.

## Next — complete the architecture contract one slice at a time

| Order | Slice | Outcome | Entry gate |
|---:|---|---|---|
| 01 | `S01` | Tenant authority, jurisdiction and client-money inputs | Five review seats and secure evidence access |
| 02–03 | `S02–S03` | Canonical language, authority and systems of record | S01 accepted |
| 04–06 | `S04–S06` | Coverage/time, placement topology and financial model | Prior slices accepted |
| 07–10 | `S07–S10` | Tenant security, data, interfaces and operations | Domain foundation accepted |
| 11 | `S11` | Conformance review and `BT-G0` decision | S01–S10 accepted |

**Exit:** architecture authority records `ACCEPT`, `CONDITIONAL_ACCEPT`,
`REVISE` or `REJECT`. Document length does not constitute acceptance.

## Later — authorize implementation by capability gate

- `P0 / BT-G1`: prove Logto → tenant context → PostgreSQL RLS → audit evidence.
- `P1 / BT-G2`: deliver the broker core from client and risk to authoritative cover evidence.
- `P2 / BT-G3`: add placement, servicing, claims and renewal depth.
- `P3 / BT-G4–BT-G6`: add money, ledger, commission, settlement, adapters and independent tenant provisioning.

No later phase may borrow authority from an approved earlier phase.

## Operating cadence

| Cadence | Review | Output |
|---|---|---|
| Start of session | State, issue, branch, authority, dependencies | Resume decision and one next action |
| Daily | Today, blockers, pull requests, snapshot freshness | Refreshed operational view |
| Per slice | Decision alternatives, evidence, dissent | Accepted or revised slice |
| Weekly | Backlog ageing, risks, evidence durability | Portfolio review and escalations |
| At gate | Independent conformance and authority | Recorded transition or stop |
