# BizTrust Guide — Repository Agent Operating Charter

## 1. Mission

Maintain an accurate, accessible and evidence-backed implementation guide for the BizTrust Agentic Engineer Team. This repository is a documentation and deployment surface; it does not grant authority to implement the BizTrust production platform.

## 2. Precedence

When instructions conflict, apply this order:

1. Human authority recorded for the active Work Package
2. Repository protection and security policy
3. This `AGENTS.md`
4. Active Work Package contract
5. Architecture decisions and normative documentation
6. Templates and examples

Unknown or conflicting authority is not permission. Set the state to `WAIT_FOR_AUTHORITY`, record the blocker and stop the affected action.

## 3. Mandatory resume protocol

At the beginning of every session, agent handoff or recovery:

1. Read this file completely.
2. Read `badf/current-state.json`.
3. Read `badf/next-actions.json`.
4. Locate the active Work Package, its scope and acceptance criteria.
5. Read the latest checkpoint and handoff referenced by current state.
6. Inspect the current Git branch, `HEAD`, worktree and remote divergence.
7. Run `python3 -m unittest discover -s tests` — the validator's own self-tests — then `python3 scripts/validate_continuity.py`.
8. Reconcile observed state with recorded state.
9. Output one resume decision: `CONTINUE`, `BLOCKED`, `WAIT_FOR_AUTHORITY`, `RECOVERY_REQUIRED` or `COMPLETE`.

An agent must not continue from chat recollection alone.

## 4. Sources of truth

| Concern | Source of truth |
|---|---|
| Repository policy | `AGENTS.md` |
| Current operational state | `badf/current-state.json` |
| Ordered pending work | `badf/next-actions.json` |
| Human coordination | GitHub Issue / Project item |
| Delivery scope | Active Work Package |
| Architecture decision | Accepted ADR |
| Code and content | Git commit on `main` — **not branch-protected**; `GET /branches/main/protection` returns 404. The gate is convention, not mechanism |
| Test result | CI run bound to commit SHA |
| Session recovery | Latest valid checkpoint + handoff |
| Approval | Explicit authority record; never inferred |

Since WP-044, `badf/current-state.json`, `badf/next-actions.json` and every entry of `badf/decision-log.jsonl` are validated against `schemas/*.schema.json` by `tests/test_badf_match_schemas.py`, together with the rules the schemas cannot express: exactly one primary action, named by the state file; priorities numbered 1 to n; one package id across both files; the latest checkpoint present; decision ids unique and ascending.

If sources disagree, the agent records the conflict and stops the affected transition.

## 5. Work constraints

- No ticket, no work.
- Every material change must reference one Work Package ID.
- One Work Package has one objective, bounded scope and explicit acceptance criteria.
- Do not broaden scope because an adjacent improvement is convenient.
- Do not modify `main` directly when branch protection and pull requests are available.
- Do not overwrite unrelated human or agent changes.
- Do not mark work accepted based only on the implementing agent's assertion.
- Do not place secrets, tokens, private client information or regulated data in this public repository.

## 6. Required session checkpoint

Create or update a checkpoint at every one of these boundaries:

- before a risky or long-running action;
- after a coherent implementation slice;
- before requesting authority;
- before switching agents;
- when blocked;
- before ending a session;
- after verification or release.

Every checkpoint must conform to `schemas/session-checkpoint.schema.json` and record:

> Conformance is mechanically checked since WP-035 (issue #68): `tests/test_checkpoints_match_schema.py` validates every file in `sessions/checkpoints/` against the schema with a stdlib checker that refuses any schema keyword, or `format` value, it does not implement. Three checkpoints that predate enforcement — WP-017, WP-024, WP-026 — fail on shape and are registered there as a ratchet rather than rewritten; the registry may only shrink. `scripts/validate_continuity.py` itself still confirms only that the schema files parse and declare the right dialect.


- work package and state;
- objective and completed scope;
- current branch and baseline commit;
- files changed;
- validation commands and outcomes;
- decisions and assumptions;
- blockers and authority status;
- exactly one recommended next action;
- recovery instructions.

## 7. Handoff contract

A handoff is required when responsibility changes. It must identify:

- sender and receiver roles;
- stable Work Package ID;
- observed facts versus decisions;
- completed, remaining and excluded work;
- exact source revision;
- evidence references;
- unresolved risks;
- first safe command or inspection for the receiver;
- stop conditions.

Silence is never evidence of completion.

## 8. State transitions

Allowed high-level states:

`DRAFT → READY → AUTHORIZED → IN_PROGRESS → VALIDATING → ENGINEERING_READY → ACCEPTED → CLOSED`

Exceptional states:

- `BLOCKED`
- `WAIT_FOR_AUTHORITY`
- `RECOVERY_REQUIRED`
- `REJECTED`
- `CANCELLED`

Only an authorized transition may advance delivery. Validation success does not grant deployment authority.

## 9. Evidence requirements

Evidence must be attributable, reproducible and bound to the relevant source revision. At minimum record:

- repository and commit SHA;
- command or workflow identity;
- execution time and environment;
- exit status;
- material output or artifact reference;
- verifier role;
- known coverage and declared non-coverage.

## 10. Change completion protocol

Before handoff or pull request:

1. Run deterministic validation.
2. Confirm no broken local asset references.
3. Confirm every tracked `*.html` reaches the publishing artifact — CI step *Verify every tracked page reached the artifact* — not only root `index.html`. Seventeen of the eighteen tracked pages live under `stages/`, `phases/`, `reference/` and `landing/`.
4. Update `badf/current-state.json` and `badf/next-actions.json`.
5. Create a checkpoint from `templates/session-checkpoint.json`.
6. Summarize risks, non-coverage and next action.
7. Link the Work Package issue in the pull request.

## 11. Stop conditions

Stop immediately when:

- required authority is absent, ambiguous or expired;
- the repository state conflicts with the checkpoint;
- the active Work Package cannot be identified;
- validation fails on a protected invariant;
- sensitive data is detected;
- a destructive or irreversible action is outside explicit scope;
- evidence cannot be bound to the source revision;
- another agent has overlapping ownership without an explicit coordination record.

## 12. Current scope boundary

This repository may document future BizTrust architecture, but documentation must not claim that a capability is implemented, secure, compliant or production-ready unless linked evidence proves that claim.


## Agent skills

Configuration for the mattpocock engineering skills reached through `/setup-matt-pocock-skills`: `/triage` and `/code-review` read it by name; `/wayfinder`, `/to-tickets`, `/to-spec`, `/domain-modeling`, `/grill-with-docs` and `/improve-codebase-architecture` rely on the tracker and layout it records. Nothing here loosens sections 1 to 12; where the two disagree, sections 1 to 12 win.

### Issue tracker

Issues are GitHub issues in `bstBizEra/biztrust_guide`, worked through Work Package tickets. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`); a triage label never substitutes for Work Package authority. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `CONTEXT.md` and `docs/adr/`, both created lazily, with `docs/architecture/ADR_REGISTER.md` as the decision register. See `docs/agents/domain.md`.
