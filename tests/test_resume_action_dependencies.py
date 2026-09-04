#!/usr/bin/env python3
"""Issue #52 item 3, enforced: `computed.next_action.requires` names what the action
consumes, per fixture, with no inherited default, and no sealed field moved.

History this module carries. PR #56 added the edge as a constant `["main_sha"]` set once
in build.py's base() and inherited by eight fixtures; on fixture 08 it asserted the action
consumed only a CURRENT input and so pre-decided a label that was still undecided. #57
reverted it. The human record (DEC-026 disposition 5) then required the edge per action,
with no inherited default, every entry naming an existing key, and fixture-specific
positive and negative tests. DEC-033 chose the form: the edge names what the ACTION
consumes; `computed.freshness` stays what the DERIVATION consumed; nothing sealed moves.

So this module proves four things, each a way the last attempt went wrong:

  * no default is inherited     -> base() has no edge, and each fixture function's SOURCE
                                    assigns one (or has no action) as a literal, with a
                                    comment on it. A source test proves placement, not
                                    authorship - a copied line passes it - and a mutant test
                                    proves it refuses the #57 mechanism. Agreement between
                                    fixtures is expected - eight share one action.
  * the edge is enforced         -> build.py reads the shape rules from the schema and
                                    refuses an entry that names no existing key, an empty
                                    edge, a repeated entry, a mis-shaped entry, or an
                                    action with no edge; the CLI exits 1 and writes nothing.
  * per fixture, both ways       -> nine positive tests name their fixture's exact edge;
                                    nine negative tests each break the edge in a way that
                                    only that fixture's observations make possible; generic
                                    shape refusals live in one shared test.
  * nothing sealed moved         -> resume_decision, computed.freshness, stop_conditions
                                    and every oracle.yaml are byte-identical to the 2.0.0
                                    set, pinned here as literals and digests, not read
                                    from git.

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "docs/experiments/fixtures/build.py"
SCHEMA = ROOT / "docs/experiments/schema/resume.schema.json"
FIXTURES = ROOT / "docs/experiments/fixtures"

# Per fixture: the edge its own function assigns (None = no action), and the sealed fields
# as they were in the 2.0.0 set, before item 3. These are LITERALS on purpose, and the edge is
# written out eight times rather than named once: a test that read them from git would pass
# against whatever git held, and a shared constant here would be the one place an edit could
# reach eight fixtures.
EXPECTED: dict[str, dict] = {
    "01-fresh":                  {"fn": "f1", "requires": ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"], "decision": "CONTINUE", "freshness": "CURRENT"},
    "02-main-moved":             {"fn": "f2", "requires": ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"], "decision": "CONTINUE", "freshness": "CURRENT"},
    "03-label-contradicts-merge": {"fn": "f3", "requires": ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"], "decision": "CONTINUE", "freshness": "CURRENT"},
    "04-authority-expired":      {"fn": "f4", "requires": ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"], "decision": "CONTINUE", "freshness": "CURRENT"},
    "05-zero-candidates":        {"fn": "f5", "requires": None, "decision": "COMPLETE", "freshness": "CURRENT"},
    "06-multiple-candidates":    {"fn": "f6", "requires": ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"], "decision": "CONTINUE", "freshness": "CURRENT"},
    "07-conflicting-inputs":     {"fn": "f7", "requires": ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"], "decision": "CONTINUE", "freshness": "CURRENT"},
    "08-api-unavailable":        {"fn": "f8", "requires": ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"], "decision": "CONTINUE", "freshness": "UNKNOWN"},
    "09-tampered-bundle":        {"fn": "f9", "requires": ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"], "decision": "CONTINUE", "freshness": "CURRENT"},
}
# SHA-256 (first 16 hex) of each committed oracle.yaml blob at the 2.0.0 set (main at 83f0d5a),
# taken with `git cat-file -p main:<path> | sha256sum` - from the blob, not a working copy, because
# the first pins were computed on a CRLF checkout and matched nothing committed. The guard below
# hashes the WORKING COPY, so it holds only because .gitattributes (WP-035) pins LF on checkout;
# on a tree without that pin a CRLF checkout would fail it. An oracle that changes under this
# package is a defect; the oracles wait for an independent author.
ORACLE_SHA256 = {
    "01-fresh": "d04a4f264eae3b8b",
    "02-main-moved": "291d305531a667ad",
    "03-label-contradicts-merge": "8ab53508f40583d1",
    "04-authority-expired": "b20b6413eb33722f",
    "05-zero-candidates": "4c3ae0a72cec1773",
    "06-multiple-candidates": "85758c5508dcc99c",
    "07-conflicting-inputs": "51e21d6af31fea59",
    "08-api-unavailable": "079177fe0d3f9104",
    "09-tampered-bundle": "9fde6314ca8aa720",
}


def load_build():
    spec = importlib.util.spec_from_file_location("wp024_build_deps", BUILD)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = previous
    return mod


class TestDeclaration(unittest.TestCase):
    def test_schema_declares_the_edge(self) -> None:
        s = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual("3.0.0", s["properties"]["schema_version"]["const"])
        action = next(o for o in s["properties"]["computed"]["properties"]["next_action"]["oneOf"] if o.get("type") == "object")
        self.assertIn("requires", action["required"])
        req = action["properties"]["requires"]
        self.assertEqual(1, req["minItems"])
        self.assertTrue(req["uniqueItems"])
        self.assertTrue(re.match(req["items"]["pattern"], "asserted.documentation_authority"))
        self.assertFalse(re.match(req["items"]["pattern"], "main_sha"), "a bare key names no category")
        self.assertFalse(re.match(req["items"]["pattern"], "computed.freshness"), "the edge names inputs, not outputs")

    def test_freshness_is_the_derivations_not_the_actions(self) -> None:
        """DEC-033 form (iii): the schema must say freshness is NOT rescoped by requires."""
        s = json.loads(SCHEMA.read_text(encoding="utf-8"))
        text = s["properties"]["computed"]["properties"]["freshness"]["description"]
        self.assertIn("DERIVATION", text)
        self.assertIn("not scoped to next_action.requires", text)


class TestNoInheritedDefault(unittest.TestCase):
    def setUp(self) -> None:
        self.build = load_build()

    def test_base_carries_no_edge(self) -> None:
        action = self.build.base()["computed"]["next_action"]
        self.assertNotIn("requires", action, "the #57 defect: an edge set once in base() reaches every fixture")

    def test_each_fixture_function_assigns_its_own_edge(self) -> None:
        """Read the SOURCE. A fixture that carries an edge it did not assign inherited it."""
        for slug, spec in EXPECTED.items():
            fn = getattr(self.build, spec["fn"])
            src = inspect.getsource(fn)
            with self.subTest(fixture=slug):
                if spec["requires"] is None:
                    self.assertNotIn('["requires"]', src)
                    self.assertIsNone(fn()["computed"]["next_action"])
                else:
                    lines = src.splitlines()
                    hits = [i for i, line in enumerate(lines) if 'd["computed"]["next_action"]["requires"] =' in line]
                    self.assertEqual(1, len(hits), f"{spec['fn']} does not assign its own edge exactly once")
                    i = hits[0]
                    near = lines[i] + (lines[i - 1] if i else "")
                    self.assertIn("#", near, f"{spec['fn']}: no comment on the assignment or the line above it")
                    self.assertNotIn("AUTHORING", src, f"{spec['fn']} names a shared constant")

    def test_the_source_guard_can_fail(self) -> None:
        """Move f1's assignment into base() in a copy of build.py; the guard must go red.

        A test that inspects source proves placement, not authorship: a one-liner copied
        into eight functions passes it. What it does refuse is the #57 mechanism - one
        assignment in base() reaching fixtures that never wrote it - and this proves it can.
        """
        import tempfile
        src = BUILD.read_text(encoding="utf-8")
        assignment = '    d["computed"]["next_action"]["requires"] = ["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"]\n'
        f1_start = src.index("def f1():"); f1_end = src.index("def f2():")
        f1 = src[f1_start:f1_end]
        self.assertIn(assignment, f1)
        mutant = src[:f1_start] + f1.replace(assignment, "") + src[f1_end:]
        mutant = mutant.replace("    for k, v in over.items():", assignment.replace("d[", "d[", 1) + "    for k, v in over.items():", 1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "build.py"; path.write_text(mutant, encoding="utf-8")
            spec = importlib.util.spec_from_file_location("wp024_build_mutant", path)
            mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
            self.assertEqual(["observed.main_sha", "asserted.documentation_authority", "asserted.active_work_package"], mod.f1()["computed"]["next_action"]["requires"],
                             "the mutant must still produce the edge - inherited, not authored")
            self.assertIn("requires", mod.base()["computed"]["next_action"], "the mutant's base() carries the edge")
            self.assertNotIn('d["computed"]["next_action"]["requires"] =', inspect.getsource(mod.f1))


class TestEnforcementReadsTheSchema(unittest.TestCase):
    def setUp(self) -> None:
        self.build = load_build()
        self.rules = self.build.schema_rules()

    def test_rules_are_read_from_the_schema(self) -> None:
        s = json.loads(SCHEMA.read_text(encoding="utf-8"))
        action = next(o for o in s["properties"]["computed"]["properties"]["next_action"]["oneOf"] if o.get("type") == "object")
        self.assertEqual(action["required"], self.rules["action_required"])
        self.assertEqual(action["properties"]["requires"]["items"]["pattern"], self.rules["requires_item_pattern"])
        self.assertEqual(action["properties"]["requires"]["minItems"], self.rules["requires_min_items"])

    def test_enforcement_follows_a_changed_schema(self) -> None:
        """Narrow the pattern to observed.* only in a copy; asserted.* entries must become refused."""
        import tempfile
        original = json.loads(SCHEMA.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            altered = json.loads(json.dumps(original))
            action = next(o for o in altered["properties"]["computed"]["properties"]["next_action"]["oneOf"] if o.get("type") == "object")
            action["properties"]["requires"]["items"]["pattern"] = r"^observed\.[A-Za-z_][A-Za-z0-9_]*$"
            path = Path(tmp) / "resume.schema.json"; path.write_text(json.dumps(altered), encoding="utf-8")
            saved = self.build.SCHEMA
            try:
                self.build.SCHEMA = path
                rules = self.build.schema_rules()
                found = self.build.violations(self.build.f1(), rules)
            finally:
                self.build.SCHEMA = saved
        self.assertTrue(any("asserted.documentation_authority" in v and "pattern" in v for v in found), found)
        self.assertEqual([], self.build.violations(self.build.f1(), self.rules), "the real schema admits the edge")

    def test_missing_edge_is_refused(self) -> None:
        state = self.build.base()   # has an action and no edge
        found = self.build.violations(state, self.rules)
        self.assertTrue(any("requires missing" in v for v in found), found)

    def test_null_action_needs_no_edge(self) -> None:
        self.assertEqual([], self.build.violations(self.build.f5(), self.rules))

    def test_edge_shape_rules(self) -> None:
        cases = {
            "empty":         ([], "fewer than 1"),
            "repeat":        (["observed.main_sha", "observed.main_sha"], "repeats"),
            "bare key":      (["main_sha"], "pattern"),
            "output named":  (["computed.freshness"], "pattern"),
            "not a string":  ([3], "pattern"),
            "not a list":    ("observed.main_sha", "not an array"),
            "trailing newline": (["observed.main_sha\n"], "not a key of"),
        }
        for label, (value, word) in cases.items():
            state = self.build.f1(); state["computed"]["next_action"]["requires"] = value
            with self.subTest(case=label):
                found = self.build.violations(state, self.rules)
                self.assertTrue(any(word in v for v in found), f"{label}: {found}")

    def test_action_object_shape_is_enforced(self) -> None:
        """The rules around the edge - closed key set, string properties - are read too."""
        s = self.build.f1(); s["computed"]["next_action"]["extra"] = 1
        self.assertTrue(any("not a declared key" in v for v in self.build.violations(s, self.rules)))
        s = self.build.f1(); s["computed"]["next_action"]["id"] = 7
        self.assertTrue(any("id is not a string" in v for v in self.build.violations(s, self.rules)))

    def test_entry_must_resolve_to_an_existing_key(self) -> None:
        for entry in ("observed.no_such_key", "asserted.no_such_grant",
                      "observed.documentation_authority",   # right name, wrong category
                      "asserted.main_sha"):
            state = self.build.f1(); state["computed"]["next_action"]["requires"] = [entry]
            with self.subTest(entry=entry):
                found = self.build.violations(state, self.rules)
                self.assertTrue(any("is not a key of" in v for v in found), f"{entry}: {found}")


class TestPerFixturePositive(unittest.TestCase):
    """One method per fixture, deliberately not parametrised: a shared loop could be
    satisfied by one value, and one value reaching all nine is the defect."""

    def setUp(self) -> None:
        self.build = load_build()
        self.rules = self.build.schema_rules()

    def _positive(self, slug: str) -> None:
        spec = EXPECTED[slug]
        state = getattr(self.build, spec["fn"])()
        action = state["computed"]["next_action"]
        if spec["requires"] is None:
            self.assertIsNone(action)
        else:
            self.assertEqual(spec["requires"], action["requires"])
            for entry in action["requires"]:
                category, _, name = entry.partition(".")
                self.assertIn(name, state[category], f"{slug}: {entry} does not resolve")
        self.assertEqual([], self.build.violations(state, self.rules))
        committed = json.loads((FIXTURES / slug / "RESUME.json").read_text(encoding="utf-8"))
        self.assertEqual(state["computed"], committed["computed"], f"{slug}: committed file differs from its source")

    def test_01_fresh(self) -> None: self._positive("01-fresh")
    def test_02_main_moved(self) -> None: self._positive("02-main-moved")
    def test_03_label_contradicts_merge(self) -> None: self._positive("03-label-contradicts-merge")
    def test_04_authority_expired(self) -> None: self._positive("04-authority-expired")
    def test_05_zero_candidates(self) -> None: self._positive("05-zero-candidates")
    def test_06_multiple_candidates(self) -> None: self._positive("06-multiple-candidates")
    def test_07_conflicting_inputs(self) -> None: self._positive("07-conflicting-inputs")
    def test_08_api_unavailable(self) -> None:
        self._positive("08-api-unavailable")
        # The point of the package: the UNKNOWN inputs are NOT in the edge, and freshness is still UNKNOWN.
        state = self.build.f8()
        self.assertEqual("UNKNOWN", state["observed"]["ci_conclusion"]["freshness"])
        self.assertEqual("UNKNOWN", state["observed"]["pages_status"]["freshness"])
        self.assertNotIn("observed.ci_conclusion", state["computed"]["next_action"]["requires"])
        self.assertNotIn("observed.pages_status", state["computed"]["next_action"]["requires"])
        self.assertEqual("UNKNOWN", state["computed"]["freshness"])
    def test_09_tampered_bundle(self) -> None: self._positive("09-tampered-bundle")


class TestPerFixtureNegative(unittest.TestCase):
    """Break each fixture's own edge in a way specific to it; build.py must refuse."""

    def setUp(self) -> None:
        self.build = load_build()
        self.rules = self.build.schema_rules()

    def _refused(self, state: dict, word: str, slug: str) -> None:
        found = self.build.violations(state, self.rules)
        self.assertTrue(any(word in v for v in found), f"{slug}: expected {word!r} in {found}")

    def test_01_fresh_edge_borrows_another_scenarios_observation(self) -> None:
        # issue_2_linked_pr_merged exists only on fixture 03; the control does not observe it.
        s = self.build.f1(); s["computed"]["next_action"]["requires"] = ["observed.issue_2_linked_pr_merged"]
        self._refused(s, "not a key of observed", "01")

    def test_02_main_moved_edge_names_a_key_that_is_not_there(self) -> None:
        s = self.build.f2(); s["computed"]["next_action"]["requires"] = ["observed.main_sha_previous"]
        self._refused(s, "not a key of observed", "02")

    def test_03_label_contradicts_merge_edge_names_the_wrong_category(self) -> None:
        s = self.build.f3(); s["computed"]["next_action"]["requires"] = ["asserted.issue_2_linked_pr_merged"]
        self._refused(s, "not a key of asserted", "03")

    def test_04_authority_expired_grant_withdrawn_from_asserted(self) -> None:
        # The expiring grant is the input this fixture turns on; if it is not asserted at all the edge cannot resolve.
        s = self.build.f4(); del s["asserted"]["documentation_authority"]
        self._refused(s, "not a key of asserted", "04")

    def test_05_zero_candidates_an_action_without_an_edge(self) -> None:
        s = self.build.f5()
        s["computed"]["next_action"] = {"id": "NS-999", "action": "anything", "authority": "none"}
        self._refused(s, "requires missing", "05")

    def test_06_multiple_candidates_edge_removes_the_package(self) -> None:
        s = self.build.f6(); del s["asserted"]["active_work_package"]
        self._refused(s, "not a key of asserted", "06")

    def test_07_conflicting_inputs_edge_names_the_count_under_another_name(self) -> None:
        # This fixture observes open_pull_requests and all_work_merged; a near-miss name must not resolve.
        s = self.build.f7(); s["computed"]["next_action"]["requires"] = ["observed.open_pull_request_count"]
        self._refused(s, "not a key of observed", "07")

    def test_08_api_unavailable_edge_names_the_unavailable_call_by_a_wrong_key(self) -> None:
        # ci_conclusion and pages_status exist (UNKNOWN); pages_build does not. An UNKNOWN key
        # is a legal edge entry - the artifact may say the action needs an input nobody could read.
        s = self.build.f8(); s["computed"]["next_action"]["requires"] = ["observed.ci_conclusion", "observed.pages_build"]
        self._refused(s, "not a key of observed", "08")
        s = self.build.f8(); s["computed"]["next_action"]["requires"] = ["observed.ci_conclusion"]
        self.assertEqual([], self.build.violations(s, self.rules), "an UNKNOWN observation is still a key")

    def test_09_tampered_bundle_edge_names_the_manifest(self) -> None:
        # The manifest is out of band and trusted; it is not an observation in the bundle.
        s = self.build.f9(); s["computed"]["next_action"]["requires"] = ["observed.manifest_digest"]
        self._refused(s, "not a key of observed", "09")


