# Derived Resume Control Plane

> **Status: `PROPOSED`.** Not an approved architecture decision. Exit criteria for the
> bounded experiment are in *Key Assumptions*; nothing here is implemented, and no
> repository change should follow until the blind handoff experiment reports.

## Problem Statement

**How might we give a resuming agent one surface that cannot tell it something false — in a repository where operational state has a measured 24-hour half-life and the existing controls prove shape rather than truth?**

## Recommended Direction

**Authoritative inputs → one deterministic derivation model → `RESUME.json` + HTML, published as artifacts.**

Three measurements on `main` at `36f7c5d`:

1. **The controls pass while the content is false.** The full suite reports 47/47 and the validator prints `CONTINUITY_VALIDATION=PASS`, while `current-state.json` names `WP-017` active (merged), `NS-001 · enable Pages` as next (Pages is live, serving 200), and *"Seven pull requests await human review"* (zero are open). The recorded baseline is **13 commits behind** `main`. Every control is green and every operational claim is wrong.
2. **Correction does not hold.** PR #30 fixed exactly this on 2026-09-03. It was wrong again within 24 hours, corrected by the same person who wrote the correction.
3. **Only about half the file is machine-writable.** At leaf level — 33 leaves, not 14 top-level properties — the split is `STATIC 6% · OBSERVED 33% · ASSERTED 39% · COMPUTED 21%`. **54%** can be derived.

An earlier draft of this page claimed 71% and asserted that "the fields that rot are exactly the fields a machine could write." **Both were wrong**, and an audit caught them. The 71% counted top-level keys, treating `authority` (5 leaves) and `active_work_package.scope` (4 leaves) as single facts. And `active_work_package.id` is an **assertion that went stale** — a human wrote "WP-017 is active" and never retracted it when WP-017 merged. Assertions rot too, whenever the world they reference moves.

That correction changes the design. Derivation alone is insufficient because 39% of the leaves are human assertions. Those need **structure** — issuer, scope, evidence, effective time, expiry, revocation — rather than the unqualified strings they are today. The operative question for every leaf is not *"who writes it"* but **"can this be wrong without anyone noticing?"** That criterion cuts across all four categories and is what the deriver must close.

Build one read-only deriver producing both outputs from a single in-memory model, published as **artifacts** — `_site/RESUME.json` and `_site/control-room.html` — never committed back. The page leads with stop conditions and declared non-coverage, then names **exactly one** safe next action, because the success criterion is *an agent resumed correctly, unaided*, and agents resume incorrectly by acting confidently on premises that moved while they were away.

## Key Assumptions to Validate

- [ ] **A blind agent resumes correctly from the artifact alone.** *Test:* hand-authored fixtures, multiple blind agents each, no conversation history. Minimum set: fresh snapshot · `main` moved after derivation · issue/PR changed with `main` static · authority expired · zero *and* multiple candidate Work Packages · API unavailable · conflicting inputs. **Accept only if:** correct resume decision, zero unauthorised execution, every critical stop condition named, exactly one safe next action, source SHA and freshness cited, and **no invented facts**. A single passing run is a smoke test, not evidence.
- [ ] **The deriver reports truth, not merely labels.** Issue #2 is open and labelled `state:in-progress` while its work merged in #28. A deriver can render that label accurately and still infer the wrong operational state. *Test:* a fixture where the label and the reality disagree; the correct output is a stop condition, not a next action.
- [ ] **Unavailable inputs degrade to `UNKNOWN`, never to a guess.** *Test:* run with the API blocked. A deriver that guesses is worse than the prose it replaces.
- [ ] **A build cannot report its own outcome.** The Pages deploy job runs *after* validation, so a deriver inside that workflow cannot know whether deployment succeeded. *Test:* assert the artifact records the **previous completed** deployment, or `PENDING_EXTERNAL_CONFIRMATION` — never the in-flight one.

## MVP Scope

Minimum that tests assumption 1 — nothing more.

**In:** a read-only deriver run in **shadow mode** (produces output, changes no behaviour) · `RESUME.json` with per-leaf `source`, `observed_at` and `freshness` · the snapshot inheriting the **worst** freshness of its critical inputs · `main_sha != source_sha` → immediately stale · hand-authored fixtures · the blind handoff experiment.

**Out:** the ten Markdown sources and the Markdown parser · per-section refresh dates · search, filter, print · the second theme system · any change to `AGENTS.md`, the validator or the continuity guide until the experiment reports.

**Deferred to phase 2, deliberately:** hybrid event-based invalidation (issue/PR/label refresh with bounded observation age). The built system needs it — issues and authority change without a push — but the MVP's only job is to learn whether an agent can use this surface at all. Building polling machinery first means constructing invalidation for something nobody has shown is usable.

## Not Doing (and Why)

- **CI commits to `main`.** The workflow sets `contents: read` and `persist-credentials: false` on purpose. An earlier draft of this proposal said "derive, commit if changed" — that needs `contents: write` and silently undoes a deliberate boundary. Publish artifacts under `pages: write` + `id-token: write` instead, which is GitHub's supported model and needs no repository write at all.
- **A Markdown source layer.** It forks the source of truth, agents never read it, and it produced eight false assertions in the previous attempt. Durable content — rationale, policy, ADRs, historical evidence — stays in Markdown. Volatile state replicas do not.
- **Per-section refresh dates.** Seven of ten sections previously carried `refresh_by: null` and could never expire, which is exactly where the wrong facts lived. One freshness verdict for the snapshot, derived from its worst input.
- **A universal 24-hour expiry.** Constants do not expire. Authority expires on its own terms. External observations expire on theirs. A blanket window either never fires or fires constantly, and a check people route around is worse than none.
- **A second theme system.** The previous page shipped 9 tokens with no dark counterpart, including `--blue-700` at **2.87:1** on every link. Use `styles.css` and inherit the detector from #42.
- **A dashboard that shows only green.** This repository's own evidence is that 47 passing tests and a `PASS` validator coexisted with a wholly false operational record. Show what is **not** enforced with equal prominence, or do not build it.
- **Retiring manual state before the experiment reports.** The current ledger stays authoritative until shadow mode has been proven across several `main` moves, an issue-only change, expired authority and an API failure.

## Open Questions

- **Who issues and revokes `authority`?** It is 5 of the 13 asserted leaves and no role owns it. Without an issuer, adding `valid_until` just moves the staleness.
- **What retracts a stale assertion?** `active_work_package.id` was asserted, then rotted. Expiry helps; automatic revocation on a contradicting observation may be better, and is riskier.
- **Should `#32` be re-scoped or closed and replaced?** Its title and body describe the Markdown-first design this supersedes. Re-scoping preserves the thread; closing keeps the record honest about what was rejected.
