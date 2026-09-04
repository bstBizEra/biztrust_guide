# `RESUME.json` — sealed schema for WP-024

> **Sealed before any fixture existed.** The schema shapes what an agent can conclude, so
> it has more influence on the experiment's outcome than any individual fixture. Committing
> it alone, ahead of the fixtures, means no fixture could be written to flatter it.

> **Amended after WP-024 ran, under `NS-032` (issue #52 item 2), to `2.0.0`.** `static.repository` became
> required and an observation source may no longer be an unresolved template; the nine fixtures were
> regenerated against the amendment. The sealed `1.0.0` form is at `e37fa3b`. The amendment touches
> neither `resume_decision`, nor `next_action`, nor any oracle — and `build.py` now reads the identity
> rules from this file and refuses a fixture that breaks them, so the schema is enforced, not only declared.

## Why four categories and not one flat object

`badf/current-state.json` is flat, and an audit of the WP-024 proposal showed why that is
the wrong shape. Its 33 leaves divide into four kinds that **expire for different reasons**:

| Category | Expires when | Count in `current-state.json` |
| :--- | :--- | ---: |
| `static` | never | 2 |
| `observed` | the observation ages, or the API was unavailable | 11 |
| `asserted` | its own `valid_until` passes, **or the world it references moves** | 13 |
| `computed` | any input changes | 7 |

A single flat structure gives them one invalidation rule, so either constants expire
needlessly or assertions never do. Both happened in this repository.

## What each category exists to prevent

**`observed` carries per-leaf freshness** so that one unavailable API call cannot silently
downgrade the rest. A `value: null` must be paired with `freshness: UNKNOWN`; the proposal's
own invariant is that an unavailable input degrades to `UNKNOWN` rather than to a guess.

**`asserted` carries `issuer` and `revoked_at`, not just `valid_until`.** Assertions rot
differently from observations: `active_work_package.id` read `WP-017` for a day after WP-017
merged, because a human wrote it and nobody retracted it. A clock would not have caught that
— only a contradicting observation would. An assertion with no issuer cannot be revoked by
anyone, which is why `issuer` is required.

**`computed.next_action` is one object or `null`, never a list.** A list lets the reader
choose, and choosing is the failure this artifact exists to prevent.

**`computed.freshness` is the worst of its critical inputs, never an average.** One `UNKNOWN`
critical observation makes the artifact `UNKNOWN`.

**`source_sha` is separate from `observed.main_sha`** so a reader can compare them. That
comparison is the cheapest staleness check available and needs no clock.

**`declared_non_coverage` is required and non-empty** so that the absence of a stop condition
is never read as the absence of risk.

## What this schema does not do

It does not define **when** each `resume_decision` value applies. This repository has never
specified a complete decision function, and inventing one here would make the experiment test
my rules rather than the artifact's usability. The oracles state the expected decision per
fixture; the schema only fixes the shape.

It also carries no integrity field. A digest stored inside the artifact is signed by the
thing it is meant to check, so integrity lives in the out-of-band manifest.

## Provenance

Sealed under `NS-030`, before fixtures, and amended to `2.0.0` under `NS-032` after WP-024 ran, per
[`WP-024-blind-handoff-preregistration.md`](../WP-024-blind-handoff-preregistration.md) v2.
