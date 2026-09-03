# Tenant Authority and Operating-Regime Profile — Template

> Use one copy per tenant **and** materially different product/authority arrangement. Store restricted agreements outside this public repository; record only approved metadata and evidence references here.

| Field | Required value |
|---|---|
| Profile ID | `BIZTRUST-AUTHORITY-PROFILE-...` |
| Status | `DRAFT`, `IN_REVIEW`, `ACCEPTED`, `EXPIRED` or `BLOCKED` |
| Tenant / arrangement | Stable non-sensitive identifier |
| Acting legal entity | Registered name and approved identifier |
| Operating jurisdictions | Countries/territories and relevant sub-jurisdictions |
| Lines of business | Approved insurance classes/products |
| Effective period | Start, end/review date and timezone |
| Profile owner | Named accountable human role |
| Source revision | Git commit containing this profile metadata |

## 1. Licence and operating permissions

| Question | Answer | Evidence reference | Reviewer | Expiry / recheck |
|---|---|---|---|---|
| What intermediary activity may the legal entity perform? | `UNKNOWN_BLOCKING` | | | |
| Which regulator/authority supervises it? | `UNKNOWN_BLOCKING` | | | |
| Which product classes, customers and territories are permitted? | `UNKNOWN_BLOCKING` | | | |
| Which activities require referral or prior approval? | `UNKNOWN_BLOCKING` | | | |

## 2. Contract-conclusion authority

Choose only after reviewing the operative agreement:

```text
REQUEST_ONLY
DELEGATED_AUTHORITY
MASTER_POLICY_CERTIFICATE
OTHER_DEFINED_AUTHORITY
UNKNOWN_BLOCKING
```

| Question | Answer | Evidence reference | Reviewer |
|---|---|---|---|
| Who can make cover legally effective? | `UNKNOWN_BLOCKING` | | |
| Can this entity conclude contracts on an insurer's behalf? | `UNKNOWN_BLOCKING` | | |
| Can it issue certificates or other evidence of cover? | `UNKNOWN_BLOCKING` | | |
| What products, limits, territories and periods constrain the authority? | `UNKNOWN_BLOCKING` | | |
| What referrals, approvals or counter-signatures are required? | `UNKNOWN_BLOCKING` | | |
| What evidence and reference identify an effective confirmation? | `UNKNOWN_BLOCKING` | | |
| What effective-date, time and timezone rules apply? | `UNKNOWN_BLOCKING` | | |

## 3. Product, wording, rating and quote authority

| Object | Authoritative owner | BizTrust role | Evidence | Qualification |
|---|---|---|---|---|
| Insurance product | `UNKNOWN_BLOCKING` | Catalogue/reference/distribution configuration | | |
| Policy wording | `UNKNOWN_BLOCKING` | Immutable representation/digest | | |
| Rating rules | `UNKNOWN_BLOCKING` | Adapter or approved delegated execution | | |
| Eligibility/underwriting rule | `UNKNOWN_BLOCKING` | Capture/evaluate/refer as authorized | | |
| Price calculated by BizTrust | `INDICATION`, `INSURER_QUOTE`, `DELEGATED_OFFER` or `UNKNOWN_BLOCKING` | | | |
| Quote/offer | `UNKNOWN_BLOCKING` | Immutable sourced representation | | |

## 4. Placement and contract topology

| Question | Answer | Evidence / example |
|---|---|---|
| May a risk be split by insurer share? | `YES`, `NO`, `UNKNOWN_BLOCKING` | |
| May cover be arranged in layers with attachment/exhaustion points? | `YES`, `NO`, `UNKNOWN_BLOCKING` | |
| Are facilities, schemes or master policies used? | `YES`, `NO`, `UNKNOWN_BLOCKING` | |
| Are certificates/declarations issued beneath them? | `YES`, `NO`, `UNKNOWN_BLOCKING` | |
| Are bordereaux required? At what cadence and cut-off? | `YES`, `NO`, `UNKNOWN_BLOCKING` | |
| Are account-current statements required? | `YES`, `NO`, `UNKNOWN_BLOCKING` | |

## 5. Client money and risk transfer

