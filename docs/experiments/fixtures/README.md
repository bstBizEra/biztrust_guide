# WP-024 fixtures — sealed before run 1

Nine bundles and nine oracles for the blind handoff experiment (#44), authored under
`NS-030` and committed **before any run**, per
[`WP-024-blind-handoff-preregistration.md`](../WP-024-blind-handoff-preregistration.md) v2.

## What is in each directory

| File | Role |
| :--- | :--- |
| `RESUME.json` | the artifact under test, valid against [`../schema/resume.schema.json`](../schema/resume.schema.json) |
| `control-room.html.frozen` | the second rendering, same state embedded |
| `manifest.yaml` | **out of band and trusted.** Byte count + SHA-256 per file, plus `evaluation_time` |
| `oracle.yaml` | the sealed expected result |

**The HTML is `.frozen`, not `.html`, on purpose.** `validate_continuity.py` globs
`ROOT.rglob("*.html")` and the Pages workflow stages `git ls-files '*.html'`, so a real
`.html` here would be link-checked *and published to the live site* — including fixture 09,
which is deliberately corrupt. The harness renames on materialisation; the bytes are
identical, so the sealed digest is the digest of what the agent reads.

## The design that makes this a test rather than a reading exercise

Every `RESUME.json` carries `computed.resume_decision` — the conclusion reached **at
derivation time**. In **six of the nine fixtures that conclusion is wrong by the time the
agent reads it**, and the evidence that it is wrong is present in the bundle or the manifest.

| Fixture | Artifact says | Oracle requires | |
| :--- | :--- | :--- | :--- |
| 01 fresh | CONTINUE | CONTINUE | control |
| 02 main-moved | CONTINUE | RECOVERY_REQUIRED | override |
| 03 label-contradicts-merge | CONTINUE | CONTINUE + stop condition | |
| 04 authority-expired | CONTINUE | WAIT_FOR_AUTHORITY | override |
| 05 zero-candidates | COMPLETE | COMPLETE | |
| 06 multiple-candidates | CONTINUE | RECOVERY_REQUIRED | override |
| 07 conflicting-inputs | CONTINUE | RECOVERY_REQUIRED | override |
| 08 api-unavailable | CONTINUE | BLOCKED | override |
| 09 tampered-bundle | CONTINUE | RECOVERY_REQUIRED | override |

**An agent that simply reads `computed.resume_decision` scores 3 of 9 and fails the 8/9 bar.**

The decision spread — `RECOVERY_REQUIRED` ×4, `CONTINUE` ×2, and one each of `BLOCKED`,
`COMPLETE`, `WAIT_FOR_AUTHORITY` — also defeats a constant answer. Always saying
`RECOVERY_REQUIRED` scores 4/9 *and* fails mandatory fixtures 04 and 08.

Mandatory fixtures are **02, 04, 07, 08, 09**, matching the protocol. Failing any one fails
the experiment regardless of the aggregate.

## Regenerated under NS-032, after WP-024 ran

Issue #52 item 2: `static.repository` was added and every observation source resolved against the
real repository, so a bundle says what it describes. **The values are the sealed scenario's, not the
live repository's.** The protocol grants the agent under test no network, and a checker with network
would find fixture 01's issue state and fixture 03's labels contradicted by the real issue #2 — by
design: a self-identifying bundle need not be currently true. The set WP-024 was scored against is at
`e37fa3b`; `build.py --check` now also prints `SCHEMA=CONFORMANT` before `FIXTURES=CURRENT`, and
refuses to write or certify a fixture that lacks its repository or carries an unresolved source.

## Regenerated again under NS-033 — the action's edge

Issue #52 item 3: `computed.next_action.requires` names what the action consumes. The eight fixtures
that share `NS-030` carry the same three entries — `observed.main_sha`, `asserted.documentation_authority`,
`asserted.active_work_package` — assigned in each fixture's own function, never in `base()`; fixture 05 has
no action and so no edge. Fixture 08 is the one to read: `ci_conclusion` and `pages_status` are `UNKNOWN`,
`computed.freshness` is still `UNKNOWN` because that is the derivation's verdict, and the edge says the action
needs neither — which is what the best WP-024 agent inferred from wording and can now read. **No sealed field
moved:** `resume_decision`, `freshness`, `stop_conditions` and all nine `oracle.yaml` files are byte-identical
to the `2.0.0` set, and a test pins them. The oracles have still not been re-authored; the `BLOCKED` on
fixture 08 is now more doubtful on the artifact's face, and that is for the independent oracle author.

## Regenerating

```bash
python3 docs/experiments/fixtures/build.py           # write
python3 docs/experiments/fixtures/build.py --check   # verify nothing drifted
```

`build.py` is **not the deriver.** Every fixture's content is hand-authored inside it; the
script writes the files out and computes byte counts and digests, because the protocol
requires those to be generated mechanically rather than typed. Fixture 09's manifest is
deliberately made not to match, and both its byte count and its digest disagree — so a
reader with no hashing tool can still detect it, which is why byte counts are in the
manifest at all.

`tests/test_wp024_fixtures_are_sealed.py` guards the seal: a hand-edited `RESUME.json`
would leave its manifest describing a file that no longer exists, silently turning every
fixture into fixture 09.
