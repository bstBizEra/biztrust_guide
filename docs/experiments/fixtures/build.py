#!/usr/bin/env python3
"""Materialise the nine WP-024 fixture bundles and compute their manifests.

This is NOT the deriver. Every fixture's content is hand-authored below; this
script only writes the files out and computes byte counts and SHA-256, because
the protocol requires those to be generated mechanically rather than typed.

The frozen HTML is committed as `control-room.html.frozen`, not `.html`. The
validator globs ROOT.rglob("*.html") and the Pages workflow stages
`git ls-files '*.html'`, so a real `.html` here would be link-checked and
PUBLISHED to the live site - including fixture 9, which is deliberately
corrupt. The harness renames on materialisation; the bytes are identical, so
the sealed digest is the digest of what the agent reads.

Usage:  python3 docs/experiments/fixtures/build.py [--check]
"""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEAL_SHA = "e23143ef91dcf0fd03e1686a1b2880c0696b798d"   # main when fixtures were authored
MOVED_SHA = "aa11bb22cc33dd44ee55ff6600778899aabbccdd"  # a later, different main
EVAL = "2026-09-04T09:00:00+07:00"

SCHEMA = HERE.parent / "schema" / "resume.schema.json"
# Action dependencies, added under NS-033 (issue #52 item 3, DEC-033 form iii). There is NO shared
# constant and nothing in base(): each fixture function below writes its own three-entry literal and
# says why, so that no single edit can reach eight fixtures. The eight literals agree because the
# action is the same - authoring against a baseline, under a grant, inside a package - and one action
# consumes one set of inputs. The source test checks that each function carries its own assignment
# and a comment on it; it cannot judge whether the comment is true. That judgement is the author's.

# Repository identity, added under NS-032 (issue #52 item 2). Every observation source below is
# RESOLVED against it; the schema refuses an unexpanded template, and this script enforces that
# refusal by reading the rule from the schema - one place, not two.
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
        "schema_version": "3.0.0",
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
                            "authority": "GRANTED_BY_USER_REQUEST_2026_09_03"},
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
    d = base()
    # Control. Local authoring reads the baseline, the grant and the package; nothing else.
    d["computed"]["next_action"]["requires"] = ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"]
    return d


def f2():
    d = base()
    d["observed"]["main_sha"] = obs(MOVED_SHA)
    # The baseline this action authors against is exactly the input that moved.
    d["computed"]["next_action"]["requires"] = ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"]
    return d   # computed still says CONTINUE - true at derivation, false now


def f3():
    d = base()
    d["observed"]["issue_2_state"] = obs("open", source=f"{API}/issues/2")
    d["observed"]["issue_2_labels"] = obs(["state:in-progress"], source=f"{API}/issues/2")
    d["observed"]["issue_2_linked_pr_merged"] = obs(True, source=f"{API}/pulls/28")
    # Issue 2's label and its merged PR contradict each other; authoring fixtures reads neither.
    # The contradiction is a stop condition for the reader, not an input to this action.
    d["computed"]["next_action"]["requires"] = ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"]
    return d


def f4():
    d = base()
    d["asserted"]["documentation_authority"] = asrt(
        "GRANTED", "operator", until="2026-09-03T23:59:59+07:00",
        evidence="user request 2026-09-03, expiring")
    # The grant this action needs is the assertion that expires - named, so the reader need not infer it.
    d["computed"]["next_action"]["requires"] = ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"]
    return d


def f5():
    d = base()
    d["computed"]["next_action"] = None      # no action, so no edge: requires lives on the action
    d["computed"]["resume_decision"] = "COMPLETE"
    return d


def f6():
    d = base()
    d["asserted"]["active_work_package"] = asrt(
        ["BIZTRUST-GUIDE-WP-024", "BIZTRUST-GUIDE-WP-025"], "operator",
        evidence="two work packages asserted active; the repository permits one")
    # The package this action belongs to is the assertion that names two.
    d["computed"]["next_action"]["requires"] = ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"]
    return d


