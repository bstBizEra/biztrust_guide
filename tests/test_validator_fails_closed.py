#!/usr/bin/env python3
"""Prove the continuity validator fails CLOSED.

Every case here traces to a defect found in review of BIZTRUST-GUIDE-WP-005.
Two of them (EMPTY_ACTIONS, EMPTY_CHECKPOINT) produced
`CONTINUITY_VALIDATION=PASS` with exit 0 while every continuity check was
silently skipped - a clean verdict that established nothing.

The tests run the validator as a SUBPROCESS against a COPY of the repository.
Nothing here writes to the working tree. Stdlib only; no pytest required:

    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STATE = "badf/current-state.json"
ACTIONS = "badf/next-actions.json"


class ValidatorHarness(unittest.TestCase):
    """Copy the repo, mutate one thing, run the validator, read the verdict."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "repo"
        shutil.copytree(
            REPO, self.root,
            ignore=shutil.ignore_patterns(".git", "_site", "node_modules", "__pycache__"),
        )
        self.addCleanup(self._tmp.cleanup)

    # -- helpers -------------------------------------------------------

    def run_validator(self) -> tuple[int, list[str], str]:
        proc = subprocess.run(
            [sys.executable, "-B", str(self.root / "scripts/validate_continuity.py")],
            capture_output=True, text=True, timeout=120,
        )
        return proc.returncode, proc.stdout.splitlines(), proc.stderr

    def verdicts(self, out: list[str]) -> list[str]:
        return [line for line in out if line.startswith("CONTINUITY_VALIDATION=")]

    def load(self, relative: str) -> dict:
        return json.loads((self.root / relative).read_text(encoding="utf-8"))

    def save(self, relative: str, document: object) -> None:
        (self.root / relative).write_text(json.dumps(document, indent=2), encoding="utf-8")

    def checkpoint_path(self) -> str:
        return self.load(STATE)["latest_checkpoint"]

    def assert_fails_closed(self, expect_substring: str = "", expect_code: int = 1) -> str:
        """A failure must be: exactly one verdict, FAIL, non-zero, no stdout traceback."""
        code, out, _err = self.run_validator()
        verdicts = self.verdicts(out)
        joined = "\n".join(out)
        self.assertEqual(len(verdicts), 1, f"expected exactly one verdict line, got {verdicts}")
        self.assertEqual(verdicts[0], "CONTINUITY_VALIDATION=FAIL", joined)
        self.assertEqual(code, expect_code, f"exit code; stdout was:\n{joined}")
        self.assertNotIn("Traceback", joined, "traceback must not pollute the verdict channel")
        if expect_substring:
            self.assertIn(expect_substring, joined)
        return joined


class TestBaselineIsGreen(ValidatorHarness):
    def test_unmutated_copy_passes(self) -> None:
        """The control. If this fails, every negative case below is meaningless."""
        code, out, _ = self.run_validator()
        self.assertEqual(self.verdicts(out), ["CONTINUITY_VALIDATION=PASS"], "\n".join(out))
        self.assertEqual(code, 0)


class TestFailsOpenRegressions(ValidatorHarness):
    """These two printed PASS with exit 0 before the fix."""

    def test_empty_actions_document_is_not_a_pass(self) -> None:
        self.save(ACTIONS, {})
        self.assert_fails_closed("badf/next-actions.json: document is empty")

    def test_empty_checkpoint_document_is_not_a_pass(self) -> None:
        self.save(self.checkpoint_path(), {})
        self.assert_fails_closed("checkpoint document is empty")

    def test_skipped_check_cannot_yield_a_pass(self) -> None:
        """Even with a wrong work-package id, an empty actions file must not pass."""
        state = self.load(STATE)
        state["active_work_package"]["id"] = "TOTALLY-WRONG-WP-999"
        state["primary_next_action_id"] = "DOES-NOT-EXIST"
        self.save(STATE, state)
        self.save(ACTIONS, {})
        joined = self.assert_fails_closed()
        self.assertIn("check did not run: continuity-actions", joined)


