# BizTrust Architecture Foundation Research Ledger

| Field | Value |
|---|---|
| Research date | `2026-09-03` |
| Repository baseline reviewed | `b1a3fa455b758cc6e27404e9b84ee1dce3acf385` |
| Architecture documentation branch | `feat/biztrust-guide-wp-003-architecture-flows` |
| Architecture Work Package | [Issue #27](https://github.com/bstBizEra/biztrust_guide/issues/27) |
| Primary project finding | [Issue #15](https://github.com/bstBizEra/biztrust_guide/issues/15) |
| Research status | `COMPLETE FOR SEQUENCING; BUSINESS AND LEGAL INPUTS STILL REQUIRED` |
| Implementation authority | `NOT GRANTED` |

This is the canonical research ledger for the initial architecture-foundation sequence. It records what the available evidence supports, what it does not support, and which questions must be answered by a qualified human before `BIZTRUST-ARCH-001` can be frozen.

## 1. Research question

What is the safest, dependency-ordered way to complete the BizTrust architecture foundation without allowing agents to:

- encode an unverified insurance operating model into the data schema;
- mistake a broker instruction for legally effective cover;
- design a ledger before determining whose money is being held;
- make one status or timestamp carry several independent meanings;
- open many architecture issues whose assumptions conflict; or
- lose decisions, evidence, authority and recovery state between sessions?

## 2. Scope and assumptions

### In scope

- architecture sequencing and issue-control design;
- insurance intermediary authority and client-money implications;
- high-cost storage-shape gaps identified in issue #15;
- tenancy, authorization, API, event, workflow and observability foundation sources;
- explicit decisions, evidence and human-review gates needed before P0 implementation.

### Out of scope

- legal advice or a conclusion about Lao PDR law;
- interpretation of private licences, insurer agreements or government-program contracts that were not supplied;
- acceptance of an ADR or `BIZTRUST-ARCH-001`;
- selection of production vendors merely because their documentation was researched;
- production application or infrastructure work.

### Working assumptions

1. BizTrust is intended to serve at least two materially different tenant contexts.
2. One context may involve a master policy, certificates, or delegated authority; this is not yet proved.
3. The current repository is a temporary documentation and coordination home, not automatically the permanent architecture system of record.
4. Sensitive licences and agreements must not be copied into this public repository. The public record should contain redacted decision facts, document identifiers and digests.

## 3. Executive answer

Architecture cannot safely start with technology selection or a physical schema. The first controlled slice must establish, per tenant and product arrangement:

1. which legal entity acts;
2. what insurance activity it is licensed or contracted to perform;
3. whether it can conclude insurance contracts or only request insurer confirmation;
4. who owns product, wording, rating and quote authority;
5. who bears the risk while premium or refund money is in transit;
6. which client-money, bank-account, remittance and reconciliation rules apply;
7. which jurisdictions, residency, retention and disclosure requirements apply; and
8. which source documents and qualified reviewers establish those facts.

Only after that evidence pack is accepted should the team freeze coverage states, effective dating, placement topology, product provenance, the ledger, tenancy and integration contracts. The ordered sequence in [`FOUNDATION_SEQUENCE.md`](../../architecture/FOUNDATION_SEQUENCE.md) follows those dependencies.

## 4. Gap matrix

| Gap | Severity | Why it blocks foundation | Required disposition |
|---|---|---|---|
| Binding/delegated authority is unknown per tenant | Critical | Determines who can create an authoritative coverage confirmation and which evidence is legally effective | Written, tenant-specific answer from the business principal and qualified insurance-domain reviewer |
| Client-money/risk-transfer regime is unknown | Critical | Changes bank-account controls, chart of accounts, posting rules, refund behavior, commission withdrawal and reconciliation | Qualified legal/accounting determination linked to governing agreements and jurisdiction |
| Effective time and record time are not modeled separately | Critical | A later-recorded backdated or future-dated transaction cannot be represented accurately with one timestamp | Temporal semantics ADR and examples for bind, endorsement, cancellation and renewal |
| Co-insurance, layers and facilities/master policies are absent | Critical | A single insurer or policy key causes an expensive retrofit when a risk is split by share, layer or certificate | Contract-topology ADR and conceptual model before physical schema |
| Product, wording, rating, indication and insurer quote authority are conflated | Critical | A broker distribution configuration can be mistaken for an insurer product or offer | Systems-of-record decision and provenance model |
| Payment-to-cover coupling is underspecified | High | Premium warranties or non-payment can affect cover, but a payment callback must not unilaterally change it | Cross-context invariant and authority-aware workflow contract |
| MTA, cancellation and renewal economics are shallow | High | Commission earning, clawback, refund basis, day count and version selection affect stored history | Servicing and finance decision pack |
| Lao PDR jurisdiction profile is unverified | High | Licensing, data location, client money, currency, retention and reporting cannot be inferred from global guidance | Review current Lao-language law and operative licences with qualified local counsel |
| Domain-conformance review is not mechanically gated | High | Structural validation cannot prove that a coverage or money state is semantically true | Named practitioner reviewer plus scenario-based conformance evidence |
| Technical candidates can appear more final than they are | Medium | Vendor documentation proves capability, not fit, operations or exit cost | Bounded spikes and ADRs; keep vendor choices `IMPLEMENTATION_CANDIDATE` |
| Architecture work can fan out into contradictory issues | High | Parallel design based on different authority/money assumptions creates rework and hidden conflicts | One active architecture slice, native issue dependencies, one recorded next action |

## 5. Evidence synthesis

### 5.1 Insurance authority comes before cover-state design

The International Association of Insurance Supervisors (IAIS) Insurance Core Principles treat an intermediary's relationship to insurers—and specifically whether the intermediary is authorized to conclude insurance contracts—as information important enough to disclose to customers. This supports issue #15's conclusion that BizTrust cannot adopt one universal `insurer confirms` state machine until each tenant's authority arrangement is known.

Architecture consequence: represent the **authority source** and **confirmation evidence** explicitly. An insurer may be the authority holder in one arrangement; a broker or scheme operator may act under a narrowly scoped delegated agreement in another. Application roles alone cannot create legal authority.

### 5.2 Client money is a first-order architecture input

IAIS ICP 18 separates client-money handling from ordinary intermediary finance. It identifies jurisdiction-specific risk transfer, separate client accounts, authorized payments, auditable books and records, regular reconciliation, discrepancy handling and non-negative per-client balances as possible safeguards. Therefore the ledger cannot be frozen from a generic premium example.

Architecture consequence: record the applicable money regime before selecting a chart of accounts. Separate external bank/PSP facts, custody/risk ownership, client-money subledger, office-money subledger, insurer statements, allocations, commission entitlements and settlements. The exact legal/accounting treatment remains jurisdiction-dependent.

### 5.3 Local evidence and experienced review are required

The IAIS framework says implementation varies by domestic context and that assessment requires qualified people with relevant professional knowledge and practical experience. The Lao PDR Official Gazette and Lao Services Portal expose official legal sources, but the relevant current law and subordinate instruments were not reliably available here in an authoritative English form. Search results and third-party summaries are not sufficient to freeze a legal model.

Architecture consequence: the first slice ends with a signed or otherwise attributable input pack from a UniTrust principal, an experienced placing broker, qualified Lao legal/compliance review and financial/accounting review. Unknowns remain explicit blockers rather than agent assumptions.

### 5.4 Tenancy requires layered, resource-level enforcement

NIST SP 800-207 rejects implicit trust based on network location and focuses protection on resources. OWASP API Security Top 10 identifies broken object-level authorization as a primary API risk. Logto's organization-level API flow supplies audience, organization context and scopes that the API must validate. PostgreSQL Row-Level Security can provide a separate database barrier and defaults to denial when RLS is enabled without a matching policy.

Architecture consequence: retain the proposed `identity token → tenant context → business authorization → RLS → audit` proof, but do not confuse it with insurance authority. The security system answers whether an actor may execute a command; the insurance authority record answers whether that command can create a legally authoritative business fact.

### 5.5 Interface standards are suitable baselines, not business decisions

OpenAPI 3.2.0 is the current published OpenAPI Specification and AsyncAPI 3.1.0 is the current published AsyncAPI specification as of the research date. RFC 9457 defines HTTP Problem Details, RFC 9562 defines UUIDv7, W3C Trace Context defines distributed trace propagation, and CloudEvents defines a common event envelope model.

Architecture consequence: these are reasonable contract baselines, but they cannot resolve domain semantics. A perfectly valid API schema can still label an indication as a quote or a bind request as confirmed cover. Domain ownership, provenance and transition preconditions must be frozen first.

### 5.6 Durable execution still requires idempotent business effects

Temporal's official documentation warns that Activities may be retried and should be idempotent. OpenTelemetry context propagation can correlate traces, metrics and logs across process boundaries. Apache APISIX documents OIDC and mTLS capabilities. These support the candidate platform shape, but none proves production suitability for BizTrust.

Architecture consequence: keep Temporal, NATS JetStream, APISIX, OpenTelemetry and fine-grained authorization engines behind bounded evaluation ADRs. Selection requires compatibility, failure, upgrade, cost, security, licensing and exit-strategy evidence.

### 5.7 GitHub can encode the ordered work graph

GitHub supports sub-issues and explicit blocked-by/blocking relationships. These relationships are visible in issues and projects. This is preferable to relying on issue numbers, free-text checklists or conversation memory.

Architecture consequence: use one contract-freeze parent issue, model each decision slice as a sub-issue only when it is ready to start, and mark native dependencies. At most one architecture slice carries `state:in-progress`; later slices stay in the sequence document until their prerequisites pass.

## 6. Decision recommendations

The following recommendations are evidence-backed but remain proposals until accepted through their ADRs:

1. Start `BIZTRUST-WP-ARCH-001A` with authority, jurisdiction and money-regime discovery.
2. Keep issue #15 open as the blocking finding until the first slice's evidence is accepted.
3. Add ADR topics for binding/delegated authority, client money, effective dating, contract topology, product/rating authority, payment-cover coupling, jurisdiction/data residency and servicing transactions.
4. Generalize `BindConfirmed` to an authority-aware `CoverageConfirmed` fact that records the authority agreement, source actor/system, effective period and evidence reference. Do not decide which actor can produce it until the tenant profile is approved.
5. Model insurer product/wording/rating, broker distribution configuration, broker indication and insurer quote as distinct concepts with provenance.
6. Make temporal semantics explicit for every coverage-sensitive and financial-effective fact.
7. Add scenario-based domain conformance review by a practitioner who has placed insurance; structural tests are necessary but insufficient.
8. Open architecture issues only as the previous gate closes. Do not activate the P0 security slice until `BT-G0` passes.

## 7. Limitations and unresolved evidence

- No private binding-authority, cover-holder, master-policy, insurer-agency, bank, client-money or government-program agreement was supplied.
- No authoritative English consolidation of current Lao PDR insurance law and subordinate rules was verified. The Lao-language official source must be reviewed by qualified counsel.
- No chart of accounts, bank-account structure, insurer statement, bordereau or commission agreement was supplied.
- No target hosting jurisdiction, data classification, RTO/RPO or service-level objective was authorized.
- ACORD public pages establish that insurance data/reference standards exist, but detailed member materials and licensing conditions were not available for review. Compatibility scope remains an ADR input.
- Product vendors were researched only for capability boundaries. No production selection is supported by this report.

## 8. Claim-to-source ledger

| Claim used in the architecture sequence | Source | Source class | Strength / limitation |
|---|---|---|---|
| Intermediary authority to conclude insurance contracts must be made explicit | [IAIS ICP and ComFrame, ICP 18.5](https://www.iaisweb.org/icp-online-tool/) | Primary global supervisory standard | Strong for the need to distinguish authority; local implementation still varies |
| Client-money treatment can depend on who bears risk while funds pass through an intermediary | [IAIS ICP and ComFrame, ICP 18.6](https://www.iaisweb.org/icp-online-tool/) | Primary global supervisory standard | Strong architecture input; not a Lao legal conclusion |
| Client-money safeguards may include separate accounts, authorization, records and reconciliation | [IAIS ICP and ComFrame, ICP 18.6](https://www.iaisweb.org/icp-online-tool/) | Primary global supervisory standard | Strong control taxonomy; exact local requirements require counsel |
| Local context and practical insurance experience are necessary for credible assessment | [IAIS ICP introduction and assessment methodology](https://www.iaisweb.org/icp-online-tool/) | Primary global supervisory standard | Strong support for qualified human review |
| Current Lao legal material must be checked from official sources | [Lao PDR Official Gazette](https://laoofficialgazette.gov.la/) and [Lao Services Portal](https://lsp.moic.gov.la/) | Primary government portals | Authoritative portals; relevant documents were not reliably available in authoritative English |
| Zero trust focuses on resources and does not grant implicit trust by location | [NIST SP 800-207](https://csrc.nist.gov/pubs/sp/800/207/final) | Primary public-sector security standard | Strong security architecture principle |
| Organization-level API tokens carry organization context that APIs must validate | [Logto organization-level API resources](https://docs.logto.io/authorization/organization-level-api-resources) | Official product documentation | Strong for capability; adoption remains an ADR |
| RLS can independently deny unmatched row access | [PostgreSQL Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) | Official product documentation | Strong database behavior; owner/BYPASSRLS design still required |
| Object identifiers require object-level authorization checks | [OWASP API Security Top 10 2023](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/) | Primary OWASP project | Strong threat-class evidence |
| OpenAPI 3.2.0 is the current published OAS baseline | [OpenAPI Specification](https://spec.openapis.org/oas/latest.html) | Primary specification | Strong as of research date; tool compatibility still needs a spike |
| AsyncAPI 3.1.0 is the current published AsyncAPI baseline | [AsyncAPI Specification](https://www.asyncapi.com/docs/reference/specification/latest) | Primary specification | Strong as of research date |
| HTTP errors, identifiers and trace context have stable standards | [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html), [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562.html), [W3C Trace Context](https://www.w3.org/TR/trace-context/) | Primary standards | Strong for wire-format baseline |
| Retried workflow activities must be idempotent | [Temporal Activity definition](https://docs.temporal.io/activity-definition) | Official product documentation | Strong capability constraint; does not select Temporal |
| Distributed telemetry can be correlated through propagated context | [OpenTelemetry context propagation](https://opentelemetry.io/docs/concepts/context-propagation/) | Primary project documentation | Strong observability principle |
| Issue hierarchy and native dependencies can encode the work graph | [GitHub sub-issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-sub-issues) and [issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies) | Official product documentation | Strong for GitHub control-plane design |

## 9. Research conclusion

The architecture foundation is designable, but it is not yet freezable. The next responsible action is not another technology diagram. It is to obtain and approve the tenant authority, jurisdiction and money-regime input contract described by the first slice in `BIZTRUST-WP-ARCH-001A`. All downstream design remains blocked where it depends on those answers.
