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
    "GET https://host.example:8080/health",                     # a colon that is not a path parameter
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
        """Disposition 4: item 2 lands alone. A `requires` key here is item 3 smuggled in."""
        for p in sorted(FIXTURES.glob("*/RESUME.json")):
            na = json.loads(p.read_text(encoding="utf-8"))["computed"]["next_action"]
            with self.subTest(fixture=p.parent.name):
                self.assertNotIn("requires", na or {})

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
    """Verify by invoking the command, not by importing the function."""

    SNIPPET = (
        "import importlib.util, sys\n"
        "spec = importlib.util.spec_from_file_location('b', sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "m.REPO.pop('remote')\n"           # every generated fixture now lacks its remote
        "sys.exit(m.build(check={check}))\n"
    )

    def _run(self, check: bool) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", "-c", self.SNIPPET.format(check=check), str(BUILD)],
                              capture_output=True, text=True, cwd=ROOT)

    def test_build_refuses_a_fixture_without_repository(self) -> None:
        proc = self._run(check=True)
        self.assertEqual(1, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("SCHEMA=VIOLATION", proc.stdout)
        self.assertIn("static.repository.remote missing", proc.stdout)
        self.assertNotIn("FIXTURES=CURRENT", proc.stdout, "a violation must not be certified current")

    def test_write_mode_writes_nothing_when_non_conformant(self) -> None:
        before = {p: p.read_bytes() for p in FIXTURES.glob("*/*") if p.is_file()}
        proc = self._run(check=False)
        self.assertEqual(1, proc.returncode, proc.stdout + proc.stderr)
        self.assertNotIn("FIXTURES=WRITTEN", proc.stdout)
        after = {p: p.read_bytes() for p in FIXTURES.glob("*/*") if p.is_file()}
        self.assertEqual(before, after, "write mode changed a file while the state was non-conformant")

    def test_the_committed_tree_is_certified(self) -> None:
        proc = subprocess.run([sys.executable, "-B", str(BUILD), "--check"], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("SCHEMA=CONFORMANT count=9", proc.stdout)
        self.assertIn("FIXTURES=CURRENT count=9", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