class TestWrongTypesAreRecordedNotRaised(ValidatorHarness):
    def test_recovery_as_string(self) -> None:
        chk = self.load(self.checkpoint_path())
        chk["recovery"] = "just a sentence"
        self.save(self.checkpoint_path(), chk)
        self.assert_fails_closed("checkpoint.recovery: expected an object, found str")

    def test_baseline_commit_as_integer(self) -> None:
        state = self.load(STATE)
        state["source"]["baseline_commit"] = 42
        self.save(STATE, state)
        self.assert_fails_closed("baseline_commit is not a 40-character SHA")

    def test_baseline_commit_as_null(self) -> None:
        """.get(key, '') does NOT fall back when the key exists holding null."""
        state = self.load(STATE)
        state["source"]["baseline_commit"] = None
        self.save(STATE, state)
        self.assert_fails_closed("baseline_commit is not a 40-character SHA")

    def test_source_as_null_names_the_right_field(self) -> None:
        state = self.load(STATE)
        state["source"] = None
        self.save(STATE, state)
        self.assert_fails_closed("current-state.source: expected an object, found nothing")

    def test_action_id_unhashable(self) -> None:
        actions = self.load(ACTIONS)
        actions["actions"][0]["id"] = ["NS-011"]
        self.save(ACTIONS, actions)
        self.assert_fails_closed("have a non-string id")

    def test_priority_mixed_types_does_not_raise(self) -> None:
        actions = self.load(ACTIONS)
        actions["actions"][0]["priority"] = "1"
        self.save(ACTIONS, actions)
        self.assert_fails_closed("positive integer priority")

    def test_decision_log_id_unhashable(self) -> None:
        log = self.root / "badf/decision-log.jsonl"
        log.write_text(
            log.read_text(encoding="utf-8") + json.dumps({"id": ["D-999"]}) + "\n",
            encoding="utf-8",
        )
        self.assert_fails_closed("id must be a non-empty string")

    def test_latest_checkpoint_as_object(self) -> None:
        state = self.load(STATE)
        state["latest_checkpoint"] = {"path": "x"}
        self.save(STATE, state)
        self.assert_fails_closed("latest_checkpoint must be a string path")

    def test_action_row_not_an_object(self) -> None:
        actions = self.load(ACTIONS)
        actions["actions"][0] = "not an object"
        self.save(ACTIONS, actions)
        self.assert_fails_closed("are not objects")


class TestUnreadableInputs(ValidatorHarness):
    def test_invalid_utf8_is_reported_not_raised(self) -> None:
        """UnicodeDecodeError is a ValueError, not a JSONDecodeError."""
        (self.root / STATE).write_bytes(b'{"a": "\xff\xfe"}')
        self.assert_fails_closed("cannot load valid JSON")

    def test_directory_named_like_a_page_is_ignored(self) -> None:
        """rglob('*.html') matches DIRECTORIES; read_text on one raises.

        This asserts the exact outcome, not "either is fine". The earlier
        version accepted both 0 and 1, so it passed against the unfixed
        validator for the wrong reason and could not fail when the is_file()
        filter was removed.
        """
        before_code, before_out, _ = self.run_validator()
        self.assertEqual(before_code, 0)
        pages_before = [l for l in before_out if l.startswith("PASS: html-pages:")]

        (self.root / "trap.html").mkdir()
        code, out, _ = self.run_validator()
        self.assertEqual(self.verdicts(out), ["CONTINUITY_VALIDATION=PASS"], "\n".join(out))
        self.assertEqual(code, 0)
        self.assertNotIn("Traceback", "\n".join(out))
        pages_after = [l for l in out if l.startswith("PASS: html-pages:")]
        self.assertEqual(pages_before, pages_after, "a directory must not change the page count")

    def test_unparseable_href_is_reported_not_raised(self) -> None:
        """urlsplit raises ValueError on '//[' - reachable from hand-written HTML."""
        page = self.root / "stages/architect.html"
        page.write_text(
            page.read_text(encoding="utf-8").replace(
                '<a class="skip" href="#main">', '<a class="skip" href="//[">', 1
            ),
            encoding="utf-8",
        )
        self.assert_fails_closed("unparseable")


class TestVerdictChannelDiscipline(ValidatorHarness):
    def test_unforeseen_exception_exits_two_and_keeps_traceback_off_stdout(self) -> None:
        """A validator defect and a data defect must be distinguishable."""
        script = self.root / "scripts/validate_continuity.py"
        script.write_text(
            script.read_text(encoding="utf-8").replace(
                "def main() -> int:",
                "def main() -> int:\n    raise RuntimeError('injected control')",
                1,
            ),
            encoding="utf-8",
        )
        code, out, err = self.run_validator()
        self.assertEqual(self.verdicts(out), ["CONTINUITY_VALIDATION=FAIL"])
        self.assertEqual(code, 2, "validator defect must not be exit 1 like a data defect")
        self.assertNotIn("Traceback", "\n".join(out), "stdout is the verdict channel")
        self.assertIn("Traceback", err, "stderr must keep the diagnosis")
        self.assertIn("injected control", err)


