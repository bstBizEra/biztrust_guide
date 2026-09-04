# Recommended Next Steps

**Document:** BIZTRUST-GUIDE-ROADMAP-002  
**Decision posture:** The nine-stage guide is drafted and under defect correction — see `gates.content` in `badf/current-state.json`. Governance hardening remains; deployment activation (NS-001) is done, and production verification (NS-002) is verified for bytes, assets and HTTPS with navigation, search and mobile layout not exercised — both dated below.

> ⚠️ **The NS ids in this document are frozen roadmap labels from 2026-09-02. They are NOT the live action ledger.**
>
> `badf/next-actions.json` allocates NS ids as a rolling counter, a fresh block per work package, retiring the previous block. It never re-uses an id with a different meaning *within* its own ledger — but **NS-004 through NS-012 name different work there than they do here**, because both files number from one. Only NS-001, NS-002 and NS-003 mean the same thing in both places.
>
> A `next_action_id` found in `badf/` or in `sessions/checkpoints/` **must** be resolved against `badf/next-actions.json` **at the revision that issued it** — never against this file. Resolving NS-011 here yields "prove P0 tenant isolation"; in the ledger that issued it, it meant "merge pull request #4". This repository has no authority to do the former.

## Immediate — verify the public guide (NS-001 and NS-002 dated below)

### NS-001: Enable GitHub Pages

- **Owner:** Repository administrator
- **Action:** Select `GitHub Actions` under `Settings → Pages → Build and deployment → Source`.
- **Evidence:** Successful `Deploy BizTrust Guide to GitHub Pages` run and reachable production URL.
- **Stop if:** The repository contains sensitive or unapproved information.
- **Done, dated 2026-09-04:** `GET /repos/bstBizEra/biztrust_guide/pages` reports `build_type: workflow`, and the `github-pages` environment's first successful deployment (6244308440, of `ba46e1f7`) is timestamped 2026-09-03T12:51:36Z. This entry records that the action happened; it does not say what the site serves now — read that from the deployments API.

### NS-002: Verify production

- **Owner:** QA / documentation engineer
- **Action:** Verify entry page, CSS, JavaScript, images, navigation, search, mobile layout and HTTPS.
- **Evidence:** Deployment URL, source SHA, checklist and timestamp.
- **Stop if:** The deployment SHA differs from approved `main`.
- **Verified (bytes, assets, HTTPS), dated 2026-09-04T19:22:58Z:** recorded in the § 7 format of `LIVE_PREVIEW.md`, with three added fields (`deployment`, `all_tracked_pages`, `https`), against `main` at `6a88463b7db2d20ef2a1c71c9983536c340f65f3`.

  ```text
  source_commit: 6a88463b7db2d20ef2a1c71c9983536c340f65f3
  preview_mode: github-pages
  url: https://bstbizera.github.io/biztrust_guide/
  entry_file: index.html
  assets_checked: true                         # styles.css, script.js and all three assets/*.png -> 200 at committed sizes
  validation_command: python3 scripts/validate_continuity.py
  validation_exit_code: 0
  workflow_run: https://github.com/bstBizEra/biztrust_guide/actions/runs/33910065490   # pointer only; expires
  deployment: 6271172171 (github-pages, sha 6a88463b, created 2026-09-04T19:14:09Z)
  deployed_bytes: 42335
  deployed_sha256: c06d5c6831f7a84bc1dd6694042c93ed91f78360d5610091cfbf4f5aeed183a2
  source_bytes: 42335
  source_sha256: c06d5c6831f7a84bc1dd6694042c93ed91f78360d5610091cfbf4f5aeed183a2
  all_tracked_pages: 17 fetched, 17 byte-identical to git show main:<path> (sha256 compared)
  https: enforced (GET /pages https_enforced true; http:// -> 301 to https://)
  verified_by: documentation-engineer (agent), evidence in the WP-041 checkpoint; independently reproduced by the PR #83 reviewer
  verified_at: 2026-09-04T19:22:58Z
  ```

  Checklist against the Action line above: entry page ✓ · CSS ✓ · JavaScript ✓ · images ✓ (three PNGs) · HTTPS ✓ (enforced) · navigation ✗ · search ✗ · mobile layout ✗ — the last three were not exercised in a browser and remain open.

  This records that the deployment of that commit was verified at that time. It says nothing about what the site serves now; read that from the deployments API, as NS-001 says.