| Question | Answer | Evidence reference | Finance/legal review |
|---|---|---|---|
| Does the entity receive premium from clients? | `UNKNOWN_BLOCKING` | | |
| Does it receive claims/refund money from insurers? | `UNKNOWN_BLOCKING` | | |
| Who bears loss risk while funds are held or in transit? | `CLIENT`, `INSURER`, `BROKER`, `OTHER`, `UNKNOWN_BLOCKING` | | |
| When is premium legally treated as paid? | `UNKNOWN_BLOCKING` | | |
| Must client and office funds be separated? | `UNKNOWN_BLOCKING` | | |
| Which account, bank, currency and signatory constraints apply? | `UNKNOWN_BLOCKING` | | |
| May commission be withdrawn before insurer remittance? | `UNKNOWN_BLOCKING` | | |
| What reconciliation cadence and approval apply? | `UNKNOWN_BLOCKING` | | |
| Can a refund be paid before insurer reimbursement? | `UNKNOWN_BLOCKING` | | |
| What happens on insolvency or account shortfall? | `UNKNOWN_BLOCKING` | | |

## 6. Servicing and cover/payment conditions

| Question | Answer | Evidence / rule owner |
|---|---|---|
| Can a premium warranty delay, suspend or cancel cover? | `UNKNOWN_BLOCKING` | |
| Who authorizes an endorsement/MTA and when is it effective? | `UNKNOWN_BLOCKING` | |
| What cancellation bases and notice periods exist? | `UNKNOWN_BLOCKING` | |
| Is refund pro-rata, short-rate or rule-dependent? | `UNKNOWN_BLOCKING` | |
| When is commission earned and when is it clawed back? | `UNKNOWN_BLOCKING` | |
| Which day-count, precision and rounding rules apply? | `UNKNOWN_BLOCKING` | |
| How are renewal invitation, lapse, NTU and continuous cover handled? | `UNKNOWN_BLOCKING` | |

## 7. Information, residency and retention

| Data class | Permitted locations | Retention | Erasure/legal hold | Disclosure limits | Evidence |
|---|---|---|---|---|---|
| Identity and access | `UNKNOWN_BLOCKING` | | | | |
| Client and risk | `UNKNOWN_BLOCKING` | | | | |
| Quote/advice/acceptance | `UNKNOWN_BLOCKING` | | | | |
| Policy and documents | `UNKNOWN_BLOCKING` | | | | |
| Claims and medical/sensitive evidence | `UNKNOWN_BLOCKING` | | | | |
| Payment and client money | `UNKNOWN_BLOCKING` | | | | |
| Journal, settlement and reconciliation | `UNKNOWN_BLOCKING` | | | | |
| Audit and security telemetry | `UNKNOWN_BLOCKING` | | | | |

## 8. Required external obligations

| Counterparty | Interface/report | Direction | Cadence/SLA | Authority/security | Owner |
|---|---|---|---|---|---|
| Insurer | `UNKNOWN_BLOCKING` | | | | |
| Bank/PSP | `UNKNOWN_BLOCKING` | | | | |
| Regulator/government | `UNKNOWN_BLOCKING` | | | | |
| Partner/channel | `UNKNOWN_BLOCKING` | | | | |

## 9. Evidence register

| Evidence ID | Type/title | Parties/issuer | Effective period | Secure location | SHA-256 if permitted | Reviewed subjects | Access owner |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

Never place credentials, bank account details, customer data, private clauses or unrestricted legal advice in this table.

## 10. Review record

| Review seat | Reviewer | Date | Verdict | Qualifications / limits | Finding reference |
|---|---|---|---|---|---|
| Business authority | | | `PENDING` | | |
| Insurance domain | | | `PENDING` | | |
| Legal/compliance | | | `PENDING` | | |
| Finance/accounting | | | `PENDING` | | |
| Architecture | | | `PENDING` | | |

Allowed verdicts: `ACCEPT`, `REVISION_REQUIRED`, `NOT_APPLICABLE_WITH_RATIONALE`.

## 11. Unresolved blockers and expiry

| Blocker | Dependent architecture slices | Owner | Target resolution | Fallback |
|---|---|---|---|---|
| | | | | Keep dependent decisions unfrozen |

The profile must be revalidated when a licence, agreement, product authority, bank arrangement, law, jurisdiction, data location or operating model changes, and no later than its recorded review date.