class TestContentPresence(ValidatorHarness):
    """A check that runs against nothing must not report PASS.

    These two passed on the pre-fix validator AND on main: the html-pages
    token was appended unconditionally, so the "check did not run" assertion
    could never fire for it.
    """

    def test_gutted_site_is_not_a_pass(self) -> None:
        # rglob, not stages/*.html. When `reference/` was added the narrow glob
        # left two pages standing, so their local links kept total_refs above
        # zero and the assertion below could not fire - the site was not gutted
        # and the test said nothing while still passing for the first clause.
        # The premise is "no page has any content", so it must reach every page
        # wherever a future one is filed.
        index = (self.root / "index.html").resolve()
        for page in self.root.rglob("*.html"):
            if page.is_file() and page.resolve() != index:
                page.unlink()
        (self.root / "index.html").write_text("", encoding="utf-8")
        joined = self.assert_fails_closed("index.html is present but empty")
        self.assertIn("the link check validated nothing", joined)

    def test_empty_index_is_not_a_pass(self) -> None:
        (self.root / "index.html").write_text("", encoding="utf-8")
        self.assert_fails_closed("index.html is present but empty")


class TestGuardsWithoutCoverage(ValidatorHarness):
    """Behaviours that survived mutation testing undetected."""

    def test_latest_checkpoint_with_null_byte(self) -> None:
        state = self.load(STATE)
        state["latest_checkpoint"] = "sessions/\x00evil.json"
        self.save(STATE, state)
        # Discriminate on the message UNIQUE to this guard. Asserting the
        # bare phrase "null byte" passes even with the guard removed, because
        # resolve() then raises ValueError("embedded null byte") and the
        # generic handler reports it - a test matching something adjacent to
        # what it is testing.
        self.assert_fails_closed("latest_checkpoint contains a null byte")

    def test_latest_checkpoint_escaping_the_repository(self) -> None:
        state = self.load(STATE)
        state["latest_checkpoint"] = "../../../../etc/hostname"
        self.save(STATE, state)
        self.assert_fails_closed("escapes the repository root")

    def test_boolean_priority_is_not_an_integer(self) -> None:
        """True is an int in Python. A priority of true must still be rejected."""
        actions = self.load(ACTIONS)
        actions["actions"][0]["priority"] = True
        self.save(ACTIONS, actions)
        self.assert_fails_closed("positive integer priority")

    def test_wrong_schema_dialect_withholds_the_check(self) -> None:
        path = "schemas/session-checkpoint.schema.json"
        schema = self.load(path)
        schema["$schema"] = "https://json-schema.org/draft-07/schema#"
        self.save(path, schema)
        joined = self.assert_fails_closed("unsupported or missing JSON Schema dialect")
        self.assertIn("check did not run: schemas", joined)


class TestWorkflowPinningDoesNotBlockUpgrades(ValidatorHarness):
    """The workflow check must guard pinning WITHOUT freezing a version.

    It previously asserted the literal string "actions/deploy-pages@v4", so the
    only way to move to v5 was to edit the check that exists to guard the
    workflow. A gate that makes maintenance fail is a gate that gets deleted or
    worked around; the first test here is the one that matters.
    """

    WORKFLOW = ".github/workflows/pages.yml"
    ACTION = "actions/deploy-pages"

    def current_pin(self) -> str:
        """Read the version actually pinned, rather than naming one here.

        The first version of these tests hard-coded "actions/deploy-pages@v4"
        and broke the moment the pin moved to v5 - rebuilding, inside the test
        suite, the exact trap the check under test exists to remove.
        """
        text = (self.root / self.WORKFLOW).read_text(encoding="utf-8")
        match = re.search(rf"uses:\s*{re.escape(self.ACTION)}@(\S+)", text)
        self.assertIsNotNone(match, f"{self.ACTION} is not used by the workflow")
        return match.group(1)

    def edit_workflow(self, old: str, new: str) -> None:
        path = self.root / self.WORKFLOW
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, "workflow anchor missing")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def repin(self, new_ref: str) -> None:
        self.edit_workflow(f"{self.ACTION}@{self.current_pin()}", f"{self.ACTION}@{new_ref}")

    def test_upgrading_an_action_does_not_fail_the_check(self) -> None:
        bumped = "v" + str(int(self.current_pin().lstrip("v").split(".")[0]) + 1)
        self.repin(bumped)
        code, out, _ = self.run_validator()
        self.assertEqual(self.verdicts(out), ["CONTINUITY_VALIDATION=PASS"], "\n".join(out))
        self.assertEqual(code, 0)

    def test_a_full_sha_pin_is_accepted(self) -> None:
        """SHA pinning is GitHub's hardening recommendation; refusing it would
        push the workflow toward the weaker of the two supported styles."""
        self.repin("0f7b2e1c8d4a6f9e3b5c7d1a2e4f6b8c0d2e4f6a")
        code, out, _ = self.run_validator()
        self.assertEqual(self.verdicts(out), ["CONTINUITY_VALIDATION=PASS"], "\n".join(out))
        self.assertEqual(code, 0)

    def test_an_unpinned_action_fails(self) -> None:
        self.repin("main")
        self.assert_fails_closed("pins actions/deploy-pages to 'main'")

    def test_a_missing_action_fails(self) -> None:
        path = self.root / self.WORKFLOW
        text = path.read_text(encoding="utf-8")
        path.write_text(
            "\n".join(l for l in text.splitlines() if "actions/deploy-pages" not in l),
            encoding="utf-8",
        )
        self.assert_fails_closed("does not use actions/deploy-pages")

    def test_a_dropped_permission_still_fails(self) -> None:
        """The non-version tokens are still literal, and must stay guarded."""
        path = self.root / self.WORKFLOW
        text = path.read_text(encoding="utf-8")
        path.write_text(
            "\n".join(l for l in text.splitlines() if "id-token: write" not in l),
            encoding="utf-8",
        )
        self.assert_fails_closed("missing required token: id-token: write")


