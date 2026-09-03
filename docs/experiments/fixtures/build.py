#!/usr/bin/env python3
"""Materialise the nine WP-024 fixture bundles and compute their manifests.

This is NOT the deriver. Every fixture's content is hand-authored below; this
script only writes the files out and computes byte counts and SHA-256, because
the protocol requires those to be generated mechanically rather than typed.

REVISED after WP-024 failed, per issue #52 items 2 and 3. The fixtures now carry
`static.repository`, fully resolved observation sources, and `next_action.requires`.
The recorded results in WP-024-results.md pertain to the ORIGINAL fixtures sealed
at e37fa3b; these revised ones have never been run.

The frozen HTML is committed as `control-room.html.frozen`, not `.html`. The
validator globs ROOT.rglob("*.html") and the Pages workflow stages
`git ls-files '*.html'`, so a real `.html` here would be link-checked and
PUBLISHED to the live site - including fixture 9, which is deliberately
corrupt. The harness renames on materialisation; the bytes are identical, so
the sealed digest is the digest of what the agent reads.

Usage:  python3 docs/experiments/fixtures/build.py [--check]
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEAL_SHA = "e23143ef91dcf0fd03e1686a1b2880c0696b798d"   # main when fixtures were authored
MOVED_SHA = "aa11bb22cc33dd44ee55ff6600778899aabbccdd"  # a later, different main
EVAL = "2026-09-04T09:00:00+07:00"


REPO = {"owner": "bstBizEra", "name": "biztrust_guide",
        "remote": "https://github.com/bstBizEra/biztrust_guide"}
API = "GET https://api.github.com/repos/bstBizEra/biztrust_guide"


def obs(value, at=EVAL, freshness="CURRENT", source="git rev-parse HEAD"):
    return {"value": value, "observed_at": at, "freshness": freshness, "source": source}


def asrt(value, issuer, effective="2026-09-03T00:00:00+07:00",
         until=None, revoked=None, evidence="operator instruction, recorded in DEC-021"):
    return {"value": value, "issuer": issuer, "effective_at": effective,
            "valid_until": until, "revoked_at": revoked, "evidence": evidence}


def base(**over):
    d = {
        "schema_version": "1.0.0",
        "source_sha": SEAL_SHA,
        "derived_at": EVAL,
        "static": {"project_id": "BIZTRUST-GUIDE", "deriver_policy_version": "0.1.0-fixture",
                   "repository": REPO},
        "observed": {
            "main_sha": obs(SEAL_SHA),
            "open_pull_requests": obs(0, source=f"{API}/pulls?state=open"),
            "ci_conclusion": obs("success", source=f"{API}/commits/{SEAL_SHA}/check-runs"),
            "pages_status": obs("serving", source=f"{API}/pages"),
            "issue_2_state": obs("closed", source=f"{API}/issues/2"),
            "issue_2_labels": obs([], source=f"{API}/issues/2"),
        },
        "asserted": {
            "active_work_package": asrt("BIZTRUST-GUIDE-WP-024", "operator"),
            "documentation_authority": asrt("GRANTED", "operator",
                                            evidence="user request 2026-09-03"),
        },
        "computed": {
            "resume_decision": "CONTINUE",
            "next_action": {"id": "NS-030",
                            "action": "Author and seal the nine WP-024 fixtures and oracles.",
                            "authority": "GRANTED_BY_USER_REQUEST_2026_09_03",
                            "requires": ["main_sha"]},
            "stop_conditions": [],
            "freshness": "CURRENT",
        },
        "declared_non_coverage": [
            "This artifact does not establish that the derivation is correct.",
            "It makes no claim about work not represented in observed or asserted.",
        ],
    }
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(d.get(k), dict):
            d[k] = {**d[k], **v}
        else:
            d[k] = v
    return d


# ---------------------------------------------------------------- fixtures
def f1():
    return base()


def f2():
    d = base()
    d["observed"]["main_sha"] = obs(MOVED_SHA)
    return d   # computed still says CONTINUE - true at derivation, false now


def f3():
    d = base()
    d["observed"]["issue_2_state"] = obs("open", source=f"{API}/issues/2")
    d["observed"]["issue_2_labels"] = obs(["state:in-progress"], source=f"{API}/issues/2")
    d["observed"]["issue_2_linked_pr_merged"] = obs(True, source=f"{API}/pulls/28")
    return d


def f4():
    d = base()
    d["asserted"]["documentation_authority"] = asrt(
        "GRANTED", "operator", until="2026-09-03T23:59:59+07:00",
        evidence="user request 2026-09-03, expiring")
    return d


def f5():
    d = base()
    d["computed"]["next_action"] = None
    d["computed"]["resume_decision"] = "COMPLETE"
    return d


def f6():
    d = base()
    d["asserted"]["active_work_package"] = asrt(
        ["BIZTRUST-GUIDE-WP-024", "BIZTRUST-GUIDE-WP-025"], "operator",
        evidence="two work packages asserted active; the repository permits one")
    return d


def f7():
    d = base()
    d["observed"]["open_pull_requests"] = obs(3, source=f"{API}/pulls?state=open")
    d["observed"]["all_work_merged"] = obs(True, source=f"{API}/pulls?state=open")
    return d


def f8():
    d = base()
    d["observed"]["ci_conclusion"] = obs(None, at=None, freshness="UNKNOWN",
                                         source=f"{API}/commits/{SEAL_SHA}/check-runs - 503")
    d["observed"]["pages_status"] = obs(None, at=None, freshness="UNKNOWN",
                                        source=f"{API}/pages - 503")
    d["computed"]["freshness"] = "UNKNOWN"
    return d


def f9():
    return base()   # content is fine; the MANIFEST will disagree with it


FIXTURES = [
    ("01-fresh", f1, True),
    ("02-main-moved", f2, True),
    ("03-label-contradicts-merge", f3, True),
    ("04-authority-expired", f4, True),
    ("05-zero-candidates", f5, True),
    ("06-multiple-candidates", f6, True),
    ("07-conflicting-inputs", f7, True),
    ("08-api-unavailable", f8, True),
    ("09-tampered-bundle", f9, False),   # False = manifest must NOT match
]

HTML = """<!doctype html>
<meta charset="utf-8">
<title>Delivery state &middot; {slug}</title>
<h1>Delivery state</h1>
<p>Derived from <code>{sha}</code> at <code>{at}</code>.</p>
<p>Decision: <strong>{decision}</strong></p>
<p>Next action: <strong>{action}</strong></p>
<script type="application/json" id="state">
{payload}
</script>
"""


def render(slug: str, state: dict) -> str:
    na = state["computed"]["next_action"]
    return HTML.format(
        slug=slug, sha=state["source_sha"], at=state["derived_at"],
        decision=state["computed"]["resume_decision"],
        action=(na["action"] if na else "NONE_SAFE"),
        payload=json.dumps(state, indent=2, sort_keys=True),
    )


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def build(check: bool) -> int:
    problems = []
    for slug, fn, honest in FIXTURES:
        d = HERE / slug
        d.mkdir(exist_ok=True)
        state = fn()
        rj = (json.dumps(state, indent=2, sort_keys=True) + "\n").encode()
        html = render(slug, state).encode()

        if honest:
            man = {"RESUME.json": {"bytes": len(rj), "sha256": digest(rj)},
                   "control-room.html": {"bytes": len(html), "sha256": digest(html)}}
        else:
            # Fixture 9: the manifest describes a bundle that was not delivered.
            # Byte count AND digest both disagree, so a reader who cannot hash
            # can still detect it - which is why byte counts are in the manifest.
            man = {"RESUME.json": {"bytes": len(rj) + 41, "sha256": digest(rj + b"tampered")},
                   "control-room.html": {"bytes": len(html), "sha256": digest(html)}}

        manifest = ("# Supplied out of band by the harness. TRUSTED.\n"
                    "# The bundle it describes is NOT trusted.\n"
                    f'evaluation_time: "{EVAL}"\nfiles:\n' +
                    "".join(f'  {k}:\n    bytes: {v["bytes"]}\n    sha256: "{v["sha256"]}"\n'
                            for k, v in man.items()))

        targets = {d / "RESUME.json": rj,
                   d / "control-room.html.frozen": html,
                   d / "manifest.yaml": manifest.encode()}
        for path, content in targets.items():
            if check:
                if not path.is_file() or path.read_bytes() != content:
                    problems.append(str(path.relative_to(HERE.parents[2])))
            else:
                path.write_bytes(content)

    if check:
        if problems:
            print("FIXTURES=STALE\n  " + "\n  ".join(problems))
            return 1
        print(f"FIXTURES=CURRENT count={len(FIXTURES)}")
        return 0
    print(f"FIXTURES=WRITTEN count={len(FIXTURES)}")
    return 0


if __name__ == "__main__":
    sys.exit(build("--check" in sys.argv))
