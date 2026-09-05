# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout: single-context

This repo is single-context. There is no `CONTEXT-MAP.md`.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root (does not exist yet; see below).
- **`docs/adr/`**: read ADRs that touch the area you're about to work in (does not exist yet; see below).
- **`docs/architecture/ADR_REGISTER.md`**: the existing register of BizTrust architecture decisions ADR-001 to ADR-020. None is accepted; each is `DRAFT_REQUIRED` or `BLOCKED_BY_S01`. Read it before proposing any decision so you reuse an existing ADR number rather than inventing a parallel one.
- **`docs/architecture/DOMAIN_MODEL.md`**: the conceptual domain model. It is the glossary of record until `CONTEXT.md` exists.

If `CONTEXT.md` or `docs/adr/` don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## Repo-specific rules for ADRs

- A new ADR file under `docs/adr/` must be registered as a row in `docs/architecture/ADR_REGISTER.md`, and must follow the structure that file requires.
- Writing an ADR does not accept it. Under `AGENTS.md` an ADR moves from `DRAFT_REQUIRED` only through the authority and review process of its Work Package. Never set an ADR's status to accepted yourself.
- Documentation must not claim a capability is implemented, secure, compliant or production-ready unless linked evidence proves it.

## File structure

Single-context repo (this repo):

```
/
├── CONTEXT.md                          ← created lazily by /domain-modeling
├── docs/adr/                           ← created lazily; each file registered in ADR_REGISTER.md
│   └── 0001-<slug>.md
└── docs/architecture/
    ├── ADR_REGISTER.md                 ← existing decision register
    └── DOMAIN_MODEL.md                 ← existing conceptual model
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`, or in `docs/architecture/DOMAIN_MODEL.md` until `CONTEXT.md` exists. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal: either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR or a `PROPOSED_DECISION` in the architecture pack, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders), but worth reopening because…_
