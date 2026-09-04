# Agent Continuity & Recovery Protocol

**Document:** BIZTRUST-GOV-CONTINUITY-001  
**Control objective:** No agent depends on transient conversation context to identify authorized work, current state, evidence or the next safe action.

## 1. Why agents lose track

Common failure modes are predictable:

1. A session ends before state is persisted.
2. A new agent reads code but not the governing decision.
3. Completed work and accepted work are treated as equivalent.
4. Multiple agents work the same scope from different baselines.
5. A blocker is described in chat but not attached to the Work Package.
6. The next action has no owner, prerequisite or stop condition.
7. Evidence is unbound from the commit it allegedly verifies.
8. A stale summary overrides newer repository state.

The control response is a dual ledger:

- **GitHub Issue/Project:** human-visible ownership, discussion, priority and approvals.
- **Versioned repository state:** agent-readable state, checkpoint, handoff, evidence and next action.

Neither chat nor an agent's internal memory is a source of truth.

## 2. Continuity architecture

```text
GitHub Issue / Project item
        │
        ├── scope + owner + status + human decisions
        │
        ▼
Work Package contract
        │
        ├── acceptance criteria + authority + risk
        │
        ▼
badf/current-state.json ──→ latest checkpoint
        │                         │
        ├── active state          ├── evidence
        ├── active branch         ├── changes
        ├── blockers              ├── assumptions
        └── next action           └── recovery command
        │
        ▼
badf/next-actions.json
        │
        ▼
Exactly one safe resumable action
```

## 3. Five continuity invariants

### CONT-001 — Stable identity

Every material activity has one stable Work Package ID reused in the issue, branch, commits, pull request, checkpoints and evidence.

### CONT-002 — One authoritative current state

`badf/current-state.json` identifies exactly one active Work Package or explicitly declares that no work is active.

### CONT-003 — Exactly one primary next action

The active Work Package has one `primary` next action with an owner, prerequisites, expected evidence and stop conditions.

### CONT-004 — Commit-bound evidence

Validation evidence records the commit or content digest that was tested. Evidence from another revision cannot authorize the current revision.

### CONT-005 — Fail-closed recovery

Missing, invalid, stale or conflicting continuity data produces `RECOVERY_REQUIRED` or `WAIT_FOR_AUTHORITY`; it never defaults to execution.

## 4. Mandatory session start

Every agent starts with the following algorithm:

```text
READ AGENTS.md
READ badf/current-state.json
READ badf/next-actions.json
RESOLVE active Work Package and GitHub Issue
READ latest checkpoint and handoff
OBSERVE git branch, HEAD, status and remote divergence
RUN deterministic continuity validator
COMPARE observed state to recorded state
DECIDE CONTINUE | BLOCKED | WAIT_FOR_AUTHORITY | RECOVERY_REQUIRED | COMPLETE
RECORD the decision before mutation
```

If an active action belongs to another agent or has a live ownership lease, stop and coordinate before editing.

## 5. Session checkpoint protocol

### When to checkpoint

- start of authorized execution;
- every coherent delivery slice;
- before high-risk operations;
- before an external tool call that may outlive the session;
- after test or review results;
- whenever authority or scope changes;
- on blocker detection;
- before handoff or session end.

### What to checkpoint

Use `templates/session-checkpoint.json`. A valid checkpoint records facts, not optimistic narrative:

- current objective;
- completed output;
- remaining output;
- branch and baseline;
- changed files;
- exact validation results;
- decisions and assumptions;
- blocker and authority state;
- one primary next action;
- safe recovery instructions.

### Checkpoint freshness

A checkpoint is stale when:

- recorded branch differs from the working branch;
- the baseline commit is not an ancestor of `HEAD`;
- a newer accepted decision changes scope or authority;
- referenced evidence is missing;
- another owner has advanced the Work Package;
- the expiry time has passed for time-bounded authority.

Stale checkpoints are retained for history but cannot authorize execution.

## 6. Agent handoff protocol

The sender must create a handoff from `templates/handoff.json` and the receiver must acknowledge it before taking ownership.

### Sender responsibilities

1. Stop mutation at a coherent boundary.
2. Run applicable validation.
3. Update current state and next actions.
4. Separate observations from decisions.
5. Declare non-coverage and unresolved risk.
6. Name the first safe receiver action.
7. Release ownership or record an expiry.

### Receiver responsibilities

1. Verify the sender's source revision.
2. Re-run the continuity validator.
3. Confirm scope and authority independently.
4. Accept or reject the handoff explicitly.
5. Create a new checkpoint before mutation.

No response, no quorum or unavailable reviewer is `UNKNOWN`, not approval.

## 7. Ownership lease

To prevent duplicate work, an active Work Package may carry an ownership lease:

```json
{
  "owner_role": "documentation-engineer",
  "owner_session": "session-identifier",
  "acquired_at": "2026-09-02T14:00:00Z",
  "expires_at": "2026-09-02T18:00:00Z",
  "scope": ["docs", "website"],
  "renewal_requires_checkpoint": true
}
```

An expired lease does not mean the work is safe to continue. The next agent must first inspect the repository and reconcile state.

