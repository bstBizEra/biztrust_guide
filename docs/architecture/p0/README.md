# P0 Design Pack

| Field | Value |
|---|---|
| Version | `0.1-draft` |
| Status | `TEMPLATE AND RULES — NO DESIGN ACCEPTED BY THIS FILE` |
| Map | [P0 design map, issue #128](https://github.com/bstBizEra/biztrust_guide/issues/128) |
| Parent | [`DELIVERY_PLAN.md`](../DELIVERY_PLAN.md) section 3, and the [P0 manual](../../phases/p0.html) |
| Decided under | [#130](https://github.com/bstBizEra/biztrust_guide/issues/130), Work Package `BIZTRUST-GUIDE-WP-046` |

This directory holds one engineering design per P0 epic, P0.2 to P0.12, plus the independent security proof. A design says what will be built, how it will be proven, and what it depends on. It does not build anything: P0 implementation waits for `BT-G0` and a Work Package with explicit, expiring authority in a platform repository, which this repository cannot grant (`AGENTS.md` sections 1 and 12).

P0.1 has no design here. It is the architecture contract and ADR-001 to ADR-020, charted on the [ARCH-001A map](https://github.com/bstBizEra/biztrust_guide/issues/91).

## 1. What a design is for

The [P0 manual](../../phases/p0.html#epics) gives each epic a deliverable, a landing place, a proof and what it is built against. That is enough to plan a Work Package and not enough to review one. A design closes the gap: a reviewer reading it can say which interface a change touches, which negative control must be seen failing, which evidence fields the proof must record, and which decision the design is waiting on. A design that cannot answer those four questions is a description, and the status block below says so.

## 2. File naming and layout

```text
docs/architecture/p0/
├── README.md                           ← this file
├── P0.02-repository-and-boundaries.md
├── P0.03-token-validation.md
├── P0.04-tenant-mapping.md
├── P0.05-tenant-provisioning.md
├── P0.06-tenancy-data-model.md
├── P0.07-rls-enforcement.md
├── P0.08-api-conventions.md
├── P0.09-event-conventions.md
├── P0.10-audit-framework.md
├── P0.11-observability-baseline.md
├── P0.12-secrets-and-configuration.md
└── P0.SECURITY-PROOF.md                ← the BT-G1 test matrix, verifier and evidence binding
```

- `P0.NN-<slug>.md`: two-digit epic number, then a slug of at most four words. The number is the epic's number in `DELIVERY_PLAN.md` section 3; the slug may differ from the manual's row title but the number may not.
- Exception: the independent security proof, ticket [#148](https://github.com/bstBizEra/biztrust_guide/issues/148), is `P0.SECURITY-PROOF.md`. It is not an epic; it is the `BT-G1` matrix that the epics' negative controls feed.
- One design per epic. An epic that needs two documents is an epic that should be two Work Packages; say so in the design's open questions rather than splitting the file.
- The manual links each epic row to its design once the design exists. A design links back to the manual's `#epics` anchor, to every ADR it depends on by register number, and to every research file it cites by branch and path.

## 3. Status vocabulary

```text
DRAFT        the file exists; sections may be empty
PROPOSED     every mandatory section is filled and every dependency is named
IN_REVIEW    a fresh-context review is recorded on the ticket
ACCEPTED     the architecture authority has recorded acceptance after BT-G0 and after every ADR the design depends on is ACCEPTED
REJECTED     a review turned the design down; the ticket records why, and a replacement starts at DRAFT
SUPERSEDED   replaced by a later design, which is linked
```

The vocabulary is a subset of the ADR register's, with the same acceptance rule. A `DRAFT` lives on its branch; a design lands on `main` only at `PROPOSED`.

No agent marks a design `ACCEPTED`. A design cannot be `ACCEPTED` while any ADR it names is not, and cannot be `ACCEPTED` before `BT-G0`. A `PROPOSED` design is a proposal to review, nothing more; the manual's status language for P0 does not change because a design exists.

## 4. Mandatory sections

Every design has these sections, in this order, with these headings. A missing or empty mandatory section keeps the design at `DRAFT`.

### 4.1 Status block

A table at the top: version, status (from section 3), epic number and manual row, map ticket, Work Package that landed it, the ADRs it depends on with each one's register status, and the research files it cites.

### 4.2 Scope and non-scope

What this epic builds and what it deliberately does not. Non-scope names the epic or phase that owns each excluded item, so a gap reads as a decision and not an omission (the Architect stage's rule, [`stages/architect.html#freeze`](../../stages/architect.html#freeze): deferral is an output, not an omission).

### 4.3 Authorization-sequence step

Which step of the tenant authorization sequence ([`FLOWS.md`](../FLOWS.md) section 3, the manual's "security chain"; the map's tickets call it the security spine) this epic implements or supports: user or service, organization token, gateway candidate, API boundary, organization-to-tenant resolver, business authorization, row-level security, audit and observability, or the allow-or-deny with evidence. An epic outside the sequence (repository boundaries, secrets) says which steps it protects.

### 4.4 Interfaces and data shapes

What the epic exposes and what it consumes: commands, queries, events, tables, configuration, environment. Each interface names its owner module, its authority (who may call it and under which validated context), and its provenance fields. Data shapes carry `tenant_id` where the tenancy contract requires it and both valid time (the flows' effective time) and record time where ADR-015 requires it. Shapes are stated in prose and tables, or as fenced pseudo-schema; not as code that could be mistaken for an implementation.

### 4.5 Negative controls

A negative control is a test observed failing before the protection exists and passing after. Each control is one row: the threat or defect it detects, the exact condition, the expected denial or failure, and the step at which it must be seen failing. A design with no negative control has no proof; the manual's rule is negative tests first.

### 4.6 Evidence contract

What the proof of this epic records, per `AGENTS.md` section 9, as a table: repository and commit SHA; command or workflow identity; execution time and environment (runtime versions, database version, tool versions); exit status; the artifact or output reference; the verifier role, who is not the implementer for any control on the `BT-G1` matrix; declared coverage; declared non-coverage. A proof missing any field is not evidence.

### 4.7 Technology candidates

A table: candidate, what it is a candidate for, the ADR that decides it with its register status, the research file that informs it, and the exit path if it is rejected after use. A design says "candidate X, pending ADR-NNN". It never says "we use X". A technology with no ADR row is not a candidate; it is a question for section 4.8.

### 4.8 Open questions and dependencies

Numbered. Each names the ticket, ADR or human decision it waits on, and what the design assumes meanwhile, marked `ASSUMED`. An `UNKNOWN_BLOCKING` item is one the design cannot proceed past; it must name who can unblock it.

### 4.9 Work Package cut

How the epic becomes one or more Work Packages: each with one bounded outcome, an owner role, a verifier role, acceptance criteria drawn from sections 4.5 and 4.6, and a rollback. The one-primary-package rule of the manual applies; the cut says which package is first and why.

## 5. Rules every design obeys

1. **Tenant names.** Tenant A is UniTrust, the corporate brokerage; Tenant B is the government-linked travel scheme. Both names are used because they are already public in this repository; the operator may withdraw either.
2. **Vocabulary** follows `CONTEXT.md` once it exists and [`DOMAIN_MODEL.md`](../DOMAIN_MODEL.md) section 3 until then. *Instruct*, *confirm* and *issue* are three binding moments, never one *bind*; an *indication* is a broker-computed price and a *quote* an insurer's offer; a *representation* is never the *fact* it represents.
3. **Claims.** A design never says a capability is implemented, secure, compliant or production-ready. It says what would prove that, and who would record it.
4. **Sources.** A fact about a product or specification cites the primary source by URL and date checked, or is marked `UNVERIFIED`. The research files are the pack's first citations: `docs/research/p0-design/<slug>.md` on branch `research/<slug>` for this map, and `docs/research/arch-001a/<slug>.md` on branch `research/<slug>` for the contract map. None is merged to `main`; a design cites the branch and the commit.
5. **Synthetic data only.** Every example, fixture and scenario in a design uses synthetic Tenant A and Tenant B records. No client, policy, claim or premium data, real or plausible, enters this repository.
6. **Landing.** A design lands by one Work Package pull request from one branch, referencing the map and its ticket, after a fresh-context review of the head that is merged, with `badf/` re-anchored and a checkpoint, as every package here does.

## 6. How the manual and the pack refer to each other

- The manual's twelve-epics section links to this file, and each epic row links to its design when that design reaches `PROPOSED`.
- A design's status block links to the manual's `#epics` anchor.
- The manual's status sentences about P0 do not change because designs exist. The manual describes the phase; the pack describes the work; `BT-G0` and `BT-G1` are recorded by humans in neither.
