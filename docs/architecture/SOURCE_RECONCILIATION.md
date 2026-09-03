# Architecture Source Reconciliation

| Field | Value |
|---|---|
| Work Package | `BIZTRUST-GUIDE-WP-003` |
| Purpose | Preserve source provenance and editorial decisions so later agents do not repeat or reverse the reconciliation accidentally |
| Output status | Documentation integration only; architecture acceptance remains pending |

## Source fingerprints

| Supplied source | SHA-256 | Primary contribution |
|---|---|---|
| `Pasted markdown.md` | `2eac78f8e20f605efe328696b11ef0986d490b030be430f2e79068a47b6ee9ec` | Platform position, tenant model, product engine, API/payment model, open-source and integration strategy |
| `Pasted markdown (2).md` | `55dd4909df64166ad84e3d56ed27c1a1592abc52a5732ed604e5b200601cff9e` | Artifact hierarchy, invariants, ERD, RBAC, state machines, P0–P3 plan and architecture gates |

The raw drafts are not copied into the repository because they substantially duplicate one another and contain unresolved recommendations. This reconciliation record preserves what was promoted, normalized, deferred or rejected.

## Promotion matrix

| Source topic | Integrated location | Treatment |
|---|---|---|
| BizTrust as broker core, not insurer core | `BIZTRUST-ARCH-001` §1 | Promoted as platform-position proposal with explicit delegated-authority qualification |
| Tenant as business and security boundary | `BIZTRUST-ARCH-001` §7 | Promoted with negative proof requirements |
| Logto organization mapping | `BIZTRUST-ARCH-001` §8; `FLOWS` §3 | Marked proposed pending ADR-002/003 |
| PostgreSQL RLS | `BIZTRUST-ARCH-001` §7; `FLOWS` §3 | Marked proposed pending ADR-004; defense-in-depth clarified |
| Domain lists | `BIZTRUST-ARCH-001` §6 | Normalized into capability groups; no fixed service count |
| Broker lifecycle | `FLOWS` §1–2 | Promoted; authority/effective-cover boundary strengthened |
| Product-as-configuration | `BIZTRUST-ARCH-001` §10 | Qualified as broker distribution configuration with source authority and immutable historical versions |
| OpenAPI, AsyncAPI and errors | `BIZTRUST-ARCH-001` §11 | Versions verified from primary sources and marked proposed |
| ACORD compatibility | `BIZTRUST-ARCH-001` §14 | Retained as an optional mapping layer, not canonical storage |
| Payment API and accounting | `BIZTRUST-ARCH-001` §13; `FLOWS` §12–14 | Promoted with jurisdiction/accounting warning |
| Durable workflow and events | `BIZTRUST-ARCH-001` §12; `FLOWS` §15 | Promoted as patterns; named products remain spike candidates |
| Module command/query/event table | `FLOWS` §4 | Normalized and labeled candidate contract language |
| RBAC matrix | Architecture authorization model | Role/permission/scope/condition/authority concept retained; exact grants deferred to IAM contract |
| State machines | `FLOWS` §6–13 | Promoted with immutable offer revisions, temporal semantics and policy dimensions |
| P0–P3 plan | `DELIVERY_PLAN` | Promoted as the near-term planning baseline |
| Architecture gates | `DELIVERY_PLAN` §7 | Renamed `BT-G0…BT-G6` to avoid lifecycle-gate collision |
| Required ADRs | `BIZTRUST-ARCH-001` §16; `ADR_REGISTER` | Expanded from 12 to 20 after issue #15; none marked accepted |

## Conflicts resolved

### 1. Roadmap scope

One source proposed P0–P9 while the other proposed P0–P3. The guide uses P0–P3 as the reviewable near-term baseline. Later capabilities remain an uncommitted horizon so agents do not infer sequencing or authority from speculative phase numbers.

### 2. Gate identifiers

The existing engineering guide already used `G0…G8` for the delivery lifecycle, while the architecture draft used `G0…G6` for platform milestones. The normalized identifiers are:

