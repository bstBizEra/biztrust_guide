# BIZTRUST-PLAN-001 — Architecture-to-Production Delivery Plan

| Field | Value |
|---|---|
| Version | `1.0-draft` |
| Status | `PROPOSED — PLANNING BASELINE, AUTHORITY REQUIRED PER WORK PACKAGE` |
| Parent | `BIZTRUST-ARCH-001` |
| Supersedes | [`DELIVERY_PLAN.md`](DELIVERY_PLAN.md) `0.1-draft`, in part: the phase partition and the epic homes (part one, [#155](https://github.com/bstBizEra/biztrust_guide/issues/155)) and the gate table (part two, [#156](https://github.com/bstBizEra/biztrust_guide/issues/156)). Not its decomposition rule, backlog or exit criteria, which stand until a ticket carries them |
| Source | The operator's roadmap, [`../research/roadmap/BIZTRUST-ROADMAP-001-operator-draft.md`](../research/roadmap/BIZTRUST-ROADMAP-001-operator-draft.md), 2026-09-05, cited below by its section numbers; and `DELIVERY_PLAN.md` v0.1, cited by its section numbers |
| Map | [Engineering Guide v2.0 map, issue #153](https://github.com/bstBizEra/biztrust_guide/issues/153); this document resolves tickets [#155](https://github.com/bstBizEra/biztrust_guide/issues/155) and [#156](https://github.com/bstBizEra/biztrust_guide/issues/156) |
| Decided under | Part one: `BIZTRUST-GUIDE-WP-048`, issue [#181](https://github.com/bstBizEra/biztrust_guide/issues/181). Part two: `BIZTRUST-GUIDE-WP-049`, issue [#183](https://github.com/bstBizEra/biztrust_guide/issues/183) |

Nothing in this document is accepted, and nothing it names is implemented. It is the proposed partition of the delivery work between the architecture contract and production, written so that every epic the previous plan defined keeps a home and every new epic cites where it came from. Acceptance is the architecture authority's at `BT-G0`; implementation of any phase needs a Work Package with explicit, expiring authority, which this repository cannot grant (`AGENTS.md` sections 1 and 12).

## 0. Relation to the previous plan

`DELIVERY_PLAN.md` v0.1 defined four phases, P0 to P3, and 46 epics. The P3 manual under `phases/` still renders that file, and `tests/test_phase_pages.py` fails if it disagrees with it; the overview and the P0, P1 and P2 manuals render this document. So this document does not overwrite it. Until the manuals are rewritten under tickets [#165](https://github.com/bstBizEra/biztrust_guide/issues/165) to [#170](https://github.com/bstBizEra/biztrust_guide/issues/170), the previous plan remains the record the manuals render, and this document is the record of where the partition is going. Section 9 maps every epic from the one to the other. When the last manual moves, the previous plan's sections 3 to 6 are retired and this document takes the file's place.

## 1. Naming rule

Three things are named here and must never be confused (previous plan, section 1; roadmap, section 1):

| Term | Meaning | Identifiers |
|---|---|---|
| Stage | How one Work Package is delivered: nine stages, unchanged | `ENG-G0` to `ENG-G8` lifecycle gates |
| Phase | What is delivered between the architecture contract and production | Architecture, P0, P1, P2, P3, then Continuous Operations |
| Gate | A platform capability milestone that closes a phase | `BT-G0` to `BT-G7` in the records; the executive labels A to E in presentations, mapped in section 10 |

**Epic identifier rule.** P0 keeps its identifiers, `P0.1` to `P0.12`, with the same meaning in both plans. Every other phase uses the roadmap's group letter so that no new identifier can be mistaken for an old one: `P1A.n`, `P1B.n`, `P1C.n`; `P2A.n` to `P2F.n`; `P3A.n` to `P3J.n`. While the previous plan stands, `P1.n`, `P2.n` and `P3.n` refer only to it. The map's vocabulary line, written before this rule, said `P2.n` and `P3.n`; it is amended on the map to match.

## 2. The five phases

After the roadmap's section 1, with the purposes of P0 and P2 drawn from its sections 4 and 6 rather than quoted from section 1:

| Phase | Name | Strategic purpose | Trust established |
|---|---|---|---|
| Architecture | Design the Foundation | Create the normative contract from which engineering is authorised | Trust in the design |
| P0 | Identity and Tenant | Prove identity, authority and isolation before any insurance data | Trust in identity, authorisation and tenant isolation |
| P1 | Insurance | Build broker-native insurance operations | Trust in the insurance lifecycle |
| P2 | Payment and Finance | Control money, ledger, commission, settlement and reconciliation | Trust in financial integrity |
| P3 | Production | Operate securely and reliably | Trust in production operation |

After P3, **Continuous Operations** (measure, learn, improve, expand) is an operating lifecycle, not a build phase, and the expansion streams of section 8 are named there. The previous plan's section 10 said post-P3 work must not be labelled P4 to P9 because that would imply an unreviewed sequencing commitment; the streams keep that rule by carrying no phase number.

The executive interpretation is the roadmap's section 15: architecture establishes trust in the design; P0 in identity, authorisation and tenant isolation; P1 in brokerage operations; P2 in money, commissions, settlement and reconciliation; P3 in continuous, safe operation.

## 3. Architecture — Design the Foundation

The architecture phase is the contract freeze already under way: Work Package `BIZTRUST-WP-ARCH-001A` ([#27](https://github.com/bstBizEra/biztrust_guide/issues/27)), its eleven decision slices S01 to S11 as sequenced in [`FOUNDATION_SEQUENCE.md`](FOUNDATION_SEQUENCE.md), the twenty decisions of the [ADR register](ADR_REGISTER.md), and the contract family of [`DOMAIN_MODEL.md`](DOMAIN_MODEL.md) section 1. It has no epics of its own in this plan; its work items are the slices. It closes at `BT-G0`, whose questions the roadmap's section 3 restates as Gate A and the contract's section 17 states as exit criteria.

What the roadmap's section 3 adds to the family, `UX-001` and `OPS-001`, and the doctrine it draws in section 2, enter the contract through ticket [#158](https://github.com/bstBizEra/biztrust_guide/issues/158), not here.

## 4. P0 — Identity and Tenant

**Objective** (previous plan, section 3, with the roadmap's section 4 wording): prove who performed what, under which tenant, with which authority, against which resource, before any client, policy, claim or premium data exists on the platform. P0 carries no insurance function.

The first twelve epics are unchanged from the previous plan and keep their identifiers; the thirteenth is added by ticket [#157](https://github.com/bstBizEra/biztrust_guide/issues/157) to both plans at once, since the manual renders the previous plan:

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
| P0.13 | Control-plane web surface | Tenant selection, member administration and the audit viewer exercised end to end after the independent proof, with no insurance function present |

The roadmap's section 4 groups the same work as identity, tenancy, authorisation, data isolation and platform controls under headings it numbers P0.1 to P0.7; those are group headings, not this plan's epics, and `P0.n` here always means the previous plan's epic. It adds two surfaces. The control-plane web surface (login, tenant selection, member administration, roles, business units, branch management, security settings, sessions, tenant configuration, audit viewer; roadmap section 4, group P0.5) is `P0.13`: it is how a human exercises the tenant authorization sequence, so it belongs in P0, but it is built only after the independent security proof and it is outside the `BT-G1` test matrix, which proves the substrate and not a screen. The mobile identity surface (roadmap section 4, group P0.6) is not P0 work, because no mobile client exists before P1. By the map's charting decision 4 it is `P1A.14` in section 5.1, ahead of the P1C clients (P1C.6, P1C.7) that depend on it; the P1 manual ticket ([#167](https://github.com/bstBizEra/biztrust_guide/issues/167)) may move it to P1C if the first mobile slice argues so. P0 still carries no insurance function.

The P0 mandatory proof is the previous plan's section 3 block, carried here verbatim under WP-052 ([#166](https://github.com/bstBizEra/biztrust_guide/issues/166)) so that it has one home:

- Tenant A can access authorized Tenant A data.
- Tenant A cannot read, create, update or delete Tenant B protected data.
- Missing or invalid organization context is denied.
- Tampered URL, header, body and query tenant identifiers are denied or ignored safely.
- Wrong audience, expired token, inactive membership and absent scope are denied.
- An application-level authorization bypass test remains blocked by RLS.
- Every outcome produces tenant-safe audit evidence.

No P1 authorization may be issued until this proof passes independently.

The engineering designs for P0.2 to P0.13 are the [P0 design pack](p0/README.md).

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
| P1A.14 | Mobile identity foundation: secure login, token lifecycle, biometric local unlock, tenant context, secure storage, session expiration, device revocation | New; roadmap section 4, group P0.6, moved here by [#157](https://github.com/bstBizEra/biztrust_guide/issues/157); research [#162](https://github.com/bstBizEra/biztrust_guide/issues/162) |

The vertical-slice acceptance flow of the previous plan's section 4 is P1A's acceptance; the P1 manual renders it as the first twelve steps of its execution order (WP-053, [#167](https://github.com/bstBizEra/biztrust_guide/issues/167)).

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

The previous plan's P3.10, partner API and versioned webhooks, and P3.11, Tenant Pack validation foundation, are not P2 work: they are the first items of the expansion streams E2 and E1 in section 8, and section 9 records the move. The end-to-end evidence sentence of the previous plan's section 6 remains P2's exit condition; the P2 manual renders it as the last item of its exit checklist (WP-054, [#168](https://github.com/bstBizEra/biztrust_guide/issues/168)); the failure cases the roadmap's Gate D lists are in section 10.3.

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

The definitions these epics rest on are sourced in the map's research: release engineering, reliability and disaster recovery ([#161](https://github.com/bstBizEra/biztrust_guide/issues/161)) and mobile release pipelines ([#162](https://github.com/bstBizEra/biztrust_guide/issues/162)). Three findings bind this table: neither store offers a rollback for a released build, so P3H.1 plans on halting a rollout and shipping forward; the SRE sources define rollback for blue-green as a reversal of the routing change but give no standalone definition of rollback or of rolling deployment, so P3C.1 defines both locally and cites the workbook for blue-green; and no current standard defines an incident severity scale, so P3J.1's scale is a local decision and must be labelled one. Gate E's evidence list is part two's.

## 8. Continuous Operations and the expansion streams

After `BT-G7` (section 10) is recorded and Production v1.0 is released, Continuous Operations runs: measure, learn, improve, expand. The roadmap's section 13 converts the earlier P4 to P9 proposals into eight streams with no phase number, which is what the previous plan's section 10 required:

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

Entry conditions are in section 11; ordering and design of the streams are out of this plan's scope until Production v1.0 exists.

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

Counts: 12 unchanged, 13 renumbered, 19 moved within the production-critical plan (10 to P1B, 9 to P2), 2 moved to expansion streams; 46 in all. New in this plan: 8 epics in P1C, 10 in P3, `P0.13` and `P1A.14`, 20 in all.

## 10. Gates

### 10.1 Identifiers and labels

The previous plan's section 1 rule stands: two gate systems exist and must never be confused. `ENG-G0` to `ENG-G8` gate one Work Package through the nine stages; `BT-G0` onward are platform capability milestones that close a phase. This plan adds one identifier, `BT-G7`, and the roadmap's executive labels A to E as names for presentations. **Records use identifiers; presentations may use labels; a label never appears without its identifier the first time it is used on a page.** The mapping (roadmap sections 3 to 7 and 12, against the previous plan's section 7):

| Label | Roadmap name | Identifiers | Closes |
|---|---|---|---|
| A | Architecture Ready | `BT-G0` | Architecture |
| B | Identity and Tenant Proven | `BT-G1` | P0 |
| C | Insurance End-to-End Proven | `BT-G2` and `BT-G3` | P1 (P1A at `BT-G2`; P1B and P1C at `BT-G3`) |
| D | Financial Integrity Proven | `BT-G4` and `BT-G5` | P2 |
| E | Production Ready | `BT-G7`, with `BT-G6` judged inside it | P3 |

`BT-G6 Tenant Ready` keeps its identifier and its meaning because invariant candidate INV-011 (a second tenant onboards without a core-code fork) depends on it; it is recorded before or together with `BT-G7`, never skipped because the label E does not name it. It moves from closing the previous plan's P3 to being judged at `BT-G7`.

### 10.2 The gate table

Rows `BT-G0` to `BT-G6` are the previous plan's section 7 verbatim; `BT-G7` is new, from the roadmap's Gate E.

| Gate | Requirement | Blocking evidence |
|---|---|---|
| `BT-G0 Architecture Ready` | Domain, tenancy, API, event, workflow, data and financial contracts accepted | ARCH-001, ADR set and review record |
| `BT-G1 Security Ready` | Tenant isolation mechanically proven | P0 negative-test evidence |
| `BT-G2 Broker Core Ready` | Offer → recommendation → acceptance → authority-supported coverage → policy representation passes | P1 trace and domain UAT |
| `BT-G3 Lifecycle Ready` | Placement, endorsement, claim and renewal pass failure scenarios | P2 workflow and recovery evidence |
| `BT-G4 Financial Ready` | Payment, ledger, commission and settlement reconcile | Balanced journals and reconciliation evidence |
| `BT-G5 Integration Ready` | External adapters pass contract, retry and security tests | Provider sandbox and fault-injection evidence |
| `BT-G6 Tenant Ready` | A second independent tenant provisions without a core-code fork | Tenant #2 provisioning and isolation proof |
| `BT-G7 Production Ready` | The whole system is shown to be operable: every item of section 10.3's Gate E list has revision-bound evidence, and `BT-G6` is recorded | The Gate E evidence set, an independent production-readiness review, and the security risk owner's dated record |

In the `BT-G2` and `BT-G3` rows, "P1" and "P2" are the previous plan's phase names; in this plan they are P1A and P1B. The rows are kept verbatim so that the phase pages, which still name these gates as their exit gates, match them. The `BT-G3` row, kept verbatim, names P1B's proof; where P1C's proof sits inside Gate C is the P1 manual ticket's ([#167](https://github.com/bstBizEra/biztrust_guide/issues/167)).

The `BT-G7` row adds to the roadmap's Gate E four things the roadmap does not state, and they are this plan's proposals: revision binding of the evidence (`AGENTS.md` section 9); `BT-G6` recorded (the map's charting decision 3); an independent production-readiness review and the security risk owner's dated record (the hub's Definition of Done, whose last item is an independent review, and the previous plan's section 7 waiver rule, which names a human risk owner).

Failure at any gate blocks dependent authorization. A waiver requires a named human risk owner, expiry, compensating controls and recorded dissent (previous plan, section 7). A gate is recorded by a human; which human is the gate owner's record to name and never inferred (`AGENTS.md` section 4); a passing test suite records nothing.

### 10.3 What each label requires

Restated from the roadmap so that a manual or a showcase page can cite one place; each list is a proposal until the gate's owner accepts it.

**Gate A, `BT-G0`** (roadmap section 3): the architecture can answer who owns each datum; which tenant owns each record; who may perform each operation; which module owns each state transition; what the authoritative insurance state is; what the authoritative financial state is; how a quote becomes bound coverage; how money becomes premium; how commission is calculated and posted; how a carrier integrates; how Tenant #2 onboards without a fork; how cross-tenant isolation is mechanically proved; how failures are recovered; how a transaction is reconstructed from evidence. They correspond to, and are fewer than, the contract's seventeen section 17 exit criteria; the contract's list governs.

**Gate B, `BT-G1`** (roadmap section 4): the chain authenticated identity, validated tenant context, authorised operation, tenant-isolated data access, immutable audit evidence is mechanically demonstrated, and the P0 mandatory proof of the previous plan's section 3 passes independently of the implementer.

**Gate C, `BT-G2` and `BT-G3`** (roadmap section 5): the trace tenant, client, risk, submission, placement, quotes, comparison, recommendation, acceptance, bind coordination, carrier confirmation, policy, then endorsement, claim and renewal, is proven with authorisation, product and version reproducibility, tenant isolation, deterministic state transitions, an audit trail, web and mobile coverage, API contracts, documents, and insurer-authority separation.

**Gate D, `BT-G4` and `BT-G5`** (roadmap section 6): the trace customer, insurance transaction, invoice, payment, provider confirmation, ledger, commission, insurer payable, settlement, reconciliation, policy evidence, is proven, and these failure cases are proven handled: duplicate payment; duplicated callback; provider timeout; missing webhook; eventual confirmation; refund duplication; incorrect currency; ledger mismatch; reconciliation mismatch; carrier settlement difference.

**Gate E, `BT-G7` with `BT-G6`** (roadmap section 7): revision-bound evidence exists for security, tenant isolation, insurance end-to-end, financial reconciliation, data migration, performance, observability, backup restore, disaster recovery, rollback, incident response, release controls, secrets, mobile release, operational documentation, runbooks, on-call and escalation, and compliance evidence; the production-readiness review is executed by someone other than the implementers; the security risk owner records the gate with a date. Three definitions P3 rests on have no primary source and are local decisions the P3 manual must label: the incident severity scale, "rolling deployment", and "rollback" outside the blue-green case (research [#161](https://github.com/bstBizEra/biztrust_guide/issues/161)). Store releases have no rollback at all; the evidence for mobile release is a halted rollout and a shipped fix (research [#162](https://github.com/bstBizEra/biztrust_guide/issues/162)).

## 11. Expansion streams: entry conditions

Each stream of section 8 opens only when `BT-G7` is recorded, Production v1.0 is released, and its own entry condition below is recorded; none is ordered among the others except as its condition names another; none is authorised by this plan. Proposed conditions:

| Stream | Entry condition | Decision it waits on |
|---|---|---|
| E1 Tenant Scale | `BT-G6` recorded, and a third tenant's authority profile under S01 | ADR-011 |
| E2 Embedded Insurance | `BT-G7` recorded, and a partner contract that names the API surface it needs | ADR-005, ADR-009 |
| E3 Integration Scale | A counterparty (insurer, payment provider or bank) with a documented API and a signed sandbox agreement | ADR-009 |
| E4 Workflow Scale | Workflow volume or fault evidence from P1B and P2 showing the P0 runtime choice insufficient | ADR-001's extraction criteria; ADR-010 |
| E5 Enterprise Isolation | A tenant's regulatory or contractual requirement for a dedicated schema or database, recorded by the legal seat | The contract's section 18 dedicated-tenant trigger; ADR-004; ADR-019 |
| E6 Advanced Brokerage | P1B operating data on one tenant covering a full renewal cycle (a measurement window, not a schedule), or a second tenant's need recorded | — |
| E7 Intelligence | The data-governance track's owner, classification and consent rows exist for every dataset a model would read | ADR-019; the compliance track |
| E8 Ecosystem | E2 open and at least one partner live | — |

## 12. Cross-cutting tracks

The roadmap's section 8 names eight tracks that run through every phase. What each requires, per phase, is proposed here so that a Work Package in any phase can be checked against its track; the guide's hub already carries the security track as its section 11 and the operating half of the observability track as its section 12, and this table cites them rather than restating them.

| Track | Architecture | P0 | P1 | P2 | P3 |
|---|---|---|---|---|---|
| Security (roadmap 8A; hub section 11) | Threat model, trust boundaries, data classification in the contract | Zero trust at the boundary; least privilege; secret scanning; SAST in the pipeline; tenant-negative tests | Authorisation matrix per capability; abuse cases per workflow | Payment and ledger threat model; signed webhooks; refund abuse cases | DAST; penetration test; detection rules; vulnerability SLA |
| Compliance (8B; research [#164](https://github.com/bstBizEra/biztrust_guide/issues/164)) | The legal seat's questions recorded, not answered by agents | Consent and audit primitives | KYC and KYB where the legal seat requires; disclosure and advice evidence per recommendation | AML where applicable; client-money regime per ADR-014 | Regulatory reporting; retention; audit trail evidence |
| Data governance (8C) | Ownership matrix (contract section 9) | Tenant ownership of every record; classification field | System of record per aggregate; provenance per product version | Retention and lineage for financial records | Legal hold; deletion; residency evidence per ADR-019 |
| API governance (8D) | Contract-first rule (ADR-005) | Conventions, versioning, idempotency keys, lint | Every capability behind a versioned contract | Provider adapters behind ADR-009's boundary; timeouts, retries, rate limits | Deprecation policy; sandbox; SLA per interface |
| Quality engineering (8E) | Conformance scenarios named | Unit, contract, tenant-isolation and negative tests | Deterministic business-rule tests; end-to-end per slice | Reconciliation and failure-case tests | Performance, resilience, accessibility, mobile, disaster-recovery tests |
| Observability (8F; hub section 12) | Telemetry fields named per invariant | Logs, metrics, traces linked by request (P0.11) | Business events per state transition | Ledger and reconciliation drift signals | Service-level objectives, alerts, dashboards (P3D, P3F) |
| UX surfaces (8G) | `UX-001` in the family ([#158](https://github.com/bstBizEra/biztrust_guide/issues/158)) | Control-plane web (P0.13, [#157](https://github.com/bstBizEra/biztrust_guide/issues/157)) | Broker workstation; mobile identity foundation (P1A.14); customer and agent mobile (P1C.6, P1C.7) | Payment surfaces in each client | Store release pipelines (P3H) |
| Agentic governance (8H; `AGENTS.md`) | Every agent bound by identity, Work Package, authority, permitted tools, evidence, independent review, gate, human authorisation | Same, with implementation authority explicit and expiring | Same | Same, with financial mutations behind approval authority | Same, with release authority human-recorded |

Observability is implemented with each feature, never retrofitted in P3 (roadmap 8F). No track is a phase, and no track's requirement is met by a document alone; each cell names something a Work Package's evidence must show.

## 13. Definition of Done

The guide's hub carries an eight-item Definition of Done for a Work Package: acceptance criteria pass; contracts and docs updated; negative tests included; threat model reviewed; telemetry implemented; rollback validated; evidence manifest signed; independent review complete. The roadmap's section 11 lists seventeen items. They reconcile as follows, and the eight stand as the Work Package Definition of Done, with the roadmap's items as what each of the eight must show:

| Guide item | Roadmap items it carries |
|---|---|
| Acceptance criteria pass | Requirements satisfied; code complete; unit tests; deterministic business-rule tests |
| Contracts and docs updated | Architecture conformant; contract tests; documentation |
| Negative tests included | Tenant isolation validation; integration tests; web and mobile end-to-end where relevant; migration tested |
| Threat model reviewed | Security validation |
| Telemetry implemented | Observability implemented |
| Rollback validated | Rollback strategy |
| Evidence manifest signed | Evidence generated |
| Independent review complete | Independent review |

One roadmap item is not a Work Package item: **gate passed**. Read as `BT-Gn`, a gate closes a phase, not a package (section 10): a package is done when its eight items are shown, and a phase is closed when its gate's owner records it, so putting the gate inside the package's definition would let a package claim a phase. Read as `ENG-Gn`, passing the stage gate is the lifecycle the eight items feed, not a ninth item. On either reading it is not a package item.


## 14. What this document does not yet carry

- **The previous plan's section 7** is a pointer to section 10 here since WP-051 ([#165](https://github.com/bstBizEra/biztrust_guide/issues/165)); the overview renders section 10 and `tests/test_phase_pages.py` reads it. The P0, P1 and P2 pages render sections 4 to 6 here; the P3 page still renders the previous plan's epics and exit gates until its ticket moves it.
- **The Work Package decomposition rule, the recommended backlog and the exit from planning**: the previous plan's sections 8, 9 and 11 stand.
- **Doctrine and contract family**: [#158](https://github.com/bstBizEra/biztrust_guide/issues/158), which waits on the contract map's waiver.
- **Canonical naming** (roadmap section 14): the phase names in section 2 adopt it; its use across issues, Work Packages and pages is the overview ticket's ([#165](https://github.com/bstBizEra/biztrust_guide/issues/165)) and each manual's.
- **The manuals**: [#165](https://github.com/bstBizEra/biztrust_guide/issues/165) to [#170](https://github.com/bstBizEra/biztrust_guide/issues/170); until they move, `phases/` renders the previous plan.

## 15. Sources

- The operator's roadmap draft, sections 1 to 8, 11 to 15, as transcribed at [`../research/roadmap/BIZTRUST-ROADMAP-001-operator-draft.md`](../research/roadmap/BIZTRUST-ROADMAP-001-operator-draft.md).
- [`DELIVERY_PLAN.md`](DELIVERY_PLAN.md) v0.1, sections 1 and 3 to 11; the gate rows its section 7 held until WP-051 are quoted verbatim in section 10.
- The guide's hub, `index.html`, section 10 (the eight-item Definition of Done and the assurance metrics) and sections 11 and 12 (security engineering and production operations), as rendered at the commit this document cites.
- Research on the Guide v2 map: [#161](https://github.com/bstBizEra/biztrust_guide/issues/161) for the definitions the P3 gate rests on, [#162](https://github.com/bstBizEra/biztrust_guide/issues/162) for store release, [#163](https://github.com/bstBizEra/biztrust_guide/issues/163) for reconciliation statuses, [#164](https://github.com/bstBizEra/biztrust_guide/issues/164) for the compliance track.
- [`FOUNDATION_SEQUENCE.md`](FOUNDATION_SEQUENCE.md), [`ADR_REGISTER.md`](ADR_REGISTER.md), [`DOMAIN_MODEL.md`](DOMAIN_MODEL.md) section 1, [`BIZTRUST-ARCH-001.md`](BIZTRUST-ARCH-001.md) sections 5 and 17.