def f7():
    d = base()
    d["observed"]["open_pull_requests"] = obs(3, source=f"{API}/pulls?state=open")
    d["observed"]["all_work_merged"] = obs(True, source=f"{API}/pulls?state=open")
    # Open-PR count and 'all merged' conflict; authoring on a branch consumes neither.
    d["computed"]["next_action"]["requires"] = ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"]
    return d


def f8():
    d = base()
    d["observed"]["ci_conclusion"] = obs(None, at=None, freshness="UNKNOWN",
                                         source=f"{API}/commits/{SEAL_SHA}/check-runs - 503")
    d["observed"]["pages_status"] = obs(None, at=None, freshness="UNKNOWN",
                                        source=f"{API}/pages - 503")
    d["computed"]["freshness"] = "UNKNOWN"   # the DERIVATION consumed ci and pages; the action does not
    # ci_conclusion and pages_status are UNKNOWN and are not in this edge: local authoring
    # needs neither. freshness stays UNKNOWN because it is the derivation's, not the action's.
    d["computed"]["next_action"]["requires"] = ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"]
    return d


def f9():
    d = base()   # content is fine; the MANIFEST will disagree with it
    # The content is the control's, so the edge is the control's: baseline, grant, package.
    d["computed"]["next_action"]["requires"] = ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"]
    return d


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


# ------------------------------------------------------- schema conformance
def schema_rules() -> dict:
    """The identity (item 2) and edge (item 3) rules, read FROM the schema so the declaration and this enforcement
    are one thing. A schema nothing reads is a comment; #56 shipped 241 lines of one.

    Everything the schema can say about identity is read here: the version constant,
    the required keys, the closed key set, the three patterns, the source minimum.
    Two rules JSON Schema cannot express are in violations() as code, and the schema's
    own description names them so a reader of either file sees both."""
    s = json.loads(SCHEMA.read_text(encoding="utf-8"))
    static = s["properties"]["static"]
    repo = static["properties"]["repository"]
    rp = repo["properties"]
    source = s["$defs"]["observation"]["properties"]["source"]
    action = next(o for o in s["properties"]["computed"]["properties"]["next_action"]["oneOf"] if o.get("type") == "object")
    requires = action["properties"]["requires"]
    return {
        "action_required": list(action["required"]),
        "action_keys": list(action["properties"].keys()),
        "action_closed": action.get("additionalProperties") is False,
        "action_string_keys": [k for k, v in action["properties"].items() if v.get("type") == "string"],
        "requires_min_items": int(requires.get("minItems", 0)),
        "requires_unique": bool(requires.get("uniqueItems", False)),
        "requires_item_pattern": requires["items"]["pattern"],
        "schema_version": s["properties"]["schema_version"]["const"],
        "static_required": list(static["required"]),
        "repository_required": list(repo["required"]),
        "repository_keys": list(rp.keys()),
        "repository_closed": repo.get("additionalProperties") is False,
        "owner_pattern": rp["owner"]["pattern"],
        "name_pattern": rp["name"]["pattern"],
        "remote_pattern": rp["remote"]["pattern"],
        "source_min_length": int(source.get("minLength", 0)),
        "unresolved_source": source["not"]["pattern"],
    }


