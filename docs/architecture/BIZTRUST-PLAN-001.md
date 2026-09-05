# BIZTRUST-PLAN-001 — Architecture-to-Production Delivery Plan

| Field | Value |
|---|---|
| Version | `1.0-draft` |
| Status | `PROPOSED — PLANNING BASELINE, AUTHORITY REQUIRED PER WORK PACKAGE` |
| Parent | `BIZTRUST-ARCH-001` |
| Supersedes | [`DELIVERY_PLAN.md`](DELIVERY_PLAN.md) `0.1-draft`, in part: the phase partition and the epic homes. Not yet its gates, decomposition rule, backlog or exit criteria, which part two carries ([#156](https://github.com/bstBizEra/biztrust_guide/issues/156)) |
| Source | The operator's roadmap, [`../research/roadmap/BIZTRUST-ROADMAP-001-operator-draft.md`](../research/roadmap/BIZTRUST-ROADMAP-001-operator-draft.md), 2026-09-05, cited below by its section numbers; and `DELIVERY_PLAN.md` v0.1, cited by its section numbers |
| Map | [Engineering Guide v2.0 map, issue #153](https://github.com/bstBizEra/biztrust_guide/issues/153); this document resolves ticket [#155](https://github.com/bstBizEra/biztrust_guide/issues/155) |
| Decided under | `BIZTRUST-GUIDE-WP-048`, issue [#181](https://github.com/bstBizEra/biztrust_guide/issues/181) |

Nothing in this document is accepted, and nothing it names is implemented. It is the proposed partition of the delivery work between the architecture contract and production, written so that every epic the previous plan defined keeps a home and every new epic cites where it came from. Acceptance is the architecture authority's at `BT-G0`; implementation of any phase needs a Work Package with explicit, expiring authority, which this repository cannot grant (`AGENTS.md` sections 1 and 12).

## 0. Relation to the previous plan

`DELIVERY_PLAN.md` v0.1 defined four phases, P0 to P3, and 46 epics. The phase manuals under `phases/` render that file, and `tests/test_phase_pages.py` fails if they disagree with it. So this document does not overwrite it. Until the manuals are rewritten under tickets [#165](https://github.com/bstBizEra/biztrust_guide/issues/165) to [#170](https://github.com/bstBizEra/biztrust_guide/issues/170), the previous plan remains the record the manuals render, and this document is the record of where the partition is going. Section 9 maps every epic from the one to the other. When the last manual moves, the previous plan's sections 3 to 6 are retired and this document takes the file's place.

## 1. Naming rule

Three things are named here and must never be confused (previous plan, section 1; roadmap, section 1):

| Term | Meaning | Identifiers |
|---|---|---|
| Stage | How one Work Package is delivered: nine stages, unchanged | `ENG-G0` to `ENG-G8` lifecycle gates |
| Phase | What is delivered between the architecture contract and production | Architecture, P0, P1, P2, P3, then Continuous Operations |
| Gate | A platform capability milestone that closes a phase | `BT-G0` onward; the executive labels A to E and the mapping between them are part two's |

**Epic identifier rule.** P0 keeps its identifiers, `P0.1` to `P0.12`, with the same meaning in both plans. Every other phase uses the roadmap's group letter so that no new identifier can be mistaken for an old one: `P1A.n`, `P1B.n`, `P1C.n`; `P2A.n` to `P2F.n`; `P3A.n` to `P3J.n`. While the previous plan stands, `P1.n`, `P2.n` and `P3.n` refer only to it.

## 2. The five phases

The roadmap's section 1, unchanged in substance:

| Phase | Name | Strategic purpose | Trust established |
|---|---|---|---|
| Architecture | Design the Foundation | Create the normative contract from which engineering is authorised | Trust in the design |
| P0 | Identity and Tenant | Prove identity, authority and isolation before any insurance data | Trust in identity, authorisation and tenant isolation |
| P1 | Insurance | Build broker-native insurance operations | Trust in the insurance lifecycle |
| P2 | Payment and Finance | Control money, ledger, commission, settlement and reconciliation | Trust in financial integrity |
| P3 | Production | Operate securely and reliably | Trust in production operation |

After P3, **Continuous Operations** (measure, learn, improve, expand) is an operating lifecycle, not a build phase, and the expansion streams of section 8 are named there. The previous plan's section 10 said post-P3 work must not be labelled P4 to P9 because that would imply an unreviewed sequencing commitment; the streams keep that rule by carrying no sequence number.

The executive interpretation is the roadmap's section 15: architecture establishes trust in the design; P0 in identity, authorisation and tenant isolation; P1 in brokerage operations; P2 in money, commissions, settlement and reconciliation; P3 in continuous, safe operation.

## 3. Architecture — Design the Foundation

The architecture phase is the contract freeze already under way: Work Package `BIZTRUST-WP-ARCH-001A` ([#27](https://github.com/bstBizEra/biztrust_guide/issues/27)), its eleven decision slices S01 to S11 as sequenced in [`FOUNDATION_SEQUENCE.md`](FOUNDATION_SEQUENCE.md), the twenty decisions of the [ADR register](ADR_REGISTER.md), and the contract family of [`DOMAIN_MODEL.md`](DOMAIN_MODEL.md) section 1. It has no epics of its own in this plan; its work items are the slices. It closes at `BT-G0`, whose questions the roadmap's section 3 restates as Gate A and the contract's section 17 states as exit criteria.

What the roadmap's section 3 adds to the family, `UX-001` and `OPS-001`, and the doctrine it draws in section 2, enter the contract through ticket [#158](https://github.com/bstBizEra/biztrust_guide/issues/158), not here.

## 4. P0 — Identity and Tenant

**Objective** (previous plan, section 3, with the roadmap's section 4 wording): prove who performed what, under which tenant, with which authority, against which resource, before any client, policy, claim or premium data exists on the platform. P0 carries no insurance function.

The twelve epics are unchanged from the previous plan and keep their identifiers:

| Epic | Deliverable | Exit evidence |
|---|---|---|
| P0.1 | `BIZTRUST-ARCH-001` and ADR-001…020 | Authority record and resolved findings |
| P0.2 | Repository and module boundaries | Build, dependency and boundary tests |
| P0.3 | Logto integration spike | Token-validation evidence |
| P0.4 | Organization-to-tenant mapping | Mapping and mismatch tests |
| P0.5 | Tenant provisioning | Repeatable Tenant A and B provisioning |
| P0.6 | PostgreSQL tenancy model | Migration and ownership tests |
| P0.7 | RLS enforcement | Cross-tenant read/write/delete denial |
| P0.8 | API conventions | Linted OpenAPI baseline |
| P0.9 | Event conventions | Linted AsyncAPI/event envelope |
| P0.10 | Audit framework | Attributable denial and success evidence |
| P0.11 | Observability baseline | Logs, metrics and traces linked by request |
| P0.12 | Secrets/configuration management | Rotation and least-privilege evidence |

The roadmap's section 4 groups the same work as identity, tenancy, authorisation, data isolation and platform controls, and adds two surfaces: a control-plane web surface and a mobile identity surface. Ticket [#157](https://github.com/bstBizEra/biztrust_guide/issues/157) decides their placement; the charting decision on the map is that the web surface becomes `P0.13` after the independent security proof and outside the `BT-G1` matrix, and mobile identity moves to P1. Neither is listed here until that ticket resolves.

The P0 mandatory proof and the rule that no P1 authorisation may issue until it passes independently stand in the previous plan's section 3 and are carried into this document by the P0 manual ticket ([#166](https://github.com/bstBizEra/biztrust_guide/issues/166)), so that they have one home at a time. The engineering designs for P0.2 to P0.12 are the [P0 design pack](p0/README.md).

## 5. P1 — Insurance

**Objective** (roadmap, section 5): build the broker-native insurance operating platform as one macro-phase with three controlled sub-phases, so that the previous plan's P1 and P2 keep their content and the product engine the roadmap adds has a home.

### 5.1 P1A — Broker core

The previous plan's P1 (section 4), objective unchanged: a manual-insurer-assisted quote-to-policy lifecycle with correct broker and insurer boundaries. Automation of insurer APIs is not required; correct state, evidence and ownership are.

| Epic | Capability | Was |
|---|---|---|
| P1A.1 | Party and client account | P1.1 |
| P1A.2 | Client 360 and relationship view | P1.2 |
| P1A.3 | Risk profile and submission snapshot | P1.3 |
| P1A.4 | Insurer-product provenance and immutable distribution product version | P1.4 |
| P1A.5 | Submission lifecycle | P1.5 |
| P1A.6 | Manual insurer/delegated offer and revisions; broker indication kept distinct | P1.6 |
| P1A.7 | Coverage comparison | P1.7 |
| P1A.8 | Broker recommendation and disclosures | P1.8 |
| P1A.9 | Client acceptance evidence | P1.9 |
| P1A.10 | Bind request and authority-supported coverage evidence | P1.10 |
| P1A.11 | Broker policy register | P1.11 |
| P1A.12 | Documents and audit trail | P1.12 |
| P1A.13 | Basic broker portal | P1.13 |

The vertical-slice acceptance flow of the previous plan's section 4 is P1A's acceptance and is carried by the P1 manual ticket ([#167](https://github.com/bstBizEra/biztrust_guide/issues/167)).

### 5.2 P1B — Professional brokerage lifecycle

The previous plan's P2 (section 5), objective unchanged: expand the core into professional placement, servicing, claims advocacy and renewal operations. Exits only when delayed, duplicate and conflicting external interactions have been exercised without corrupting broker state.

| Epic | Capability | Was |
|---|---|---|
| P1B.1 | Placement workspace and insurer panel | P2.1 |
| P1B.2 | Market requests and communication evidence | P2.2 |
| P1B.3 | Quote revision and coverage matrix | P2.3 |
| P1B.4 | Durable binding workflow | P2.4 |
| P1B.5 | Policy endorsement and cancellation workflow | P2.5 |
| P1B.6 | Claims notification and broker advocacy | P2.6 |
| P1B.7 | Renewal case and market re-engagement | P2.7 |
| P1B.8 | Tasks, diary and SLA controls | P2.8 |
| P1B.9 | Compliance, consent and advice file | P2.9 |
| P1B.10 | Event infrastructure and workflow operations | P2.10 |

### 5.3 P1C — Product engine and digital insurance

New in this plan, from the roadmap's section 5 (P1C, the package recommendation engine, and the P1 mobile clients). The product engine exists so that insurance products are versioned configuration rather than hard-coded branches, which is ADR-006's question; the straight-through model and the professional model run on the same core with different workflow configuration.

| Epic | Capability | Source |
|---|---|---|
| P1C.1 | Insurance product engine: product, version, class, risk and question schemas, coverage definition, document templates, payment and commission rules, workflow definition, channel configuration, as versioned configuration | Roadmap section 5, P1C canonical structure; ADR-006 |
| P1C.2 | Eligibility rules and question schemas evaluated per product version | Roadmap section 5, P1C |
| P1C.3 | Pricing provider and carrier-rule adapter, keeping a broker indication distinct from an insurer quote | Roadmap section 5, P1C; ADR-017 |
| P1C.4 | Straight-through digital insurance workflow: customer input, eligibility, pricing, quote, acceptance, payment hand-off, insurer confirmation, policy or certificate | Roadmap section 5, straight-through model; payment execution is P2's |
| P1C.5 | Package recommendation engine, price-driven and coverage-driven | Roadmap section 5, package recommendation engine |
| P1C.6 | Customer mobile client: discover, compare, quote, apply, policy, certificate, claims, renewal, notifications | Roadmap section 5, P1 Mobile; payment execution authoritative in P2 |
| P1C.7 | Agent mobile client: prospect onboarding, client verification, quote support, document capture, servicing, policy lookup, claim assistance | Roadmap section 5, P1 Mobile |
| P1C.8 | Channel configuration and insurer-adapter binding per product version | Roadmap section 5, P1C |

The roadmap's P1 Web list (the broker workstation) is not a new epic: it is the surface P1A.13 grows into across P1A and P1B, and the P1 manual ticket decides how it is shown.

### 5.4 Authority boundaries P1 must keep

From the roadmap's section 5 and the contract's invariant candidates INV-005, INV-016 and INV-022: a broker bind request is not a carrier bind confirmation; a broker policy record is not the insurer's authoritative policy; a broker claim status is not the insurer's adjudication status. These are the same boundary the landing page states as "a request is not a confirmation".

## 6. P2 — Payment and Finance

**Objective** (previous plan, section 6, with the roadmap's section 6 wording): close the insurance-to-money-to-insurer loop with attributable, reconcilable records, so that payment, ledger, commission, settlement and reconciliation are each their own thing. The roadmap's rule that invoice, payment, payment intent, payment attempt, payment allocation, ledger, commission, settlement, reconciliation and refund must never collapse into one object is carried as P2's design constraint.

The nine finance epics of the previous plan's P3 become P2's epics, grouped by the roadmap's capability groups:

| Epic | Capability | Was |
|---|---|---|
| P2A.1 | Invoice and premium due | P3.1 |
| P2A.2 | Payment intent, attempt and allocation | P3.2 |
| P2A.3 | Payment adapter and signed webhook handling | P3.3 |
| P2A.4 | Refund, reversal and chargeback | P3.4 |
| P2B.1 | Immutable double-entry insurance subledger | P3.5 |
| P2C.1 | Versioned broker and agent commission | P3.6 |
| P2D.1 | Insurer settlement and remittance | P3.7 |
| P2E.1 | Bank/provider/ledger reconciliation | P3.8 |
| P2F.1 | Insurer and payment Adapter SDKs | P3.9 |

The previous plan's P3.10, partner API and versioned webhooks, and P3.11, Tenant Pack validation foundation, are not P2 work: they are the first items of the expansion streams E2 and E1 in section 8, and section 9 records the move. The end-to-end evidence sentence of the previous plan's section 6 remains P2's exit condition and is carried by the P2 manual ticket ([#168](https://github.com/bstBizEra/biztrust_guide/issues/168)); the failure cases the roadmap's Gate D lists are part two's.

## 7. P3 — Production

**Objective** (roadmap, section 7): prove that the whole system can be operated, from working software to reliable service. The previous plan had no production phase; P0.11 and P0.12 laid baselines that P3 scales.

| Epic | Capability | Source |
|---|---|---|
| P3A.1 | Environment architecture and controlled promotion: local, development, test, staging, pre-production, production | Roadmap section 7, P3A |
| P3B.1 | The canonical pipeline: lint, unit, build, dependency and secret scanning, SAST, contract and integration tests, tenant security tests, artifact, staging, end-to-end, DAST, performance and resilience, release evidence, authorisation, production | Roadmap section 7, P3B |
| P3C.1 | Release engineering: feature flags, canary, rolling and blue-green deployment, rollback, database and API compatibility, mobile compatibility matrix | Roadmap section 7, P3C |
| P3D.1 | Observability at production scale: every meaningful transaction reconstructable through log, metric, trace and audit event | Roadmap section 7, P3D; P0.11 |
| P3E.1 | Reliability controls: scaling, queueing, retries, circuit breakers, dead-letter handling, replication, backup, tested restore, failover, graceful degradation | Roadmap section 7, P3E |
| P3F.1 | Service-level indicators and objectives for the initial indicator set | Roadmap section 7, P3F |
| P3G.1 | Disaster recovery: recovery point and time objectives, tested | Roadmap section 7, P3G |
| P3H.1 | Mobile production: build, internal test, beta, store review, production, monitoring; minimum version and forced upgrade | Roadmap section 7, P3H |
| P3I.1 | Security operations: continuous detection across authentication, tenancy, privilege, API, payment, dependencies, secrets, drift | Roadmap section 7, P3I |
| P3J.1 | Incident management: detect, triage, contain, restore, investigate, correct, postmortem, prevent; a severity scale | Roadmap section 7, P3J |

The definitions these epics rest on are sourced in the map's research: release engineering, reliability and disaster recovery ([#161](https://github.com/bstBizEra/biztrust_guide/issues/161)) and mobile release pipelines ([#162](https://github.com/bstBizEra/biztrust_guide/issues/162)). Two findings bind this table: no primary source defines a rollback for a store release, so P3C.1 and P3H.1 plan on halting and shipping forward; and no current standard defines an incident severity scale, so P3J.1's scale is a local decision and must be labelled one. Gate E's evidence list is part two's.

## 8. Continuous Operations and the expansion streams

After `BT-G7` is recorded and Production v1.0 is released, Continuous Operations runs: measure, learn, improve, expand. The roadmap's section 13 converts the earlier P4 to P9 proposals into eight streams with no sequence number, which is what the previous plan's section 10 required:

| Stream | Capability | Carries from the previous plan |
|---|---|---|
| E1 Tenant Scale | Tenant Pack SDK, white-labelling, product packs | P3.11 Tenant Pack validation foundation |
| E2 Embedded Insurance | Developer portal, partner APIs, SDKs | P3.10 Partner API and versioned webhooks |
| E3 Integration Scale | More insurer, payment and bank adapters | — |
| E4 Workflow Scale | Event-driven and workflow-engine extraction | — |
| E5 Enterprise Isolation | Dedicated schema or database deployment | — |
| E6 Advanced Brokerage | Richer claims, renewals, placement analytics | — |
| E7 Intelligence | Recommendations, assistants, document intelligence, anomaly detection | — |
| E8 Ecosystem | Marketplace, insurer ecosystem, embedded distribution | — |

Entry conditions, ordering and design of the streams are out of this plan's scope until Production v1.0 exists.

## 9. Epic mapping: previous plan to this plan

Every one of the previous plan's 46 epics, once:

| Was | Label | Now | Note |
|---|---|---|---|
| P0.1 | `BIZTRUST-ARCH-001` and ADR-001…020 | P0.1 | Unchanged; the architecture phase's output |
| P0.2 | Repository and module boundaries | P0.2 | Unchanged |
| P0.3 | Logto integration spike | P0.3 | Unchanged |
| P0.4 | Organization-to-tenant mapping | P0.4 | Unchanged |
| P0.5 | Tenant provisioning | P0.5 | Unchanged |
| P0.6 | PostgreSQL tenancy model | P0.6 | Unchanged |
| P0.7 | RLS enforcement | P0.7 | Unchanged |
| P0.8 | API conventions | P0.8 | Unchanged |
| P0.9 | Event conventions | P0.9 | Unchanged |
| P0.10 | Audit framework | P0.10 | Unchanged |
| P0.11 | Observability baseline | P0.11 | Unchanged; P3D.1 scales it |
| P0.12 | Secrets/configuration management | P0.12 | Unchanged |
| P1.1 | Party and client account | P1A.1 | Renumbered |
| P1.2 | Client 360 and relationship view | P1A.2 | Renumbered |
| P1.3 | Risk profile and submission snapshot | P1A.3 | Renumbered |
| P1.4 | Insurer-product provenance and immutable distribution product version | P1A.4 | Renumbered; P1C.1 generalises it into the product engine |
| P1.5 | Submission lifecycle | P1A.5 | Renumbered |
| P1.6 | Manual insurer/delegated offer and revisions; broker indication kept distinct | P1A.6 | Renumbered |
| P1.7 | Coverage comparison | P1A.7 | Renumbered |
| P1.8 | Broker recommendation and disclosures | P1A.8 | Renumbered |
| P1.9 | Client acceptance evidence | P1A.9 | Renumbered |
| P1.10 | Bind request and authority-supported coverage evidence | P1A.10 | Renumbered |
| P1.11 | Broker policy register | P1A.11 | Renumbered |
| P1.12 | Documents and audit trail | P1A.12 | Renumbered |
| P1.13 | Basic broker portal | P1A.13 | Renumbered; grows into the broker workstation |
| P2.1 | Placement workspace and insurer panel | P1B.1 | Moved into P1 as its second sub-phase |
| P2.2 | Market requests and communication evidence | P1B.2 | Moved |
| P2.3 | Quote revision and coverage matrix | P1B.3 | Moved |
| P2.4 | Durable binding workflow | P1B.4 | Moved |
| P2.5 | Policy endorsement and cancellation workflow | P1B.5 | Moved |
| P2.6 | Claims notification and broker advocacy | P1B.6 | Moved |
| P2.7 | Renewal case and market re-engagement | P1B.7 | Moved |
| P2.8 | Tasks, diary and SLA controls | P1B.8 | Moved |
| P2.9 | Compliance, consent and advice file | P1B.9 | Moved |
| P2.10 | Event infrastructure and workflow operations | P1B.10 | Moved |
| P3.1 | Invoice and premium due | P2A.1 | Moved into P2 |
| P3.2 | Payment intent, attempt and allocation | P2A.2 | Moved |
| P3.3 | Payment adapter and signed webhook handling | P2A.3 | Moved |
| P3.4 | Refund, reversal and chargeback | P2A.4 | Moved |
| P3.5 | Immutable double-entry insurance subledger | P2B.1 | Moved |
| P3.6 | Versioned broker and agent commission | P2C.1 | Moved |
| P3.7 | Insurer settlement and remittance | P2D.1 | Moved |
| P3.8 | Bank/provider/ledger reconciliation | P2E.1 | Moved |
| P3.9 | Insurer and payment Adapter SDKs | P2F.1 | Moved |
| P3.10 | Partner API and versioned webhooks | E2 | Moved to an expansion stream; first item of E2 |
| P3.11 | Tenant Pack validation foundation | E1 | Moved to an expansion stream; first item of E1 |

Counts: 12 unchanged, 13 renumbered, 21 moved within the production-critical plan, 2 moved to expansion streams; 46 in all. New in this plan: 8 epics in P1C and 10 in P3, 18 in all; `P0.13` pending [#157](https://github.com/bstBizEra/biztrust_guide/issues/157).

## 10. What this document does not yet carry

- **Gates** `BT-G0` to `BT-G7`, the executive labels A to E, Gate E's evidence list, the expansion streams' entry conditions, the eight cross-cutting tracks and the Definition of Done: part two, [#156](https://github.com/bstBizEra/biztrust_guide/issues/156). Until then the previous plan's section 7 is the gate table.
- **The Work Package decomposition rule, the recommended backlog and the exit from planning**: the previous plan's sections 8, 9 and 11 stand.
- **P0.13 and mobile identity**: [#157](https://github.com/bstBizEra/biztrust_guide/issues/157).
- **Doctrine and contract family**: [#158](https://github.com/bstBizEra/biztrust_guide/issues/158), which waits on the contract map's waiver.
- **The manuals**: [#165](https://github.com/bstBizEra/biztrust_guide/issues/165) to [#170](https://github.com/bstBizEra/biztrust_guide/issues/170); until they move, `phases/` renders the previous plan.

## 11. Sources

- The operator's roadmap draft, sections 1, 2, 4, 5, 6, 7, 13 and 15, as transcribed at [`../research/roadmap/BIZTRUST-ROADMAP-001-operator-draft.md`](../research/roadmap/BIZTRUST-ROADMAP-001-operator-draft.md).
- [`DELIVERY_PLAN.md`](DELIVERY_PLAN.md) v0.1, sections 1, 3 to 7 and 10.
- [`FOUNDATION_SEQUENCE.md`](FOUNDATION_SEQUENCE.md), [`ADR_REGISTER.md`](ADR_REGISTER.md), [`DOMAIN_MODEL.md`](DOMAIN_MODEL.md) section 1, [`BIZTRUST-ARCH-001.md`](BIZTRUST-ARCH-001.md) sections 5 and 17.
- Research on the Guide v2 map: [#161](https://github.com/bstBizEra/biztrust_guide/issues/161), [#162](https://github.com/bstBizEra/biztrust_guide/issues/162), [#163](https://github.com/bstBizEra/biztrust_guide/issues/163), [#164](https://github.com/bstBizEra/biztrust_guide/issues/164), on their `research/<slug>` branches.