class TestNothingSealedMoved(unittest.TestCase):
    def test_decision_freshness_and_stop_conditions_are_as_sealed(self) -> None:
        for slug, spec in EXPECTED.items():
            c = json.loads((FIXTURES / slug / "RESUME.json").read_text(encoding="utf-8"))["computed"]
            with self.subTest(fixture=slug):
                self.assertEqual(spec["decision"], c["resume_decision"])
                self.assertEqual(spec["freshness"], c["freshness"])
                self.assertEqual([], c["stop_conditions"])

    def test_every_oracle_is_byte_identical(self) -> None:
        for slug, prefix in ORACLE_SHA256.items():
            digest = hashlib.sha256((FIXTURES / slug / "oracle.yaml").read_bytes()).hexdigest()
            with self.subTest(fixture=slug):
                self.assertTrue(digest.startswith(prefix), f"{slug}/oracle.yaml changed: {digest[:16]}")

    def test_nine_and_only_nine(self) -> None:
        self.assertEqual(9, len(EXPECTED))
        self.assertEqual(9, len(ORACLE_SHA256))
        self.assertEqual(9, len(sorted(FIXTURES.glob("*/RESUME.json"))))


class TestTheCommandRefuses(unittest.TestCase):
    """Fixture 08's edge names a key that does not exist; fixture 01 changes benignly.
    Nothing may be written, and the verdict must be SCHEMA=VIOLATION."""

    SNIPPET = (
        "import importlib.util, sys, pathlib\n"
        "spec = importlib.util.spec_from_file_location('b', sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "m.HERE = pathlib.Path(sys.argv[2])\n"
        "def broken():\n"
        "    d = m.f8(); d['computed']['next_action']['requires'] = ['observed.ci_conclusion_yesterday']; return d\n"
        "def moved():\n"
        "    d = m.f1(); d['derived_at'] = '2026-09-05T00:00:00+07:00'; return d\n"
        "m.FIXTURES = [('01-fresh', moved, True)] + list(m.FIXTURES[1:7]) + [('08-api-unavailable', broken, True), m.FIXTURES[8]]\n"
        "sys.exit(m.build(check={check}))\n"
    )

    def setUp(self) -> None:
        import shutil, tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.copy = Path(self._tmp.name) / "fixtures"
        shutil.copytree(FIXTURES, self.copy, ignore=shutil.ignore_patterns("__pycache__"))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, check: bool) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", "-c", self.SNIPPET.format(check=check), str(BUILD), str(self.copy)],
                              capture_output=True, text=True, cwd=ROOT)

    @staticmethod
    def _snapshot(root: Path) -> dict:
        return {p.relative_to(root): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}

    def test_check_mode_refuses_an_unresolvable_edge(self) -> None:
        proc = self._run(check=True)
        self.assertEqual(1, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("SCHEMA=VIOLATION", proc.stdout)
        self.assertIn("08-api-unavailable: computed.next_action.requires names 'observed.ci_conclusion_yesterday'", proc.stdout)
        self.assertNotIn("FIXTURES=CURRENT", proc.stdout)

    def test_write_mode_writes_nothing(self) -> None:
        before = self._snapshot(self.copy)
        proc = self._run(check=False)
        self.assertEqual(1, proc.returncode, proc.stdout + proc.stderr)
        self.assertEqual(before, self._snapshot(self.copy))


if __name__ == "__main__":
    unittest.main(verbosity=2)