class TestExitPathDiscipline(ValidatorHarness):
    def test_systemexit_inside_main_still_emits_a_verdict(self) -> None:
        """A SystemExit raised in main() previously escaped with NO verdict."""
        script = self.root / "scripts/validate_continuity.py"
        script.write_text(
            script.read_text(encoding="utf-8").replace(
                "def main() -> int:",
                "def main() -> int:\n    raise SystemExit(7)",
                1,
            ),
            encoding="utf-8",
        )
        code, out, _err = self.run_validator()
        self.assertEqual(self.verdicts(out), ["CONTINUITY_VALIDATION=FAIL"],
                         "a SystemExit inside main() must not escape silently")
        self.assertEqual(code, 2)


class TestResumeDecisionAgreesWithAuthority(ValidatorHarness):
    """A resuming agent must not be told to stop and to proceed at the same time.

    This shipped on main at e5ae250: `resume_decision` read WAIT_FOR_AUTHORITY while
    the primary action NS-030 carried GRANTED_BY_USER_REQUEST_2026_09_03. It happened
    because `resume_decision` is a conclusion about the primary action, and a re-anchor
    carried it forward without recomputing it - the fourth instance of stale operational
    state in two days, introduced by the commit that documented the third.
    """

    def test_granted_authority_beside_wait_for_authority_fails(self) -> None:
        """Construct BOTH halves of the contradiction.

        The first version of this test set only `resume_decision` and relied on the
        committed primary action happening to carry granted authority. When the ledger
        legitimately moved to a HUMAN_APPROVAL_REQUIRED action, WAIT_FOR_AUTHORITY became
        correct and this test failed - not because the validator regressed, but because
        the test was coupled to mutable repository data. A guard that depends on today's
        ledger tests the ledger, not the guard.
        """
        actions = self.load(ACTIONS)
        for row in actions["actions"]:
            if row.get("primary") is True:
                row["authority"] = "GRANTED_BY_TEST_FIXTURE"
        self.save(ACTIONS, actions)
        state = self.load(STATE)
        state["resume_decision"] = "WAIT_FOR_AUTHORITY"
        self.save(STATE, state)
        joined = self.assert_fails_closed("resume_decision is WAIT_FOR_AUTHORITY")
        self.assertIn("told to stop and to proceed at once", joined)

    def test_wait_for_authority_is_correct_when_approval_is_required(self) -> None:
        """The negative control. Without it this check could fire on every repo state
        and still look like it was discriminating."""
        actions = self.load(ACTIONS)
        for row in actions["actions"]:
            if row.get("primary") is True:
                row["authority"] = "HUMAN_APPROVAL_REQUIRED"
        self.save(ACTIONS, actions)
        state = self.load(STATE)
        state["resume_decision"] = "WAIT_FOR_AUTHORITY"
        self.save(STATE, state)
        code, out, _err = self.run_validator()
        self.assertEqual(self.verdicts(out), ["CONTINUITY_VALIDATION=PASS"], "\n".join(out))
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
