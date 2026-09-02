# BizTrust Agentic Engineer Team Guide

[![Pages](https://github.com/bstBizEra/biztrust_guide/actions/workflows/pages.yml/badge.svg)](https://github.com/bstBizEra/biztrust_guide/actions/workflows/pages.yml)

Enterprise-grade implementation guide for a governed AI engineering team delivering BizTrust from architecture contract through production operations.

## Live website

After GitHub Pages is enabled, the public site is available at:

**https://bstbizera.github.io/biztrust_guide/**

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
6. Run `python3 scripts/validate_continuity.py`.
7. Continue only if the resume decision is `CONTINUE`; otherwise stop with the recorded reason.

The complete protocol is documented in [Agent Continuity & Recovery](docs/AGENT_CONTINUITY.md).

## Repository contents

| Path | Purpose |
|---|---|
| `index.html` | Interactive implementation guide |
| `styles.css` | Responsive UniTrust/BizTrust visual system |
| `script.js` | Navigation, search, theme and copy controls |
| `AGENTS.md` | Repository-wide agent operating charter |
| `badf/` | Current state, next actions and decision ledger |
| `schemas/` | Machine-checkable continuity contracts |
| `templates/` | Session checkpoint and handoff templates |
| `scripts/` | Deterministic continuity validation |
| `docs/` | Preview, continuity and next-step runbooks |
| `.github/` | Pages deployment and governed work templates |

## Validate before every handoff

```bash
python3 scripts/validate_continuity.py
node --check script.js
```

## Current delivery state

The website implementation is complete. The remaining repository-administrator action is to select **GitHub Actions** under `Settings → Pages → Build and deployment → Source`. The included workflow will then publish the root static site.

## Authoritative references

- [GitHub Pages publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [Python `http.server`](https://docs.python.org/3/library/http.server.html)
- [GitHub Issues](https://docs.github.com/en/issues/tracking-your-work-with-issues/about-issues)
- [GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)
