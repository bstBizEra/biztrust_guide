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