- `ENG-G0…ENG-G8` — Work Package lifecycle;
- `BT-G0…BT-G6` — BizTrust platform capability;
- `P0…P3` — delivery phases.

### 3. Domain count

The source described “18 bounded contexts” but listed more than 18 responsibilities across its tables. The guide therefore uses candidate capability groups and explicitly delegates final bounded-context classification to `BIZTRUST-DOMAIN-001`.

### 4. Technology commitment

The drafts named Logto, APISIX, PostgreSQL, Temporal, NATS and OpenFGA with varying degrees of certainty. The guide distinguishes:

- proposed architecture decisions requiring ADRs;
- implementation candidates requiring bounded spikes;
- stable behavioral invariants that should survive tool replacement.

No dependency is described as adopted merely because it appeared in a source diagram.

### 5. Claims vocabulary

The sources alternated between `DENIED` and `DECLINED`. The guide uses `DECLINED` for the sourced insurer outcome and reserves “denied” for access-control decisions unless the claims-domain review selects different canonical terminology.

### 6. Policy status

The source mixed coverage, document, premium and servicing concerns in one policy state. The guide separates these into orthogonal status dimensions to avoid impossible combinations and unsafe derived coverage.

### 7. Payment-to-policy coupling

The source correctly warned that payment must not activate a policy directly. The pack strengthens this into a cross-module sequence: payment fact → binding workflow → authority/effective-cover evidence check → Policy-owned transition → approved ledger posting.

## Subsequent pre-freeze finding reconciliation

[Issue #15](https://github.com/bstBizEra/biztrust_guide/issues/15) was raised after the source drafts were prepared. It found four storage-shape topics and related domain controls absent from the twelve-ADR plan. The pack incorporates the **questions and structural capacity**, not unverified answers:

| Finding | Reconciliation |
|---|---|
| Binding/delegated authority unknown | Added authority profiles/agreements, authority-aware coverage confirmation, ADR-013 and S01 blocker |
| Client money/risk transfer absent | Added custody/risk classification, three reconciliation classes, ADR-014 and qualified review requirement |
| Effective dating absent | Added valid-time/record-time fields, correction/supersession rule and ADR-015 |
| Co-insurance/layers/master policy absent | Added placement sections/participations, master-policy/certificate/bordereau concepts and ADR-016 |
| Product/rating/quote ownership ambiguous | Split insurer product, distribution configuration, broker indication and authority offer; added ADR-017 |
| Payment can affect cover under contract terms | Added authority-aware premium-condition decision ADR-018; payment still cannot mutate cover directly |
| Jurisdiction profile empty | Added S01 profile, ADR-019 and explicit `UNKNOWN_BLOCKING` treatment |
| MTA/cancellation/refund/renewal shallow | Added ADR-020 and downstream scenario requirements |

No item in this table is an accepted legal or commercial conclusion. The supporting research and limits are recorded in `docs/research/architecture-foundation/report-source.md`.

## Deliberately deferred

- exact physical ERD columns and indexes;
- final bounded-context count;
- full endpoint payload schemas;
- exact RBAC grants, limits and approval thresholds;
- product-rule language and execution sandbox;
- chart of accounts and jurisdiction-specific posting rules;
- tenant-specific binding/delegated authority conclusions;
- current Lao PDR legal, regulatory, data-residency and client-money conclusions;
- insurer, PSP and bank provider selections;
- ACORD licensing and exact message/profile scope;
- production SLO, RTO, RPO and capacity targets;
- AI-agent functionality;
- service extraction and dedicated-tenant triggers.

## Change rule for future agents

Before changing a reconciled decision, an agent must:

1. identify the affected architecture section and Work Package;
2. cite new evidence or an accepted ADR;
3. update this reconciliation record;
4. update every published summary that repeats the changed claim, or record why a concurrent Work Package owns that update;
5. update current state, next action and checkpoint;
6. run deterministic validation;
7. request the appropriate independent review.