## 8. Next-action design

Every next action must answer:

| Field | Required answer |
|---|---|
| `id` | What stable action is this? |
| `priority` | In what order is it eligible? |
| `owner_role` | Who may perform it? |
| `authority` | What approval is required? |
| `prerequisites` | What must already be true? |
| `action` | What single outcome is expected? |
| `evidence_required` | What proves completion? |
| `stop_conditions` | What conditions prohibit continuation? |
| `fallback` | How is the system left safe? |

Avoid “continue implementation” or “finish testing.” A resumable next action is concrete and testable.

## 9. Recovery procedure

Use this when state is missing or contradictory:

1. Freeze all mutations.
2. Record `RECOVERY_REQUIRED` in current state.
3. Capture the observed branch, `HEAD` and worktree without cleaning or resetting.
4. Retrieve the GitHub Issue, pull request, latest accepted decision and CI runs.
5. Find the newest valid checkpoint whose baseline is an ancestor of the observed `HEAD`.
6. Compare changed files against that checkpoint.
7. Classify differences as expected, user-owned, agent-owned or unknown.
8. Reconstruct a proposed state without deleting work.
9. Run independent review for high-impact recovery.
10. Obtain authority before resuming mutation.

Never use destructive reset as an automatic recovery mechanism.

## 10. GitHub tracking model

Use a GitHub Issue as the parent Work Package. Use sub-issues or a task list for bounded delivery units. Link pull requests with closing keywords only when merge should complete the issue. Use GitHub Projects for portfolio views, iteration, priority, risk and lifecycle status.

Recommended Project fields:

| Field | Values |
|---|---|
| Lifecycle | Draft, Ready, Authorized, In Progress, Validating, Engineering Ready, Accepted, Closed |
| Authority | Not Required, Requested, Granted, Denied, Expired |
| Risk | Low, Medium, High, Critical |
| Gate | ENG-G0–ENG-G8 |
| Owner | Human or agent role |
| Target | Milestone or iteration |
| Evidence | Missing, Partial, Complete, Rejected |
| Blocker | None, Internal, External, Authority |

The `Lifecycle` values are the eight states of `AGENTS.md` §8, in order, and match the `state` enum of `schemas/session-checkpoint.schema.json`. The `Gate` values are the Work Package lifecycle gates; `BT-G0`–`BT-G6` are a different namespace (BizTrust platform capability milestones, defined in `docs/architecture/DELIVERY_PLAN.md` §1) and are not valid values for this field. Neither list is redefined here — if one is wrong, fix it at the source and update this row.

## 11. Minimum repository controls — RECOMMENDED, NONE IN FORCE

> As of 2026-09-03, `main` has **no branch protection** (`GET /branches/main/protection` → 404) and **no required status checks**. GitHub Pages has never been enabled. The `github-pages` environment does exist and `pages.yml` binds the deploy job to it — but its only branch policy is a custom pattern literally named `None`, matching no branch; `GET /pages` returns 404 and there has never been a deployment. The control has never run and cannot. An earlier version of this note called that "one control in force", which moved a safety statement in the permissive direction — the one direction a correction must never move. Everything below is the target state, tracked as NS-004 in `docs/NEXT_STEPS.md`. Do not read the list as a floor already met.

> **Corrected 2026-09-04 (issue #66).** The Pages, environment and deployment claims in the note above have since changed; the branch-protection claim has not. Measured on 2026-09-04: `GET /pages` reports `build_type: workflow`; the `github-pages` environment carries two branch policies, `main` and the earlier pattern `None`, with `can_admins_bypass: true`; and the environment holds successful deployments from `main` from 2026-09-03T12:51:36Z (deployment 6244308440) through the current head, so the control *has* run — five intermediate pushes were cancelled by the workflow's concurrency group and have no deployment of their own. `GET /branches/main/protection` still returns 404, `GET /rulesets` and `GET /rules/branches/main` return empty lists, and no `CODEOWNERS` file exists, so items 1, 2, 3, 4, 6 and 7 remain target state. Item 5 is configured, not in force: the deploy job is bound to the environment and the environment admits `main` by name, but `main` is unprotected and administrators can bypass the policy, so the restriction is bypassable by every current committer. The heading stands. The note above is left as written because it was true when dated.

1. Protect `main`; no force push or deletion.
2. Require pull requests and at least one independent approval.
3. Require continuity validation and Pages validation checks.
4. Require conversation resolution.
5. Restrict deployment to the `github-pages` environment.
6. Keep `AGENTS.md`, schemas and validators under owner review.
7. Preserve linear history where compatible with the delivery model.

## 12. Health indicators

Track these monthly:

- percentage of active Work Packages with fresh checkpoints;
- percentage with exactly one primary next action;
- orphan branches without a Work Package;
- stale ownership leases;
- evidence-to-commit mismatches;
- average recovery time after agent handoff;
- duplicate work incidents;
- authority violations prevented;
- work closed without accepted evidence.

## References

- [About GitHub Issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/about-issues)
- [About GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)
- [Syntax for GitHub Issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [Linking pull requests to issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue)
- [GitHub task lists](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/about-tasklists)

