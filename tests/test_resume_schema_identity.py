#!/usr/bin/env python3
"""Issue #52 item 2, enforced: a RESUME.json says which repository it describes, and
every observation source is resolved.

WP-024's control fixture failed for one reason: its sources read `GET /repos/:o/:r/...`
and nine of nine agents refused to trust a bundle that could not name its subject. PR #56
answered with 241 lines of schema that nothing read - `build.py --check` compares bytes,
and no code in this repository loads resume.schema.json - so the "guard" it described was
a comment. It also let `{owner}/{repo}` and `:owner/:repo` through.

This module tests the enforcement, not the declaration. `build.py` reads the two item-2
rules FROM the schema (`schema_rules()`), applies them to every generated fixture
(`violations()`), and refuses to write or certify a non-conformant one. So:

  * the schema declares the rule            -> test_schema_declares_the_rules
  * build.py enforces exactly that rule     -> test_rules_are_read_from_the_schema
  * the rule fires on each escapee          -> test_each_placeholder_form_is_refused
  * the rule stays quiet on resolved input  -> test_resolved_sources_are_accepted
  * the CLI exits 1 and writes nothing      -> test_build_refuses_a_fixture_without_repository

Item 3 (`next_action.requires`) is NOT here, by DEC-026 disposition 4: the two land
separately. No oracle is read or written by this module or by the change it guards.

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "docs/experiments/fixtures/build.py"
SCHEMA = ROOT / "docs/experiments/schema/resume.schema.json"
FIXTURES = ROOT / "docs/experiments/fixtures"


def load_build():
    """Import build.py without writing bytecode beside it.

    exec_module writes docs/experiments/fixtures/__pycache__/ by default, which is a
    TENTH directory under fixtures/ and fails the sealed-fixtures test's count of nine.
    Found on the first full-suite run of this module; the subprocess tests already
    pass -B for the same reason.
    """
    spec = importlib.util.spec_from_file_location("wp024_build", BUILD)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = previous
    return mod


ESCAPEES = (
    "GET /repos/:o/:r/pulls?state=open",                       # the WP-024 control's own text
    "GET /repos/:o/:r/commits/:sha/check-runs - 503",           # fixture 08's, with the suffix
    "GET /repos/:owner/:repo/issues/2",                         # let through by #56's guard
    "GET /repos/{owner}/{repo}/issues/2",                       # let through by #56's guard
    "GET /repos/<owner>/<repo>/pages",
)
RESOLVED = (
    "git rev-parse HEAD",
    "GET https://api.github.com/repos/bstBizEra/biztrust_guide/pulls?state=open",
    "GET https://api.github.com/repos/bstBizEra/biztrust_guide/commits/e23143ef91dcf0fd03e1686a1b2880c0696b798d/check-runs - 503",
    "GET https://git.example:8443/bstBizEra/biztrust_guide/-/pipelines",   # a port is not a path parameter
    "search/issues?q=repo:bstBizEra/biztrust_guide+is:open",              # colons that are not parameters
)
# Unresolved or wrong sources a lexical pattern cannot see. Refused by the cross-field rule:
# a URL-shaped source must reference /owner/name of static.repository.
URL_ESCAPEES = (
    "GET https://api.github.com/repos/$OWNER/$REPO/pulls",
    "GET https://api.github.com/repos/OWNER/REPO/pulls",
    "GET https://api.github.com/repos/[owner]/[repo]/pulls",
    "GET https://api.github.com/repos/%7Bowner%7D/%7Brepo%7D/pulls",
    "GET https://api.github.com/repos/someone/else/pulls",              # a different repository entirely
)


class TestDeclaration(unittest.TestCase):
    def test_schema_declares_the_rules(self) -> None:
        s = json.loads(SCHEMA.read_text(encoding="utf-8"))
        static = s["properties"]["static"]
        self.assertIn("repository", static["required"])
        repo = static["properties"]["repository"]
        self.assertEqual(["owner", "name", "remote"], repo["required"])
        self.assertTrue(repo["properties"]["remote"]["pattern"].startswith("^https://"))
        source = s["$defs"]["observation"]["properties"]["source"]
        self.assertIn("not", source, "source must carry the refusal pattern")
        self.assertIn("pattern", source["not"])


class TestEnforcementReadsTheSchema(unittest.TestCase):
    def setUp(self) -> None:
        self.build = load_build()
        self.rules = self.build.schema_rules()

    def test_rules_are_read_from_the_schema(self) -> None:
        """One source of truth. If someone edits the schema's pattern, build.py follows."""
        s = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(s["$defs"]["observation"]["properties"]["source"]["not"]["pattern"],
                         self.rules["unresolved_source"])
        self.assertEqual(s["properties"]["static"]["properties"]["repository"]["properties"]["remote"]["pattern"],
                         self.rules["remote_pattern"])
        self.assertEqual(s["properties"]["static"]["required"], self.rules["static_required"])

    def test_generated_fixtures_conform(self) -> None:
        for slug, fn, _honest in self.build.FIXTURES:
            with self.subTest(fixture=slug):
                self.assertEqual([], self.build.violations(fn(), self.rules))

    def test_committed_fixtures_conform(self) -> None:
        paths = sorted(FIXTURES.glob("*/RESUME.json"))
        self.assertEqual(9, len(paths), "the protocol fixes the count at nine")
        for p in paths:
            with self.subTest(fixture=p.parent.name):
                self.assertEqual([], self.build.violations(json.loads(p.read_text(encoding="utf-8")), self.rules))

    def test_no_fixture_carries_item_three(self) -> None:
        """Disposition 4: item 2 lands alone. A `requires` key ANYWHERE is item 3 smuggled in."""
        paths = sorted(FIXTURES.glob("*/RESUME.json"))
        self.assertEqual(9, len(paths), "an empty glob must not pass this vacuously")
        for p in paths:
            with self.subTest(fixture=p.parent.name):
                self.assertNotIn('"requires"', p.read_text(encoding="utf-8"))

    def test_missing_repository_is_refused(self) -> None:
        state = self.build.base()
        del state["static"]["repository"]
        found = self.build.violations(state, self.rules)
        self.assertTrue(any("static.repository missing" in v for v in found), found)

    def test_empty_owner_and_http_remote_are_refused(self) -> None:
        state = self.build.base()
        state["static"]["repository"] = {"owner": "", "name": "x", "remote": "http://github.com/a/b"}
        found = self.build.violations(state, self.rules)
        self.assertTrue(any("owner" in v for v in found), found)
        self.assertTrue(any("https" in v for v in found), found)

    def test_url_sources_must_name_this_repository(self) -> None:
        """The lexical pattern enumerates three template syntaxes; this rule needs none."""
        for src in URL_ESCAPEES:
            state = self.build.base()
            state["observed"]["issue_2_state"] = self.build.obs("closed", source=src)
            with self.subTest(source=src):
                found = self.build.violations(state, self.rules)
                self.assertTrue(any("does not reference /bstBizEra/biztrust_guide" in v for v in found), f"{src!r} was accepted")

    def test_remote_must_end_in_owner_and_name(self) -> None:
        state = self.build.base()
        state["static"]["repository"] = {"owner": "microsoft", "name": "vscode", "remote": "https://evil.example/x/y"}
        found = self.build.violations(state, self.rules)
        self.assertTrue(any("does not end in /microsoft/vscode" in v for v in found), found)

    def test_declared_shape_rules_are_enforced(self) -> None:
        """Every rule the schema declares about identity is read and applied - not a subset."""
        cases = {
            "owner pattern":   ({"owner": "-bad owner", "name": "x", "remote": "https://github.com/-bad owner/x"}, "owner"),
            "name pattern":    ({"owner": "a", "name": "a b", "remote": "https://github.com/a/a b"}, "name"),
            "owner type":      ({"owner": 123, "name": "x", "remote": "https://github.com/123/x"}, "owner"),
            "extra key":       ({"owner": "a", "name": "b", "remote": "https://github.com/a/b", "extra": 1}, "extra"),
            "token in remote": ({"owner": "a", "name": "b", "remote": "https://user:TOKEN@github.com/a/b"}, "remote"),
        }
        for label, (repo, word) in cases.items():
            state = self.build.base(); state["static"]["repository"] = repo
            with self.subTest(case=label):
                found = self.build.violations(state, self.rules)
                self.assertTrue(any(word in v for v in found), f"{label}: {found}")
        state = self.build.base(); state["observed"]["issue_2_state"] = {"value": 1, "observed_at": None, "freshness": "UNKNOWN", "source": 123}
        self.assertTrue(any("not a string" in v for v in self.build.violations(state, self.rules)))
        state = self.build.base(); state["schema_version"] = "1.0.0"
        self.assertTrue(any("schema_version" in v for v in self.build.violations(state, self.rules)))

    def test_enforcement_follows_a_changed_schema(self) -> None:
        """Proves the enforcer READS the file, not that two strings agree at one instant.

        The first version of this module compared the schema to build.py's read of the
        same schema, which passed with the pattern hard-coded in violations(). Here the
        schema is swapped for a copy with a different pattern, and the verdict must move
        in both directions. Found by review; recorded so it is not simplified away.
        """
        import tempfile
        original = json.loads(SCHEMA.read_text(encoding="utf-8"))
        source = self.build.obs("closed", source="GET /repos/:owner/:repo/pulls")     # refused today
        fine = self.build.obs("closed", source="git log -1")                            # accepted today
        with tempfile.TemporaryDirectory() as tmp:
            for pattern, probe, expect_refused in ((r"(NEVER-MATCHES-ANYTHING)", source, False),
                                                   (r"(git log)", fine, True)):
                altered = json.loads(json.dumps(original))
                altered["$defs"]["observation"]["properties"]["source"]["not"]["pattern"] = pattern
                path = Path(tmp) / "resume.schema.json"; path.write_text(json.dumps(altered), encoding="utf-8")
                saved = self.build.SCHEMA
                try:
                    self.build.SCHEMA = path
                    rules = self.build.schema_rules()
                    state = self.build.base(); state["observed"]["probe"] = probe
                    refused = any("unresolved template" in v for v in self.build.violations(state, rules))
                finally:
                    self.build.SCHEMA = saved
                with self.subTest(pattern=pattern):
                    self.assertEqual(expect_refused, refused, "build.py did not follow the schema it was pointed at")

    def test_each_placeholder_form_is_refused(self) -> None:
        for src in ESCAPEES:
            state = self.build.base()
            state["observed"]["issue_2_state"] = self.build.obs("closed", source=src)
            with self.subTest(source=src):
                found = self.build.violations(state, self.rules)
                self.assertTrue(any("unresolved template" in v for v in found), f"{src!r} was accepted")

    def test_resolved_sources_are_accepted(self) -> None:
        for src in RESOLVED:
            state = self.build.base()
            state["observed"]["issue_2_state"] = self.build.obs("closed", source=src)
            with self.subTest(source=src):
                self.assertEqual([], self.build.violations(state, self.rules))


