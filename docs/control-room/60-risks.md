---
id: risks
title: Blockers, Risks and Assumptions
order: 60
kind: governance
status: BLOCKED
owner: risk-owner
updated: 2026-09-03
source: https://github.com/bstBizEra/biztrust_guide/issues/15
summary: Conditions that can invalidate delivery, architecture or evidence if left implicit.
---

## Active blockers

| ID | Condition | Impact | Owner | Resolution |
|---|---|---|---|---|
| `R-001` | GitHub Pages is not enabled | Public guide cannot be verified live | Repository administrator | Complete NS-001 and retain deployment evidence |
| `R-002` | Tenant binding/delegated authority is unknown | State machine, ERD and ledger may encode the wrong legal model | Business + insurance + legal | Complete S01 profile with operative evidence |
| `R-003` | Client-money/risk-transfer regime is unknown | Chart of accounts and reconciliation may be wrong | Legal + finance | Qualified, tenant-specific conclusion |
| `R-004` | Concurrent PRs own shared files | Uncoordinated edits can erase reviewed work | Orchestrator | Compose after owners merge; stop on overlap |
| `R-005` | Actions evidence retention changes from October 2026 | Run URLs may cease to prove historical outcomes | Governance owner | Resolve Issue #26 with durable evidence content |

## Operating risks

- **Snapshot drift:** a visually polished dashboard can make old data look current.
- **Dual-ledger drift:** hand-edited HTML can contradict Markdown or GitHub Issues.
- **Authority laundering:** displaying a proposed decision can make it appear approved.
- **Sensitive disclosure:** public Markdown must never contain private agreements or client data.
- **Dependency bypass:** backlog priority can be mistaken for authorization to start.

## Assumptions requiring revalidation

- GitHub Issues remain available as the human coordination ledger.
- The static Pages artifact continues to include every tracked HTML page.
- PR #28 remains the accepted base for this stacked documentation slice.
- Initial tenant arrangements may differ materially and cannot share assumed authority rules.
