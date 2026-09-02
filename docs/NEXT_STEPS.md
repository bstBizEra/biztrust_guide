# Recommended Next Steps

**Document:** BIZTRUST-GUIDE-ROADMAP-002  
**Decision posture:** The guide is implemented; deployment activation and governance hardening remain.

## Immediate — activate the public guide

### NS-001: Enable GitHub Pages

- **Owner:** Repository administrator
- **Action:** Select `GitHub Actions` under `Settings → Pages → Build and deployment → Source`.
- **Evidence:** Successful `Deploy BizTrust Guide to GitHub Pages` run and reachable production URL.
- **Stop if:** The repository contains sensitive or unapproved information.

### NS-002: Verify production

- **Owner:** QA / documentation engineer
- **Action:** Verify entry page, CSS, JavaScript, images, navigation, search, mobile layout and HTTPS.
- **Evidence:** Deployment URL, source SHA, checklist and timestamp.
- **Stop if:** The deployment SHA differs from approved `main`.

## Next 7 days — establish controlled collaboration

### NS-003: Create the governing Work Package issue

Use the included Work Package issue form. Link the issue to a GitHub Project and assign lifecycle, authority, risk, gate and evidence fields.

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

Complete `BIZTRUST-WP-ARCH-001A`, ADR-001…012, domain glossary, conceptual ERD, RBAC and state-machine contracts.

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