class TestTheCommandRefuses(unittest.TestCase):
    """Verify by invoking the command, not by importing the function.

    The build runs against a TEMP COPY of the fixtures directory (argv[2] -> m.HERE).
    The first version of the write-refusal test ran it against the real directory and
    relied on the code under test refusing to write - which is the property under test.
    When a mutant did write, it corrupted fixture 01 on disk and the next --check was
    STALE. A test that damages the tree when it fails is a test nobody can run twice.
    """

    # Break ONE fixture (08 loses its repository) and change ANOTHER benignly (01's derived_at),
    # so a build that judged per fixture would write 01 before refusing 08. Nothing may be written.
    SNIPPET = (
        "import importlib.util, sys, pathlib\n"
        "spec = importlib.util.spec_from_file_location('b', sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "m.HERE = pathlib.Path(sys.argv[2])\n"
        "def broken():\n"
        "    d = m.f8(); del d['static']['repository']; return d\n"
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

    def test_build_refuses_a_fixture_without_repository(self) -> None:
        proc = self._run(check=True)
        self.assertEqual(1, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("SCHEMA=VIOLATION", proc.stdout)
        self.assertIn("08-api-unavailable: static.repository missing", proc.stdout)
        self.assertNotIn("FIXTURES=CURRENT", proc.stdout, "a violation must not be certified current")

    def test_write_mode_writes_nothing_when_non_conformant(self) -> None:
        real_before = self._snapshot(FIXTURES)
        before = self._snapshot(self.copy)
        proc = self._run(check=False)
        self.assertEqual(1, proc.returncode, proc.stdout + proc.stderr)
        self.assertNotIn("FIXTURES=WRITTEN", proc.stdout)
        after = self._snapshot(self.copy)
        self.assertEqual(before, after, "write mode changed a file while another fixture was non-conformant")
        self.assertEqual(real_before, self._snapshot(FIXTURES), "the real fixtures directory must never be touched by this test")

    def test_the_committed_tree_is_certified(self) -> None:
        proc = subprocess.run([sys.executable, "-B", str(BUILD), "--check"], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("SCHEMA=CONFORMANT count=9", proc.stdout)
        self.assertIn("FIXTURES=CURRENT count=9", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
