# BizTrust Architecture Pack

This directory turns the architecture source drafts into a controlled, reviewable pack. It is the detailed companion to the HTML guide.

## Authority and status

`BIZTRUST-ARCH-001` is currently **DRAFT FOR CONTRACT FREEZE**. It describes the recommended baseline; it does not prove that the BizTrust production platform exists, is secure, is compliant, or has been authorized for implementation.

Interpret statements by status:

| Status | Meaning | Required next step |
|---|---|---|
| `INVARIANT_CANDIDATE` | A rule proposed as non-negotiable | Architecture authority accepts, revises or rejects it |
| `PROPOSED_DECISION` | A recommended design awaiting its ADR | Resolve the linked ADR and record consequences |
| `IMPLEMENTATION_CANDIDATE` | A tool or technique requiring a spike | Verify compatibility, operations, security and cost |
| `JURISDICTION_DEPENDENT` | Legal, regulatory or accounting treatment varies | Obtain qualified human review for the target market |
| `EVIDENCE_REQUIRED` | A claim that must be demonstrated mechanically | Bind test evidence to an approved source revision |

No agent may silently promote a status. Acceptance requires an explicit authority record.

## Documents

| Document | Purpose |
|---|---|
| [`BIZTRUST-ARCH-001.md`](BIZTRUST-ARCH-001.md) | Parent architecture contract, invariants, ownership and standards |
| [`FLOWS.md`](FLOWS.md) | Canonical business, authorization and state-transition flows |
| [`DELIVERY_PLAN.md`](DELIVERY_PLAN.md) | P0–P3 scope, architecture gates and controlled execution order |
| [`DOMAIN_MODEL.md`](DOMAIN_MODEL.md) | Artifact hierarchy, conceptual ERD, core concepts and snapshot rules |
| [`AUTHORIZATION_BASELINE.md`](AUTHORIZATION_BASELINE.md) | Candidate roles, capability matrix, approvals and enforcement layers |
| [`FOUNDATION_SEQUENCE.md`](FOUNDATION_SEQUENCE.md) | Dependency-ordered S01–S11 architecture completion sequence and issue contract |
| [`TENANT_AUTHORITY_PROFILE_TEMPLATE.md`](TENANT_AUTHORITY_PROFILE_TEMPLATE.md) | First-slice evidence template for authority, jurisdiction, product and money regimes |
| [`ADR_REGISTER.md`](ADR_REGISTER.md) | ADR-001…020 status and minimum acceptance evidence |
| [`p0/README.md`](p0/README.md) | P0 design pack: the template, naming and status rules for one engineering design per P0 epic; designs land there as `PROPOSED` |
| [`SOURCE_RECONCILIATION.md`](SOURCE_RECONCILIATION.md) | Source fingerprints, promoted content, resolved conflicts and deferred questions |
| [`../research/architecture-foundation/report-source.md`](../research/architecture-foundation/report-source.md) | Primary-source research ledger, gap matrix and claim-to-source map |

## Canonical reading order

1. Repository [`AGENTS.md`](../../AGENTS.md)
2. [`badf/current-state.json`](../../badf/current-state.json)
3. [`badf/next-actions.json`](../../badf/next-actions.json)
4. This index and `BIZTRUST-ARCH-001`
5. `FOUNDATION_SEQUENCE` and the active architecture issue
6. `TENANT_AUTHORITY_PROFILE_TEMPLATE` while executing S01
7. `FLOWS`
8. `DOMAIN_MODEL` and `AUTHORIZATION_BASELINE`
9. `DELIVERY_PLAN`
10. `ADR_REGISTER`
11. The research ledger and `SOURCE_RECONCILIATION` when changing architecture content
12. Accepted ADRs and Work Packages when they exist

If this pack conflicts with an accepted ADR, the ADR governs and this pack must be corrected in the same Work Package.
