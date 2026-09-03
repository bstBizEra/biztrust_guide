# BizTrust ADR Register

| Field | Value |
|---|---|
| Version | `0.1-draft` |
| Status | `TRACKING REGISTER — NO ADR ACCEPTED BY THIS FILE` |
| Parent Work Package | [`BIZTRUST-WP-ARCH-001A`](https://github.com/bstBizEra/biztrust_guide/issues/27) |

An ADR can move from `DRAFT_REQUIRED` only through the authority and review process defined by its Work Package. A mention in the HTML guide, architecture contract or source draft is not acceptance.

| ADR | Decision question | Current status | Minimum acceptance evidence |
|---|---|---|---|
| ADR-001 | Should BizTrust begin as a modular monolith? | `DRAFT_REQUIRED` | Boundary tests, extraction criteria and deployment tradeoff review |
| ADR-002 | Should Logto provide identity infrastructure? | `DRAFT_REQUIRED` | Capability, security, operations, licensing and exit-strategy spike |
| ADR-003 | How does Logto organization context map to BizTrust tenant authority? | `DRAFT_REQUIRED` | Token claims, mapping lifecycle and mismatch tests |
| ADR-004 | Should shared PostgreSQL plus RLS be the default tenant isolation tier? | `DRAFT_REQUIRED` | RLS design, owner/bypass analysis and cross-tenant proof plan |
| ADR-005 | Should OpenAPI 3.2 define contract-first HTTP APIs? | `DRAFT_REQUIRED` | Toolchain compatibility, linting and breaking-change policy |
| ADR-006 | How are BizTrust distribution configurations and authorized insurance-product representations versioned? | `DRAFT_REQUIRED` | Historical reproduction, source provenance and publication-governance tests |
| ADR-007 | Which facts are broker-authoritative versus insurer-authoritative? | `DRAFT_REQUIRED` | Ownership matrix and lifecycle transition review |
| ADR-008 | How is the immutable double-entry insurance subledger represented? | `DRAFT_REQUIRED` | Balanced posting, reversal and jurisdiction/accounting review |
| ADR-009 | How do external providers integrate without leaking into the domain core? | `DRAFT_REQUIRED` | Adapter contract, failure, security and provider-exit tests |
| ADR-010 | Which long-running operations require durable workflows and which runtime is suitable? | `DRAFT_REQUIRED` | Workflow replay/versioning and operational spike |
| ADR-011 | How do Tenant Packs provide extension without tenant forks or unrestricted code? | `DRAFT_REQUIRED` | Schema, signing, compatibility and sandbox threat model |
| ADR-012 | How are financial and binding mutations idempotent under retry and concurrency? | `DRAFT_REQUIRED` | Key scope, retention, replay response, race and duplicate tests |
| ADR-013 | Who may create authoritative cover, under which insurer or delegated authority, and with what evidence? | `BLOCKED_BY_S01` | Tenant authority profiles, operative-agreement review and effective-cover scenarios |
| ADR-014 | Which client-money/risk-transfer regime governs premium, claims money and refunds? | `BLOCKED_BY_S01` | Qualified jurisdiction/finance review, funds-flow scenarios and reconciliation obligations |
| ADR-015 | How are valid time, record time, correction, supersession and effective timezone represented? | `DRAFT_REQUIRED` | Backdated, future-dated, corrected bind/MTA/cancel/renewal scenarios and query tests |
| ADR-016 | How are co-insurance, layers, facilities, master policies, certificates, bordereaux and account-current represented? | `BLOCKED_BY_S01` | Representative simple/share/layer/scheme scenarios and authority review |
| ADR-017 | Who owns product, wording, rating, indication and insurer quote, and how is provenance retained? | `BLOCKED_BY_S01` | Systems-of-record matrix and examples for broker indication versus insurer/delegated offer |
| ADR-018 | How do premium warranties and non-payment affect cover without letting payment systems invent insurance state? | `BLOCKED_BY_S01` | Authority-aware transition table, non-payment scenarios and cross-context invariant tests |
| ADR-019 | Which jurisdiction, residency, retention, localization, legal-hold and disclosure rules govern each data class? | `BLOCKED_BY_S01` | Qualified legal/privacy review and data-location/retention matrix |
| ADR-020 | How are endorsement, cancellation, refund, commission earning/clawback and renewal modeled as historical transactions? | `DRAFT_REQUIRED` | Worked MTA/cancellation/renewal scenarios, day-count/rounding rules and reproduction tests |

## Required ADR structure

Every ADR must include:

- status, owner, date and supersession links;
- business and technical context;
- precise decision question;
- decision and scope;
- alternatives considered, including “defer”;
- positive and negative consequences;
- security, privacy, compliance, operations and cost effects;
- migration and rollback implications;
- implementation constraints;
- validation and conformance evidence;
- unresolved dissent and authority record.

## Status vocabulary

```text
DRAFT_REQUIRED
BLOCKED_BY_S01
PROPOSED
IN_REVIEW
ACCEPTED
REJECTED
SUPERSEDED
DEPRECATED
```

Only the designated architecture authority may mark an ADR `ACCEPTED`, and only after required independent lenses have recorded their review.
