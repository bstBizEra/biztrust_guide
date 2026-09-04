# BizTrust Agentic Engineer Team Guide

[![Pages](https://github.com/bstBizEra/biztrust_guide/actions/workflows/pages.yml/badge.svg)](https://github.com/bstBizEra/biztrust_guide/actions/workflows/pages.yml)

Enterprise-grade implementation guide for a governed AI engineering team delivering BizTrust from architecture contract through production operations.

## Live website

The Pages workflow (`.github/workflows/pages.yml`) targets:

**https://bstbizera.github.io/biztrust_guide/**

Whether that address currently serves the `main` head is not recorded in this file — see *Current delivery state* below for where to read it.

See [Live Preview & Publishing](docs/LIVE_PREVIEW.md) for the exact GitHub and local-preview procedures.

## Local preview

### Linux, macOS or WSL

```bash
git clone https://github.com/bstBizEra/biztrust_guide.git
cd biztrust_guide
python3 -m http.server 8080 --bind 127.0.0.1
```

Open **http://127.0.0.1:8080/**. Stop the server with `Ctrl+C`.

### Windows PowerShell

```powershell
git clone https://github.com/bstBizEra/biztrust_guide.git
Set-Location biztrust_guide
py -m http.server 8080 --bind 127.0.0.1
```

If `py` is unavailable, try `python -m http.server 8080 --bind 127.0.0.1`.

> `http.server` is for trusted local preview only. It is not a production server.

## Agent continuity

Agents must resume from repository evidence, not conversation memory. The mandatory resume order is:

1. Read [`AGENTS.md`](AGENTS.md).
2. Read [`badf/current-state.json`](badf/current-state.json).
3. Read [`badf/next-actions.json`](badf/next-actions.json).
4. Inspect the active work package and latest checkpoint.
5. Verify Git `HEAD`, worktree status and applicable authority.
6. Run `python3 -m unittest discover -s tests`, then `python3 scripts/validate_continuity.py`.
7. Continue only if the resume decision is `CONTINUE`; otherwise stop with the recorded reason.

The complete protocol is documented in [Agent Continuity & Recovery](docs/AGENT_CONTINUITY.md).

## Repository contents

| Path | Purpose |
|---|---|
| `index.html` | The guide's hub — overview, lifecycle map and links to the stage and phase manuals |
| `stages/` | Nine stage manuals — the bulk of the guide |
| `phases/` | Five phase manuals — P0 to production: what agents code and humans monitor per delivery phase. A rendering of `docs/architecture/DELIVERY_PLAN.md`; `tests/test_phase_pages.py` holds its epic and gate identifiers to the plan |
| `reference/` | Two reference pages — the artifact catalogue and the risk-tier schedule: cross-stage lookups that the stage manuals cite rather than restate |
| `tests/` | Validator fail-closed suite and cross-page duplicate detector |
| `sessions/` | Session checkpoints, the recovery procedure's primary input |
| `assets/` | Brand images referenced by every page |
| `styles.css` | Responsive UniTrust/BizTrust visual system |
| `script.js` | Navigation, search, theme and copy controls |
| `AGENTS.md` | Repository-wide agent operating charter |
| `badf/` | Current state, next actions and decision ledger |
| `schemas/` | Machine-checkable continuity contracts |
| `templates/` | Session checkpoint and handoff templates |
| `scripts/` | Deterministic continuity validation |
| `docs/` | Preview, continuity and next-step runbooks |
| `.github/` | Pages deployment and governed work templates |
| `.nojekyll` | Required by the validator and copied into `_site/`, but **it does not reach the published artifact** — `actions/upload-pages-artifact` defaults `include-hidden-files` to `false`, so dotfiles are excluded. GitHub's own static-Pages starter workflow never creates one, because a custom Actions workflow uploads a prebuilt artifact and Jekyll never runs over it. |

## Validate before every handoff

```bash
python3 -m unittest discover -s tests
python3 scripts/validate_continuity.py
node --check script.js
```

CI runs these in this order, then an asset check and an artifact-completeness check. **The suite runs first**: the validator is the instrument every other gate is read through, and an instrument never observed to fail is indistinguishable from one that passed. A handoff passing only the last two commands can still fail CI.

## What the checks actually enforce

Recorded here because none of it was written down, and each is a constraint on anyone changing this repository.

| Mechanism | What it does |
|---|---|
| `tests/test_validator_fails_closed.py` | Proves the validator cannot fail **open**. A malformed artifact must produce exactly one `CONTINUITY_VALIDATION` line and a non-zero exit — never a traceback and silence, which reads as success. |
| `tests/test_no_cross_page_duplication.py` | Fails when one stage page restates another instead of linking to it. Threshold `0.70`. **Re-measured on the current nine-page tree: the highest legitimate pair is 0.692 at element level and 0.615 at sentence level — 0.008 of headroom at element level, which is the binding one.** That margin is not a consequence of the guide growing; it was 0.008 from the moment the element pass existed, and simply went unmeasured because only the sentence pass was reported. Deliberate parallels are allowlisted individually with a reason. **Never raise the threshold**, which retires the check silently; if a legitimate pair crosses it, allowlist that pair and record why. |
| `tests/test_checkpoints_match_schema.py` | Validates every committed checkpoint against `schemas/session-checkpoint.schema.json` with a stdlib checker, and fails if either schema uses a keyword or `format` value the checker does not implement — so a schema edit cannot silently go unenforced. Three checkpoints that predate the check are registered as a ratchet that may only shrink. |
| `.gitattributes` | Pins LF on every file git detects as text, and declares the PNGs binary. The sealed-fixture checks compare bytes, so a checkout that rewrote LF to CRLF failed two tests on a clean tree before this existed. |
| CI *Verify every tracked page reached the artifact* | Fails the build if any tracked `*.html` is missing from `_site/`. Before it existed, a new page could be present in git, pass every check, and 404 in production. |

The validator's exit codes carry meaning: **0** pass · **1** a data defect, the artifacts are wrong · **2** a validator defect, this script is broken · **130** interrupted. A consumer treating any non-zero as failure is correct; 1 and 2 differ so a reader knows which artifact to debug.

## Current delivery state

The guide is nine stage manuals, five phase manuals and two reference pages, plus the `index.html` hub. Documentation actions remain open — see `badf/next-actions.json`.

Deployment state is deliberately not asserted in this file: a status sentence in a page that cannot expire is the defect class issue #32 records, and an earlier version of this paragraph, true when written on 2026-09-02, was merged five minutes after the first deployment had succeeded and then stood for a day. Read deployment state from the two places it actually lives:

- the [Pages workflow runs](https://github.com/bstBizEra/biztrust_guide/actions/workflows/pages.yml) — the run bound to the current `main` head is the evidence that the head was built, validated and uploaded;
- the [`github-pages` environment's deployments](https://api.github.com/repos/bstBizEra/biztrust_guide/deployments?environment=github-pages) — the entry whose latest status (`/deployments/{id}/statuses`, newest first) is `success` is the commit the site is serving; superseded deployments read `inactive`, and a failed newer deployment leaves the previous one live. The API address is used because it answers without a login; the environment's page in the repository UI shows the same record.

The workflow stages every tracked `*.html` — including the `stages/`, `phases/` and `reference/` subtrees — not only the repository root.

## Authoritative references

- [GitHub Pages publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [Python `http.server`](https://docs.python.org/3/library/http.server.html)
- [GitHub Issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/about-issues)
- [GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)