## Next 7 days — establish controlled collaboration

### NS-003: Create the governing Work Package issue

Use the included Work Package issue form. Link the issue to a GitHub Project and assign lifecycle, authority, risk, gate and evidence fields.

- **Measured 2026-09-04T20:20Z, mostly not done.** The form (`.github/ISSUE_TEMPLATE/work-package.yml`) exists. **No issue was created through it:** none of the fourteen `work-package`-labelled issues carries the form's rendered headings (`### Work Package ID`, `### Required evidence`, `### Readiness declaration`) or its `state:draft` label; their bodies reproduce the form's sections by hand, unevenly, since issue #2 (`BIZTRUST-GUIDE-WP-003`, 2026-09-02T14:44:18Z). The lifecycle, authority, risk, gate and evidence *fields* this entry names are GitHub Project fields (`docs/AGENT_CONTINUITY.md` §10), and **no GitHub Project exists** on the owner account (`viewer.projectsV2.totalCount` = 0); no issue has a project item (`issue(number).projectItems.totalCount` = 0 across all fourteen). Creating a Project and granting write access to it is the owner's; this agent's token has no `project` scope.

### NS-004: Protect `main`

Recommended rules:

- require pull requests;
- require one independent approving review;
- dismiss stale reviews;
- require conversation resolution;
- require `Validate continuity and static site`;
- block force pushes and deletion;
- restrict bypass to emergency human authority;
- require linear history if compatible with the merge strategy.

### NS-005: Establish documentation ownership

Assign accountable human owners for:

- agent governance;
- insurance-domain accuracy;
- security architecture;
- financial architecture;
- deployment and availability;
- brand and public communications.

## Next 30 days — move from guide to executable governance

### NS-006: Implement full JSON Schema validation

The included validator covers the continuity baseline without external dependencies. The next controlled improvement should validate every checkpoint, handoff, Work Package, decision and evidence record against versioned JSON Schemas.

### NS-007: Bind Issues, branches and pull requests

Enforce the naming convention:

```text
Issue:  BIZTRUST-WP-<DOMAIN>-<NNN>
Branch: feat/<work-package-id>-<slug>
Commit: <type>(<scope>): <summary> [<work-package-id>]
PR:     [<work-package-id>] <outcome>
```

### NS-008: Add evidence manifests

For each required check, retain:

- source commit;
- workflow and job;
- tool version;
- exit code;
- artifact digest;
- verifier;
- declared coverage and non-coverage.

### NS-009: Test recovery

Run a controlled exercise in which one agent stops mid-Work Package and a separate agent resumes using only repository artifacts. Measure recovery time, missing context and duplicate work.

## Next 60–90 days — operationalize the BizTrust engineering team

### NS-010: Freeze BIZTRUST-ARCH-001

Complete `BIZTRUST-WP-ARCH-001A`, ADR-001…020, domain glossary, conceptual ERD, RBAC and state-machine contracts.

### NS-011: Prove P0 tenant isolation

Implement and verify:

```text
Logto → organization token → APISIX → tenant context
→ authorization policy → PostgreSQL RLS → audit evidence
```

P1 remains blocked until cross-tenant denial is mechanically proven.

### NS-012: Start the P1 broker-core vertical slice

Only after P0 acceptance:

```text
Tenant → Broker → Client → Risk → Product Version
→ Submission → Quote → Recommendation → Bind → Policy Register
```

## Recommended operating cadence

| Cadence | Control activity |
|---|---|
| Every session | Resume protocol and current-state reconciliation |
| Every coherent slice | Checkpoint and deterministic validation |
| Every handoff | Sender record + receiver acknowledgement |
| Every pull request | Independent review and evidence manifest |
| Weekly | Stale state, leases, blockers and orphan branch review |
| Monthly | Governance KPIs and recovery exercise |
| Quarterly | Architecture, authority and risk-policy review |

## Success criteria

This roadmap succeeds when a newly assigned agent can answer, without prior chat history:

1. What is the active Work Package?
2. What outcome is authorized?
3. What is complete, validated and accepted?
4. What is blocked and who owns the unblock?
5. What exact revision and evidence are authoritative?
6. What is the single next safe action?
7. What conditions require the agent to stop?

