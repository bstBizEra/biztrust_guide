---
id: session
title: Design Session
order: 10
kind: execution
status: IN_REVIEW
owner: documentation-engineer
updated: 2026-09-03
source: https://github.com/bstBizEra/biztrust_guide/issues/32
summary: The current delivery state plus a decision-led agenda for the next architecture design session.
work_package: BIZTRUST-GUIDE-WP-018
architecture_state: WAIT_FOR_AUTHORITY
active_slice: ARCH-001A-S01
evidence: 43 TESTS PASS · CI REQUIRED
snapshot_at: 2026-09-03T19:00:00+07:00
refresh_by: 2026-09-04T00:00:00+07:00
---

## Session contract

This session implements the Markdown-first Delivery Control Room under
[Issue #32](https://github.com/bstBizEra/biztrust_guide/issues/32). It is stacked
on the architecture documentation in
[PR #28](https://github.com/bstBizEra/biztrust_guide/pull/28); it must not be
merged before that base is accepted or the branch is safely retargeted.

| Field | Observed state | Consequence |
|---|---|---|
| Repository baseline | `b1a3fa455b758cc6e27404e9b84ee1dce3acf385` | Current public `main` before the stacked architecture pack |
| Architecture pack | PR #28 · `IN_REVIEW` | Architecture documentation exists but is not accepted |
| Continuity correction | PR #30 · `IN_REVIEW` | `NS-001` is the proposed current action; the branch baseline still emits stale `NS-026` |
| Architecture program | Issue #27 · `WAIT_FOR_AUTHORITY` | No architecture freeze or P0 implementation authority |
| Active architecture slice | Issue #15 · `ARCH-001A-S01` | Human authority, legal, domain and finance inputs required |
| Delivery slice | Issue #32 · `IN_REVIEW` | Control-room implementation awaits independent review and CI |
| Production authority | `NOT_GRANTED` | This repository remains documentation and governance only |

## Authority boundary

- The user authorized this documentation and HTML-display slice.
- The implementing agent may prepare, validate and publish a pull request.
- Architecture acceptance, legal conclusions, merge, production implementation and GitHub Pages administration remain human-reserved.
- Unknown or conflicting authority remains `WAIT_FOR_AUTHORITY`; the interface cannot convert silence into approval.

> Observation, decision, authority and evidence remain separate records.

## Next architecture design session — S01 authority profile

**Decision question:** for each initial tenant and product arrangement, can
UniTrust make cover effective, or can it only request an insurer decision?

| Seat | Required contribution | May accept |
|---|---|---|
| Accountable business owner | Actual entities, channels, products and intended responsibilities | Operating-model facts |
| Insurance domain lead | Placement, bind, policy, servicing and claims practice | Domain semantics |
| Lao-qualified legal/regulatory reviewer | Licence, delegated authority, disclosures, client-money and jurisdiction | Legal/regulatory conclusions |
| Finance/client-money owner | Collection, trust/segregation, remittance, commission and reconciliation | Accounting-operating facts |
| Architecture authority | Alternatives, invariants, consequences and unresolved assumptions | Architecture slice after other inputs exist |
| Recorder/red-team | Evidence links, dissent, contradictions, actions and stop conditions | Nothing on behalf of another seat |

### Ninety-minute agenda

1. `00–10` Confirm scope, participants, decision rights and evidence handling.
2. `10–25` Map legal entities, jurisdictions, tenants, channels and product arrangements.
3. `25–45` Walk quote → acceptance → bind request → insurer confirmation → cover evidence.
4. `45–60` Walk premium receipt → risk transfer → insurer payable → commission → reconciliation.
5. `60–75` Test exceptions: delegated authority, master policy, certificate, cancellation, refund and claim.
6. `75–85` Classify every conclusion as observed, proposed, accepted, disputed or unknown.
7. `85–90` Assign one next action per unresolved blocker and name the evidence required.

**Required outputs:** authority matrix v0.1, evidence index, unresolved-question
register, dissent record, named owners, refresh date and an attributable S01
gate decision. Meeting attendance alone does not convert an unknown into an
accepted conclusion.

## Known source divergence

The current branch is stacked on PR #28, while the independent continuity
correction in [PR #30](https://github.com/bstBizEra/biztrust_guide/pull/30) is
based on `main`. Until PR #30 merges or is composed into this branch,
`scripts/validate_continuity.py` still emits the obsolete `NS-026`. The control
room records `NS-001` because Issue #29 and PR #30 document why it is the
current human-owned action. A receiving agent must inspect both records and
must not interpret structural validator success as proof of factual currency.