def violations(state: dict, rules: dict) -> list[str]:
    """Every way a state fails the identity and edge rules. Empty means conformant."""
    out: list[str] = []
    if state.get("schema_version") != rules["schema_version"]:
        out.append(f"schema_version {state.get('schema_version')!r} is not the schema's {rules['schema_version']!r}")
    static = state.get("static") if isinstance(state.get("static"), dict) else {}
    for key in rules["static_required"]:
        if key not in static:
            out.append(f"static.{key} missing")
    repo = static.get("repository")
    owner = name = None
    if isinstance(repo, dict):
        if rules["repository_closed"]:
            for key in repo:
                if key not in rules["repository_keys"]:
                    out.append(f"static.repository.{key} is not a declared key")
        for key in rules["repository_required"]:
            if not isinstance(repo.get(key), str) or not repo.get(key):
                out.append(f"static.repository.{key} missing or not a non-empty string")
        owner, name, remote = repo.get("owner"), repo.get("name"), repo.get("remote")
        if isinstance(owner, str) and not re.search(rules["owner_pattern"], owner):
            out.append(f"static.repository.owner {owner!r} does not match the schema pattern")
        if isinstance(name, str) and not re.search(rules["name_pattern"], name):
            out.append(f"static.repository.name {name!r} does not match the schema pattern")
        if isinstance(remote, str):
            if not re.search(rules["remote_pattern"], remote):
                out.append(f"static.repository.remote {remote!r} is not a plain https remote")
            elif isinstance(owner, str) and isinstance(name, str) \
                    and not remote.rstrip("/").endswith(f"/{owner}/{name}"):
                # Cross-field, code-only: JSON Schema cannot say "ends in /owner/name".
                out.append(f"static.repository.remote {remote!r} does not end in /{owner}/{name}")
    elif "repository" in static:
        out.append("static.repository is not an object")
    observed = state.get("observed") if isinstance(state.get("observed"), dict) else {}
    for key, ob in observed.items():
        src = ob.get("source") if isinstance(ob, dict) else None
        if not isinstance(src, str):
            out.append(f"observed.{key}.source missing or not a string")
        elif len(src) < rules["source_min_length"]:
            out.append(f"observed.{key}.source is shorter than minLength {rules['source_min_length']}")
        elif re.search(rules["unresolved_source"], src):
            out.append(f"observed.{key}.source is an unresolved template: {src!r}")
        elif "://" in src and isinstance(owner, str) and isinstance(name, str) \
                and f"/{owner}/{name}" not in src:
            # Cross-field, code-only: a lexical pattern cannot see $OWNER, OWNER/REPO or a
            # different repository. A URL-shaped source must name THIS repository.
            out.append(f"observed.{key}.source is a URL that does not reference /{owner}/{name}: {src!r}")
    # Item 3: the action's edge. Shape rules are read from the schema; resolution is code-only.
    computed = state.get("computed") if isinstance(state.get("computed"), dict) else {}
    action = computed.get("next_action")
    if isinstance(action, dict):
        for key in rules["action_required"]:
            if key not in action:
                out.append(f"computed.next_action.{key} missing")
        if rules["action_closed"]:
            for key in action:
                if key not in rules["action_keys"]:
                    out.append(f"computed.next_action.{key} is not a declared key")
        for key in rules["action_string_keys"]:
            if key in action and not isinstance(action[key], str):
                out.append(f"computed.next_action.{key} is not a string")
        req = action.get("requires")
        if "requires" in action:
            if not isinstance(req, list):
                out.append("computed.next_action.requires is not an array")
            else:
                if len(req) < rules["requires_min_items"]:
                    out.append(f"computed.next_action.requires has fewer than {rules['requires_min_items']} entries")
                if rules["requires_unique"] and len(set(map(str, req))) != len(req):
                    out.append("computed.next_action.requires repeats an entry")
                asserted = state.get("asserted") if isinstance(state.get("asserted"), dict) else {}
                for entry in req:
                    if not isinstance(entry, str) or not re.search(rules["requires_item_pattern"], entry):
                        out.append(f"computed.next_action.requires entry {entry!r} does not match the schema pattern")
                        continue
                    category, _, name = entry.partition(".")
                    # Cross-field, code-only: JSON Schema cannot say "names an existing key".
                    if name not in (observed if category == "observed" else asserted):
                        out.append(f"computed.next_action.requires names {entry!r}, which is not a key of {category}")
    return out


def build(check: bool) -> int:
    rules = schema_rules()
    states = [(slug, fn(), honest) for slug, fn, honest in FIXTURES]
    # Pass 1: every fixture is judged before any is written or certified. A single
    # non-conformant fixture stops the run with nothing written. Judging per fixture
    # inside the write loop wrote eight good fixtures before refusing the ninth and
    # left the tree half-regenerated; a review found it, and this is the fix.
    bad = [f"{slug}: {v}" for slug, state, _honest in states for v in violations(state, rules)]
    if bad:
        print("SCHEMA=VIOLATION\n  " + "\n  ".join(bad))
        return 1
    print(f"SCHEMA=CONFORMANT count={len(states)}")

    problems = []
    for slug, state, honest in states:
        d = HERE / slug
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
        if not check:
            d.mkdir(exist_ok=True)
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
