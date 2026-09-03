# BizTrust Authorization Baseline

| Field | Value |
|---|---|
| Version | `0.1-draft` |
| Status | `DRAFT FOR IAM AND SECURITY REVIEW` |
| Parent | `BIZTRUST-ARCH-001` |
| Target child contract | `BIZTRUST-IAM-001` |

## 1. Authorization expression

BizTrust authorization is not role-name checking alone:

```text
Access Decision = Role + Permission + Resource Scope + Conditions + Approval Authority

Authoritative Act = Access Decision + Accepted Business/Legal Authority + Evidence
```

| Element | Question |
|---|---|
| Role | What business function does the actor perform? |
| Permission | Which command or query is allowed? |
| Resource scope | Which tenant, legal entity, business unit, team, client or assigned case? |
| Conditions | Which state, amount, product, channel, time or risk conditions apply? |
| Approval authority | Must another authorized actor approve the action? |
| Business/legal authority | Does a licence, insurer agreement, master policy or other accepted source permit this entity to create the asserted insurance fact? |

An access allow result requires every applicable security layer to allow. Missing context, conflicting policy or unavailable approval is deny-by-default. An access allow does not itself make a coverage assertion authoritative; `ADR-013` must also validate the governing authority, scope, effective period and evidence.

## 2. Candidate roles

### Platform roles

| Role | Intended scope | Explicit restriction |
|---|---|---|
| `platform-admin` | Platform configuration | No routine tenant business access |
| `platform-operations` | Service operation and recovery | No business approval authority |
| `platform-support` | Bounded troubleshooting | Time-limited, audited elevation only |
| `platform-compliance` | Cross-platform compliance oversight | Read-only unless a governed action says otherwise |
| `platform-auditor` | Independent evidence access | No mutation |

Platform administration must not imply unrestricted tenant-data visibility. Support access requires a separately authorized, expiring and fully audited elevation workflow.

### Tenant roles

- `tenant-owner`
- `tenant-admin`
- `broker-manager`
- `broker`
- `account-manager`
- `claims-advocate`
- `finance`
- `compliance`
- `auditor`
- `viewer`

### Machine roles

- `insurer-adapter`
- `payment-provider`
- `partner-api`
- `integration-worker`
- `reporting-service`

Machine identities receive narrow API audiences, scopes, tenant/partner mappings, credential rotation and rate limits. They do not reuse human sessions.

## 3. Draft tenant capability matrix

Legend: `F` full within granted scope, `C` controlled/approval required, `R` read, `O` own or assigned records, `—` denied by default.

| Capability | Tenant admin | Broker manager | Broker | Claims | Finance | Compliance | Auditor | Viewer |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Manage tenant configuration | F | — | — | — | — | R | R | — |
| Manage members and roles | F | C | — | — | — | R | R | — |
| Read client | F | F | O | O | R | R | R | R |
| Change client | F | F | O | — | — | — | — | — |
| Change risk | F | F | O | — | — | R | R | R |
| Submit risk | F | F | O | — | — | R | R | R |
| Manage placement and quote | F | F | O | — | — | R | R | R |
| Issue recommendation | C | F | O | — | — | R | R | R |
| Request bind | C | C | O/C | — | R | R | R | — |
| Record coverage evidence | C | C | O/C | — | — | R | R | — |
| Service policy | F | F | O | — | R | R | R | R |
| Manage claim advocacy | F | F | R | O | — | R | R | R |
| Read payment and invoice | F | R | O | — | F | R | R | R |
| Request refund | C | — | — | — | C | R | R | — |
| Read commission | F | R | O when entitled | — | F | R | R | — |
| Create settlement | C | — | — | — | C | R | R | — |
| Post or reverse journal | — | — | — | — | C | R | R | — |
| Approve compliance action | — | — | — | — | — | C | R | — |
| Read audit evidence | R | R | O | O | R | F | F | — |

This matrix is a review baseline, not an accepted entitlement configuration. Exact permissions, own/assigned semantics, amount thresholds and maker-checker rules require domain and security approval.

## 4. Sensitive-action approval baseline

| Action | Candidate control | Evidence |
|---|---|---|
| Disable tenant | Platform and tenant authority separation | Reason, approver, expiry and impact plan |
| Publish distribution product version | Distribution owner plus compliance and source-authority review | Version digest, insurer/product source and publication record |
| Issue recommendation | Qualified broker authority | Compared quotes, rationale and disclosure evidence |
| Request bind | Client acceptance plus broker authority | Accepted terms and actor evidence |
| Record coverage confirmation | Trusted authority source or permitted broker action under an accepted authority profile | Authority agreement/profile, source identity, effective period and evidence digest |
| Request refund | Finance maker-checker above configured threshold | Original payment, reason and approvals |
| Reverse journal | Separate finance authority | Original journal, reversal reason and balanced entry |
| Complete settlement | Finance approval and reconciliation | Batch items, variance and bank/carrier evidence |
| Elevate support access | Tenant consent or emergency policy | Scope, expiry, session trace and revocation |

Thresholds are tenant- and jurisdiction-dependent and must be configuration with versioned approval, not hard-coded assumptions.

## 5. Enforcement layers

| Layer | Responsibility | Failure behavior |
|---|---|---|
| Identity provider | Authenticate, issue audience/organization/scopes | Invalid token denied |
| API gateway | Basic token/traffic/mTLS policy | Deny before application where possible |
| API boundary | Verify issuer, audience, expiry and organization context | Deny with safe problem response |
| BizTrust policy | Membership, permission, scope, conditions and authority | Deny and audit reason code |
| Business-authority policy | Licence/agreement, product, limit, territory, time and referral constraints | Reject authoritative act; access permission cannot override |
| Domain module | State and business invariants | Reject prohibited transition |
| PostgreSQL RLS | Row visibility and write ownership | Default deny; no cross-tenant row returned |
| Audit | Attributable decision evidence | Alert if mandatory evidence cannot be written safely |

No single layer substitutes for another. A gateway allow is not domain authorization, and an application allow is still constrained by RLS.

## 6. Resource-scope examples

```text
tenant:<tenant-id>
legal-entity:<legal-entity-id>
business-unit:<unit-id>
team:<team-id>
client:<client-id>
placement:<placement-id>
claim:<claim-id>
assigned-to:<actor-id>
```

The exact encoding is not frozen. Stable semantics and tenant ownership must be defined before policy implementation.

## 7. Authorization evidence contract

Each sensitive decision records:

```text
decision_id
occurred_at
actor_id
actor_type
tenant_id
membership_id
permission
resource_type
resource_id
resource_scope
conditions_evaluated
approval_reference
business_authority_profile_id
business_authority_agreement_reference
business_authority_scope_evaluated
policy_version
outcome
reason_code
request_id
trace_id
```

Do not record raw tokens, secrets or unnecessary personal data.

## 8. Required tests

- valid role, permission and scope allows;
- missing role or permission denies;
- inactive membership denies;
- cross-tenant resource denies;
- same role but wrong business unit/team denies;
- own/assigned restriction denies unassigned records;
- state-dependent permission denies the wrong state;
- threshold action without approval denies;
- expired approval denies;
- replayed approval cannot authorize a different resource;
- a user with `binding:confirm` but no applicable authority profile cannot confirm cover;
- an otherwise valid delegated authority outside its product, limit, territory or effective period cannot confirm cover;
- a `REQUEST_ONLY` profile rejects broker-created confirmation and requires insurer evidence;
- support elevation expires and is fully audited;
- service principal cannot use human-only commands;
- RLS blocks access when the application authorization test path is bypassed.
