# BIZTRUST-ARCH-001

## Multi-Tenant Insurance Brokerage Platform Architecture

| Field | Value |
|---|---|
| Version | `0.1-draft` |
| Status | `DRAFT FOR CONTRACT FREEZE` |
| Parent Work Package | [`BIZTRUST-WP-ARCH-001A`](https://github.com/bstBizEra/biztrust_guide/issues/27) |
| Documentation Work Package | `BIZTRUST-GUIDE-WP-003` |
| Implementation authority | `NOT GRANTED BY THIS DOCUMENT` |
| Target review | Architecture, security, insurance domain, data, finance, API/integration and operations |

## 1. Purpose

This document is the proposed parent architecture contract for BizTrust. It establishes vocabulary, ownership, boundaries and testable invariants before production implementation begins.

The platform position is:

> BizTrust is a multi-tenant insurance brokerage, distribution and insurance API platform. It is not an insurer policy-administration or underwriting core.

BizTrust coordinates the broker-side lifecycle: clients, risks, submissions, placement, quotes, recommendations, binding coordination, broker policy records, servicing, claims advocacy, renewals, premium collection, commissions, settlement, reconciliation and partner distribution.

Insurers normally remain authoritative for underwriting decisions, risk acceptance, issued insurance contracts, insurer policy records, claim adjudication, insurer reserves and insurer accounting. A tenant may perform a narrowly scoped authoritative act only when an accepted authority profile and operative agreement prove delegated or master-policy authority; application configuration cannot create that authority.

## 2. Scope boundary

### In scope for the contract

- tenant and identity boundaries;
- business authorization and data isolation;
- brokerage domain ownership;
- intermediary, insurer and delegated contract authority;
- effective-time and record-time semantics;
- co-insurance, layer, facility, master-policy and certificate topology;
- product and rule versioning;
- quote-to-policy workflows;
- broker-versus-insurer systems of record;
- API, event and integration contracts;
- payment, ledger, commission and settlement boundaries;
- client-money, risk-transfer and reconciliation regimes;
- audit, observability, failure handling and delivery gates.

### Out of scope for the contract freeze

- production application code;
- exhaustive physical database design;
- product pricing implementation;
- live insurer, bank or payment-provider integrations;
- final jurisdiction-specific legal or accounting approval;
- microservice decomposition;
- AI insurance-agent behavior;
- proof that any documented control is already implemented.

## 3. Architecture decision hygiene

The architecture pack distinguishes four kinds of content:

1. **Invariant candidates** describe outcomes that must remain true regardless of implementation.
2. **Proposed decisions** select an approach and require an accepted ADR.
3. **Implementation candidates** identify technology to validate through a bounded spike.
4. **Jurisdiction-dependent rules** require qualified human legal, regulatory or accounting review.

Words such as “shall” in this draft mean “proposed for freeze,” not “already accepted or implemented.”

## 4. Strategic architecture

### 4.1 Proposed style

`PROPOSED_DECISION · ADR-001`

Begin with a modular monolith behind explicit module contracts, supported by external infrastructure services. Logical domain boundaries do not automatically become independently deployed services.

A module may be extracted only when evidence demonstrates a need such as independent scaling, fault isolation, regulatory separation, security isolation, team ownership or materially different availability requirements.

### 4.2 Strategic intellectual property

BizTrust should own:

1. the broker insurance domain model;
2. the versioned insurance product model;
3. placement, advice and broker workflow semantics;
4. the premium, commission and settlement subledger model;
5. tenant-pack and insurer/payment/partner interoperability contracts.

Identity, gateway, workflow runtime, messaging, database and observability should remain replaceable infrastructure behind adapters and operational contracts.

## 5. Architecture invariants

These are `INVARIANT_CANDIDATE` until accepted by the architecture authority.

| ID | Candidate invariant | Mechanical proof expected |
|---|---|---|
| INV-001 | Every tenant-owned business record has exactly one tenant owner. | Schema and invariant tests |
| INV-002 | Tenant authority originates from validated identity context, never an untrusted client identifier alone. | Negative token and request tests |
| INV-003 | Tenant A cannot read or mutate Tenant B protected data. | API and database isolation suite |
| INV-004 | Application authorization and PostgreSQL RLS independently enforce isolation. | Bypass-oriented tests |
| INV-005 | Broker records never impersonate insurer-authoritative decisions or contracts. | Ownership and transition tests |
| INV-006 | Historical transactions retain the exact product, wording, pricing and commission-rule versions used. | Reproduction tests |
| INV-007 | Material insurance and financial transitions are attributable and reconstructable. | Audit-chain tests |
| INV-008 | Posted ledger records are immutable; corrections use reversals or compensating entries. | Database and accounting tests |
| INV-009 | Financial and binding mutations safely tolerate retries. | Idempotency and concurrency tests |
| INV-010 | Provider-specific behavior remains behind an adapter boundary. | Dependency and contract tests |
| INV-011 | A second tenant onboards without a tenant-specific core-code fork. | Tenant provisioning acceptance test |
| INV-012 | Public and inter-module interfaces are contract-first and versioned. | Contract lint and compatibility tests |
| INV-013 | Long-running workflows tolerate duplicate messages, delay, restart and partial failure. | Fault-injection tests |
| INV-014 | Sensitive actions require explicit permission and, where configured, approval authority. | Authorization-matrix tests |
| INV-015 | No implementation or compliance claim is accepted without revision-bound evidence. | Evidence-manifest validation |
| INV-016 | Every representation of effective cover identifies the legal authority, effective period and retained evidence that support it. | Authority-profile and coverage-transition tests |
| INV-017 | Valid time and record time remain distinct for coverage-sensitive and financial-effective facts; correction never erases the prior assertion. | Backdated, future-dated and correction scenarios |
| INV-018 | Product, wording, rating, broker indication, insurer quote and delegated offer retain explicit authority and provenance. | Systems-of-record and provenance tests |
| INV-019 | A single risk or contract may be represented across insurer shares, layers or certificates without duplicating or overwriting the risk. | Placement-topology scenario tests |
| INV-020 | Payment state cannot invent coverage state; any premium condition affecting cover is evaluated by the authority-aware insurance workflow. | Cross-context transition and negative tests |
| INV-021 | Client-money and office-money balances, movements and reconciliations remain distinguishable under the approved operating regime. | Funds-flow, balance and reconciliation tests |
| INV-022 | Application permission never substitutes for legal, insurer-delegated or scheme authority. | Authorization-versus-authority negative tests |

## 6. Capability map

The following are logical ownership boundaries to refine during domain workshops. They are not a microservice count.

| Domain group | Candidate modules | Primary responsibility |
|---|---|---|
| Platform | Tenancy, Identity & Access, Distribution, Compliance, Audit | Tenant control plane and evidence |
| Brokerage | Party, Client, Risk, Distribution Product, Submission, Placement, Quote/Indication, Recommendation, Binding, Policy, Claims, Renewal | Broker operating lifecycle and sourced insurance representations |
| Financial | Billing, Payment, Ledger, Commission, Settlement, Reconciliation | Premium and broker financial control |
| Integration | Insurer, Payment Provider, Bank, Partner API, Documents, Notifications | Controlled external interaction |

Whether a candidate module is a bounded context, subdomain or aggregate boundary must be resolved in `BIZTRUST-DOMAIN-001`; the list must not be used to justify premature service extraction.

## 7. Tenancy contract

`PROPOSED_DECISION · ADR-003 and ADR-004`

A BizTrust tenant is both a business operating context and a security/data boundary. A branch is not automatically a tenant. A separately licensed broker, delegated agency or partner that requires independent data authority normally is.

The minimum business hierarchy is:

```text
BizTrust Platform
└── Tenant
    ├── Legal Entity
    ├── Business Unit / Branch
    ├── Team
    ├── Distribution Channel
    └── User or Service Principal
```

Tenant isolation applies to business data, business authorization, product entitlements, insurer relationships, commissions, settlements, integration configuration, branding, reporting and audit evidence.

The default SaaS isolation proposal is shared PostgreSQL with a mandatory `tenant_id` and Row-Level Security. Dedicated schema or database tiers may be offered later without changing domain semantics.

## 8. Identity and authorization contract

`PROPOSED_DECISION · ADR-002 and ADR-003`

Logto is the proposed identity infrastructure. Its organization context maps to the BizTrust tenant security context, while BizTrust remains authoritative for insurance-specific business structure and authority.

Logto owns authentication, credentials, SSO, MFA, OIDC/OAuth, organization identity context and machine identity. BizTrust owns legal entities, branches, teams, insurer relationships, product/channel entitlements, financial limits and insurance-domain decisions.

Each protected API request must verify at least:

- token signature, issuer and expiry;
- API audience;
- `organization_id` for organization-level API resources;
- required scopes;
- active BizTrust tenant and membership;
- resource scope and business authority;
- approval authority for controlled actions;
- database RLS outcome.

This access-control decision is necessary but not sufficient for authoritative insurance acts. A BizTrust permission such as `binding:confirm` only allows an actor to invoke the command. The command may represent cover as effective only when an accepted `AuthorityAgreement` or insurer evidence permits that actor/source to do so for the product, territory, limit and effective period. `ADR-013` owns this distinction.

An organization or tenant identifier in a URL, header, query string or request body is requested context only. It must match the authenticated and authorized context.

## 9. Data ownership

Every authoritative datum has one owner. Other modules consume contracts or maintain clearly labeled representations.

| Information | Authoritative owner | Important distinction |
|---|---|---|
| User identity and credentials | Logto | BizTrust owns business authority |
| Tenant business configuration | BizTrust Tenancy | Separate from identity organization metadata |
| Party and client relationship | BizTrust Party / Client | Avoid duplicate client masters |
| Risk information | BizTrust Risk | Version or snapshot when submitted |
| Insurer product, approved wording and insurer-owned rating | Insurer | BizTrust retains a sourced, immutable representation and provenance |
| Broker distribution configuration | BizTrust Distribution Product | References insurer product/wording; cannot silently become insurer authority |
| Broker submission | BizTrust Submission | Records the requested cover |
| Market placement | BizTrust Placement | Owns insurer engagement |
| Broker-calculated price indication | BizTrust Indication | Must be labeled as non-binding unless an accepted authority profile says otherwise |
| Carrier quote or delegated offer | Insurer or documented authority holder | BizTrust retains source, authority agreement, revision and validity |
| Broker recommendation | BizTrust Recommendation | Distinct from insurer quote |
| Bind coordination | BizTrust Binding | Request, referral, delegated act and confirmation are distinct |
| Effective-cover evidence | Insurer or documented delegated authority holder | Authority varies by accepted tenant/arrangement profile |
| Issued insurance contract / master policy | Insurer | Insurer-authoritative unless governing law/agreement records a narrower exception |
| Certificate under master policy | Authority defined by master-policy arrangement | BizTrust may issue only within recorded authority and reporting obligations |
| Broker policy representation | BizTrust Policy | Must reference authoritative coverage/contract evidence and its source authority |
| Broker claim advocacy record | BizTrust Claims | Separate from adjudication |
| Claim adjudication | Insurer | Never overwritten by broker workflow state |
| Payment orchestration | BizTrust Payment | External transaction remains PSP/bank-owned |
| External payment transaction | PSP or bank | Provider reference retained |
| Legal/risk ownership of in-transit premium or refund | Governing law and operative agreement | Must be resolved per tenant; BizTrust records the accepted conclusion |
| Bank account and bank transaction | Bank | Client/office classification and reconciliation retained by BizTrust |
| Broker client-money and office-money subledgers | BizTrust Ledger | Separated according to accepted regime; posted journals are immutable |
| Commission calculation | BizTrust Commission | Rule version and basis retained |
| Insurer statement/account-current | Insurer or agreed counterparty | BizTrust stores sourced representation and reconciliation result |
| Settlement, bordereau and reconciliation | BizTrust Settlement / Reconciliation | Linked to ledger, placement/certificate population and external evidence |
| Audit evidence | BizTrust Audit | Protected from ordinary mutation |

Cross-module direct table mutation is prohibited. The owning module changes its state through a command and publishes resulting facts through contracts.

## 10. Product architecture

`PROPOSED_DECISION · ADR-006`

BizTrust distributes insurance through versioned configuration rather than product-specific application forks. The configuration is not automatically the authoritative insurance product: it must identify whether each product, wording, rule and price is insurer-authored, broker-authored for distribution only, or executed under documented delegated authority.

```text
InsurerProductReference
└── DistributionProductVersion
    ├── Authority and provenance
    ├── Risk and question schemas
    ├── Eligibility and underwriting rules
    ├── Coverage definitions
    ├── Pricing adapter/configuration
    ├── Wording and document templates
    ├── Payment rules
    ├── Commission-rule version
    ├── Workflow definition
    ├── Insurer adapter mapping
    └── Channel configuration
```

An indication, insurer quote/delegated offer, recommendation, policy, endorsement and commission calculation must retain the relevant version and authority identifiers. Publishing a new distribution version cannot silently alter historical transactions or claim to change insurer wording or rating without source authority.

Tenant customization should be represented as signed, validated Tenant Packs containing configuration, products, workflows, documents, permissions, localization, branding, integration references and feature flags. Tenant Packs cannot execute unrestricted code inside the domain core.

## 11. API and event contract baseline

`PROPOSED_DECISION · ADR-005`

| Concern | Proposed baseline |
|---|---|
| HTTP description | OpenAPI 3.2.0 |
| Event description | AsyncAPI 3.1.0 |
| Event envelope | CloudEvents profile to be frozen |
| Error format | RFC 9457 `application/problem+json` |
| Trace propagation | W3C `traceparent` |
| Identifiers | UUIDv7 where ordered identifiers are beneficial |
| Dates | ISO `YYYY-MM-DD` |
| Timestamps | RFC 3339 UTC |
| Money | Decimal string plus ISO currency code |

Canonical HTTP rules:

```text
Base URI            /api/v1
Authentication      Authorization: Bearer <organization-scoped-token>
Request identity    X-Request-ID
Trace context       traceparent
Mutation replay     Idempotency-Key
Optimistic locking  ETag + If-Match
Success content     application/json
Error content       application/problem+json
```

Target contract families:

```text
openapi/
├── biztrust-insurance-api.yaml
├── biztrust-payment-api.yaml
├── biztrust-partner-api.yaml
├── biztrust-admin-api.yaml
└── components/
    ├── common.yaml
    ├── errors.yaml
    ├── money.yaml
    ├── pagination.yaml
    └── insurance.yaml
```

Representative resources include parties, clients, risks, products, product versions, submissions, placements, market requests, quotes, recommendations, bind orders, policies, endorsements, renewals, claims, documents, invoices, payment intents, payments, refunds, journals, commissions, settlements and reconciliations.

## 12. Event and workflow contract

Domain events describe completed business facts. A command request is not an event and an event does not grant authority to another module to bypass its own transition rules.

Minimum event metadata:

```text
event_id
event_type
event_version
occurred_at
effective_at_or_period when the business fact has valid-time effect
recorded_at
tenant_id
subject_type
subject_id
correlation_id
causation_id
traceparent
producer
authority_reference when the fact asserts delegated or external authority
data
```

External delivery is at-least-once unless a provider contract proves otherwise. Consumers must deduplicate by stable event identity and retain processing outcomes.

Durable workflow and messaging technologies are `IMPLEMENTATION_CANDIDATE`. Temporal and NATS JetStream are proposed for spikes; their adoption is not frozen merely because they appear in diagrams.

## 13. Financial boundary

`PROPOSED_DECISION · ADR-008 and ADR-012`

Operational payment state and accounting state are separate. A successful provider payment does not itself activate insurance coverage, and a journal posting does not replace the payment-provider transaction record.

Before the chart of accounts is frozen, each tenant/arrangement must have an accepted money-regime profile stating whether the intermediary handles client money, when premium is legally treated as received by the insurer, who bears transit/insolvency risk, which accounts are segregated, and when commission may be withdrawn. `ADR-014` owns that decision; a generic premium journal is not evidence.

The ledger is double-entry and append-oriented. Posted records are never edited destructively; corrections use reversal, compensating journal or an explicitly linked adjustment. It must distinguish at least:

- external bank and PSP transaction facts;
- client-money versus office-money custody classification;
- receipts and allocations by client, invoice, policy/contract and insurer;
- insurer payable/receivable and statement/account-current representation;
- commission earned, accrued, received, paid and clawed back;
- refunds, chargebacks, reversals and unexplained differences; and
- bank-to-ledger, ledger-to-insurer-statement and earned-to-received commission reconciliation.

Candidate invariants include balanced journals, allocations that do not exceed cleared funds, no hidden offset between client and office money, and no completion of a settlement while required differences remain unowned. Exact constraints depend on the accepted regime.

Historical commission calculations retain:

- agreement and rule version;
- calculation basis and applicable rate/rule;
- gross and net premium;
- tax and fee components;
- commission amount and beneficiary;
- effective date and calculation time;
- source transaction and policy references.

`JURISDICTION_DEPENDENT`: premium trust/client-money treatment, risk transfer, tax, revenue recognition, remittance, refund and commission accounting must be approved for each tenant arrangement and operating market. Examples in this guide are conceptual and are not accounting advice.

## 14. Integration boundary

`PROPOSED_DECISION · ADR-009`

Insurers, payment providers, banks, document services, notification providers and partners integrate through controlled adapters. Each adapter maps provider concepts to the BizTrust canonical model and owns protocol-specific retries, signatures, timeouts, rate limits and error translation.

Provider payloads and status values do not become core-domain schemas. Source payloads may be retained as immutable evidence subject to security, privacy and retention policy.

ACORD compatibility should be implemented as a mapping layer where commercially useful. ACORD is not the BizTrust database model.

## 15. Audit and observability

Every material action must be reconstructable from evidence that includes, where applicable:

- tenant and legal entity;
- actor or service principal;
- operation and resource;
- previous and resulting business state;
- timestamp, request ID and trace ID;
- authorization decision and authority reference;
- workflow, correlation and causation IDs;
- source system and external reference;
- approved source revision and contract version.

Logs and traces must not expose secrets, raw credentials, unnecessary personal data or cross-tenant information. Audit records require separate retention, access and mutation controls.

## 16. Required ADRs

| ADR | Proposed decision |
|---|---|
| ADR-001 | Modular Monolith First |
| ADR-002 | Logto as Identity Infrastructure |
| ADR-003 | Logto Organization as Tenant Security Context |
| ADR-004 | PostgreSQL and RLS Tenant Isolation |
| ADR-005 | OpenAPI 3.2 Contract-First HTTP APIs |
| ADR-006 | Versioned Insurance Product Configuration |
| ADR-007 | Broker versus Insurer Systems of Record |
| ADR-008 | Immutable Double-Entry Insurance Ledger |
| ADR-009 | External Adapter Architecture |
| ADR-010 | Durable Workflow Architecture |
| ADR-011 | Tenant Packs instead of Tenant Forks |
| ADR-012 | Idempotency for Financial and Binding Operations |
| ADR-013 | Binding, Delegated Authority and Authoritative Cover Evidence |
| ADR-014 | Client Money, Risk Transfer, Segregation and Funds Control |
| ADR-015 | Effective Time, Record Time, Correction and Supersession |
| ADR-016 | Co-insurance, Layers, Facilities, Master Policies, Certificates and Bordereaux |
| ADR-017 | Product, Wording, Rating, Indication and Quote Authority |
| ADR-018 | Premium Conditions, Non-payment and Coverage-State Coupling |
| ADR-019 | Jurisdiction, Data Residency, Retention, Localization and Legal Hold |
| ADR-020 | Endorsement, Cancellation, Refund, Commission Clawback and Renewal Transactions |

Each ADR must state context, decision, alternatives, consequences, risks, implementation implications and validation requirements. Tool adoption requires operational, security, licensing and exit-strategy review.

## 17. Contract-freeze exit criteria

`BIZTRUST-ARCH-001 v0.1` may be marked accepted only when reviewers can answer without relying on undocumented behavior:

- Who owns every major data class?
- Which tenant owns every protected business record?
- What establishes tenant authority?
- Who may perform each sensitive operation, over which scope and with whose approval?
- Which module owns each state transition?
- What is broker-authoritative and what remains insurer-authoritative?
- Under each tenant arrangement, who may legally conclude cover and within what scope?
- How does a submission become authority-supported effective cover and then an issued policy representation?
- How are effective time, record time, backdating, future dating, correction and supersession represented?
- How are insurer shares, layers, facilities, master policies, certificates and bordereaux represented?
- How are insurer product/wording/rating, broker distribution configuration, broker indication and insurer quote distinguished?
- How does a payment become an allocated premium without bypassing insurance authority?
- Whose money is held at each point, which account class contains it, and which reconciliation proves it?
- How are ledger, commission and settlement results reproduced historically?
- How do external integrations fail without corrupting state?
- How does Tenant #2 onboard without a core-code fork?
- How is every material transaction reconstructed from evidence?

Critical findings must be closed or explicitly accepted by the correct human risk owner. Test success does not self-approve the architecture.

## 18. Unresolved questions

The contract freeze must explicitly resolve:

- initial operating jurisdiction and licensing model;
- contract-conclusion, delegated-authority and master-policy/certificate authority per tenant;
- legal-entity versus tenant boundaries;
- data residency, retention and deletion requirements;
- money precision, day count, rounding, tax, risk-transfer and client-money rules;
- authority and evidence required before coverage is shown as active;
- co-insurance, layers, facilities, bordereaux and account-current obligations;
- product, wording, rating, indication, quote and publication authority;
- endorsement/MTA, cancellation, refund, commission clawback and renewal semantics;
- claims-data sensitivity and document retention;
- partner API trust tiers and mTLS/signature requirements;
- target SLO, RTO and RPO by critical user journey;
- dedicated-tenant triggers and cost model;
- ACORD licensing and exact compatibility scope;
- build-versus-adopt spike criteria for workflow, messaging and fine-grained authorization.

Issue #15 and [`FOUNDATION_SEQUENCE.md`](FOUNDATION_SEQUENCE.md) define the dependency order. Questions that change legal authority, money ownership or stored-data shape cannot be waived by an implementation team.

## 19. Primary references

- [OpenAPI Specification 3.2.0](https://spec.openapis.org/oas/latest.html)
- [AsyncAPI Specification 3.1.0](https://www.asyncapi.com/docs/reference/specification/latest)
- [RFC 9457 — Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)
- [RFC 9562 — UUIDs, including UUIDv7](https://www.rfc-editor.org/rfc/rfc9562.html)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- [CloudEvents specification](https://github.com/cloudevents/spec)
- [Logto organization-level API resources](https://docs.logto.io/authorization/organization-level-api-resources)
- [PostgreSQL Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [IAIS Insurance Core Principles and ComFrame](https://www.iaisweb.org/icp-online-tool/)
- [NIST SP 800-207 — Zero Trust Architecture](https://csrc.nist.gov/pubs/sp/800/207/final)
- [OWASP API Security Top 10 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
