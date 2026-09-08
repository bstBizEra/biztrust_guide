#!/usr/bin/env python3
"""Step 8 of the resume protocol has a tool, and this is what holds it to its four words (#345).

`AGENTS.md` section 3 step 7 runs `scripts/validate_continuity.py`; step 8 says "Reconcile observed
state with recorded state" and until WP-112 nothing performed it - the validator made no `git` call
at all. The consequence was live: `badf/current-state.json` names BIZTRUST-GUIDE-WP-111 as the
active package in a pre-merge state, and that package's merge commit IS this main line's head.

THIS MODULE SHELLS OUT. It runs `git` to build fixture repositories, and `sys.executable` to run
the validator. The rest of `tests/` is subprocess-free and that is worth saying out loud;
`tests/test_wp024_fixtures_are_sealed.py` is the precedent. Nothing here touches the network - no
`requests`, `urllib` or `socket`, and every `git` invocation names a local path. #311 keeps the
suite offline and this module stays inside that rule.

WHY THE FIXTURES ARE REAL REPOSITORIES. Each vocabulary value below is reached by CONSTRUCTING the
condition - a repository with the commits that produce it - and not by mocking a return. A mocked
`git` would measure this module's idea of git rather than git, which is how a check comes to pass
hardest at the moment it stops checking.

THE FOUR WORDS, and the rule each one is measured against:

  CONSISTENT    the recorded baseline is an ancestor of the main line and the recorded package has
                not landed. It does NOT require the main line to be still AT the baseline: another
                package merging while this one is in flight is ordinary, and calling that a
                divergence would make every normal merge look like a fault.
  LAG_EXPECTED  the recorded package HAS landed. The record is written on a package's branch
                before its merge, so it cannot record its own merge. Normal - and never to be read
                as work in progress, because the branch may still exist and an agent resuming from
                the record alone would reopen finished work.
  DIVERGED      the recorded baseline is not an ancestor of the main line. No ordering explains it.
  UNKNOWN       the history needed to judge is unavailable.

WHAT THIS DOES NOT DO. Every item is a limit, not a caveat.

 1. The live-tree assertion is CONDITIONAL on the environment, and the condition is MEASURED here
    by this module's own `git` calls rather than asked of the code under test. Where the full
    history is present the verdict must be exactly LAG_EXPECTED; where it is not - CI checks out
    with `actions/checkout@v7` and no `fetch-depth`, so every CI run is shallow - the verdict must
    be exactly UNKNOWN and its reason must name the missing fact. Neither branch is a skip: both
    assert. But it does mean the LAG_EXPECTED half of that test is not exercised in CI, which is
    why `test_lag_expected_when_the_recorded_package_has_landed` constructs the same shape in a
    fixture repository that CI can run.
 2. `test_the_current_tree_reports_lag_expected` is a reading of live records and live history, so
    it is TIME-BOUND by construction. It stays true while `badf/current-state.json` names WP-111
    and WP-111 is in the main line after the recorded baseline; when issue #316 rolls that record
    forward the anchors in `TestAnchors` fail FIRST and say which value moved. That is the
    intended behaviour of a reading of a live divergence, not rot to be papered over with a
    looser assertion.
 3. `git` must be on PATH. If it is not, this module ERRORS rather than skipping. A skip here
    would report a green suite for an environment in which nothing was measured.
 4. The reconciliation is checked for its VERDICT and for the presence of a reason. The reason's
    wording is asserted only where a rule depends on it - that a shallow clone says so, and that a
    landing does not read as work in progress.
 5. Nothing here checks that the recorded package is the RIGHT one, or that the record's
    `state`, `resume_decision` or `stop_reason` agree with the verdict. Those are records
    questions and a records edit waits on #316.

Run: `python -m unittest discover -s tests -p test_resume_reconciliation.py -v`
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "scripts/validate_continuity.py"
STATE = REPO / "badf/current-state.json"

# The anchors this module reads the live tree through. Asserted in TestAnchors, never assumed.
RECORDED_WORK_PACKAGE = "BIZTRUST-GUIDE-WP-111"
RECORDED_BASELINE = "372cf217098e2af11db0e786b746a5d583c7705a"
VOCABULARY = ("CONSISTENT", "LAG_EXPECTED", "DIVERGED", "UNKNOWN")

# Fixture commits must not depend on the runner's git identity, and must not be signed.
GIT_SETTINGS = [
    "-c", "user.name=WP-112 fixture",
    "-c", "user.email=wp112@invalid.example",
    "-c", "commit.gpgsign=false",
]


def _load_validator():
    """Import `scripts/validate_continuity.py` by path, so a copy of the tree loads its own copy."""
    spec = importlib.util.spec_from_file_location("wp112_validator_under_test", VALIDATOR)
    assert spec is not None and spec.loader is not None, f"cannot load {VALIDATOR}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR_MODULE = _load_validator()


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *GIT_SETTINGS, "-C", str(cwd), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )


def git_ok(cwd: Path, *args: str) -> str:
    done = git(cwd, *args)
    if done.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed in {cwd}: {done.stdout}{done.stderr}")
    return done.stdout.strip()


def main_line_tip(root: Path) -> tuple[str, str]:
    """The first of MAIN_REFS that resolves here, as (ref, sha).

    Written after a control measured the alternative false: this module first named
    `refs/heads/main` outright, and a plain `git clone` - which brings `origin/main` and no local
    `main` - errored the live-tree test in every control run, so the unmutated clone was red and
    the twelve controls behind it proved nothing. Corroboration has to read the ref the code
    actually read, and MAIN_REFS is pinned by TestAnchors.
    """
    for ref in VALIDATOR_MODULE.MAIN_REFS:
        done = git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
        if done.returncode == 0:
            return ref, done.stdout.strip()
    raise AssertionError(f"none of {VALIDATOR_MODULE.MAIN_REFS} resolves in {root}")


def record(work_package: str, baseline: str) -> dict:
    """The two fields the reconciliation reads, in the shape `badf/current-state.json` holds them."""
    return {"active_work_package": {"id": work_package}, "source": {"baseline_commit": baseline}}


def reconcile(root: Path, current: dict) -> tuple[str, str]:
    return VALIDATOR_MODULE.reconcile_safely(root, current)


def build_repo(path: Path, branch: str = "main") -> Path:
    path.mkdir(parents=True, exist_ok=True)
    git_ok(path, "init", "--quiet")
    # symbolic-ref rather than `init -b`: it works on every git that has ever shipped this command,
    # and the fixture's branch name is load-bearing (MAIN_REFS is not a guess about the default).
    git_ok(path, "symbolic-ref", "HEAD", f"refs/heads/{branch}")
    return path


def add_commit(root: Path, subject: str) -> str:
    log = root / "history.txt"
    previous = log.read_text(encoding="utf-8") if log.exists() else ""
    log.write_text(previous + subject + "\n", encoding="utf-8")
    git_ok(root, "add", "-A")
    git_ok(root, "commit", "--quiet", "-m", subject)
    return git_ok(root, "rev-parse", "HEAD")


class TestAnchors(unittest.TestCase):
    """What this module reads must be there, or every reading below is of something else."""

    def test_git_is_available(self) -> None:
        self.assertIsNotNone(shutil.which("git"), "this module builds fixture repositories with git")

    def test_the_validator_exposes_the_reconciliation(self) -> None:
        for name in ("reconcile_recorded_state", "reconcile_safely", "RECONCILIATION_VOCABULARY",
                     "MAIN_REFS"):
            self.assertTrue(hasattr(VALIDATOR_MODULE, name), f"{VALIDATOR} has no {name}")

    def test_the_vocabulary_is_exactly_four_words(self) -> None:
        self.assertEqual(VOCABULARY, tuple(VALIDATOR_MODULE.RECONCILIATION_VOCABULARY))

    def test_the_main_line_is_read_from_a_main_ref_and_never_from_head(self) -> None:
        """HEAD on a Work Package branch carries that package's own unmerged commits."""
        refs = tuple(VALIDATOR_MODULE.MAIN_REFS)
        self.assertEqual(("refs/remotes/origin/main", "refs/heads/main"), refs)
        self.assertNotIn("HEAD", refs)

    def test_the_recorded_state_still_names_the_work_package_this_module_reads(self) -> None:
        current = json.loads(STATE.read_text(encoding="utf-8"))
        self.assertEqual(RECORDED_WORK_PACKAGE, current["active_work_package"]["id"])
        self.assertEqual(RECORDED_BASELINE, current["source"]["baseline_commit"])


class TestTheLiveTree(unittest.TestCase):
    """The reading this whole change exists to produce, on the records and history as they are."""

    def full_history_is_present(self) -> tuple[bool, str]:
        """Measured here, with this module's own git calls, not asked of the code under test."""
        top = git(REPO, "rev-parse", "--show-toplevel")
        if top.returncode != 0:
            return False, "not a git repository"
        if git(REPO, "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
            return False, "shallow"
        if not any(git(REPO, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode == 0
                   for ref in VALIDATOR_MODULE.MAIN_REFS):
            return False, "no main ref"
        if git(REPO, "cat-file", "-e", f"{RECORDED_BASELINE}^{{commit}}").returncode != 0:
            return False, "the recorded baseline is not in the object database"
        return True, "full history"

    def test_the_current_tree_reports_lag_expected(self) -> None:
        current = json.loads(STATE.read_text(encoding="utf-8"))
        verdict, reason = reconcile(REPO, current)
        judgeable, why = self.full_history_is_present()
        if not judgeable:
            # Limit 1. Not a skip: the degraded environment is held to UNKNOWN and to a reason
            # that names what is missing, which is the whole contract in CI.
            self.assertEqual("UNKNOWN", verdict, f"{why}: {reason}")
            self.assertTrue(reason.strip(), "UNKNOWN must carry its reason")
            return
        self.assertEqual("LAG_EXPECTED", verdict, reason)
        # The two observed facts the verdict rests on, so the assertion above cannot be vacuous.
        ref, tip = main_line_tip(REPO)
        subject = git_ok(REPO, "log", "-1", "--format=%s", tip)
        self.assertTrue(subject.startswith(f"[{RECORDED_WORK_PACKAGE}]"),
                        f"{ref} is at {tip[:12]} {subject!r}, which does not land the record's package")
        self.assertNotEqual(RECORDED_BASELINE, tip, "the record would not lag if it named main's head")
        self.assertIn("has already landed", reason)

    def test_the_reconciliation_is_printed_beside_the_resume_decision(self) -> None:
        done = subprocess.run([sys.executable, "-B", str(VALIDATOR)],
                              capture_output=True, text=True, timeout=300)
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        lines = done.stdout.splitlines()
        self.assertIn("CONTINUITY_VALIDATION=PASS", lines)
        verdicts = [line for line in lines if line.startswith("STATE_RECONCILIATION=")]
        reasons = [line for line in lines if line.startswith("STATE_RECONCILIATION_REASON=")]
        self.assertEqual(1, len(verdicts), f"expected exactly one verdict line, got {verdicts}")
        self.assertEqual(1, len(reasons), f"expected exactly one reason line, got {reasons}")
        self.assertIn(verdicts[0].split("=", 1)[1], VOCABULARY)
        self.assertTrue(reasons[0].split("=", 1)[1].strip(), "the reason line is empty")
        resume = [i for i, line in enumerate(lines) if line.startswith("RESUME_DECISION=")]
        self.assertEqual(1, len(resume), "RESUME_DECISION is the line step 7 already reads")
        distance = lines.index(verdicts[0]) - resume[0]
        # Bounded on BOTH sides. An earlier version bounded only the upper end, so a verdict
        # printed above the PASS line - away from the two lines step 7 already reads - satisfied it.
        self.assertTrue(0 < distance < 4,
                        f"the reconciliation sits {distance} lines from RESUME_DECISION; it must "
                        f"follow it, beside it, where step 7 already looks")

    def test_a_tree_with_no_git_still_passes_and_says_unknown(self) -> None:
        """The degradation, end to end: no history, no verdict invented, no change to the run.

        This is the property the whole design turns on - the check degrades, it does not fail -
        measured on the validator itself rather than on the function.
        """
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as holder:
            root = Path(holder) / "repo"
            shutil.copytree(REPO, root, ignore=shutil.ignore_patterns(
                ".git", "_site", "node_modules", "__pycache__"))
            done = subprocess.run([sys.executable, "-B", str(root / "scripts/validate_continuity.py")],
                                  capture_output=True, text=True, timeout=300)
            self.assertEqual(0, done.returncode, done.stdout + done.stderr)
            self.assertIn("CONTINUITY_VALIDATION=PASS", done.stdout.splitlines())
            self.assertIn("STATE_RECONCILIATION=UNKNOWN", done.stdout.splitlines())
            self.assertEqual([], [line for line in done.stdout.splitlines()
                                  if line.startswith("ERROR:")])


class TestVocabulary(unittest.TestCase):
    """Every value reached by constructing the condition in a real repository.

    The fixtures are built once for the class: each is a few commits, but a shallow clone and four
    `git init`s per test would be paid on every push.
    """

    verdicts: dict[str, tuple[str, str]] = {}

    @classmethod
    def setUpClass(cls) -> None:
        cls._holder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        base = Path(cls._holder.name)
        cls.addClassCleanup(cls._holder.cleanup)
        cls.verdicts = {}

        # CONSISTENT, main still at the recorded baseline.
        still = build_repo(base / "still")
        baseline = add_commit(still, "[BIZTRUST-GUIDE-WP-900] the baseline")
        cls.verdicts["at_baseline"] = reconcile(still, record("BIZTRUST-GUIDE-WP-901", baseline))

        # CONSISTENT, a DIFFERENT package landed while the recorded one is in flight. This is the
        # case that separates "the record's package landed" from "the main line moved".
        moved = build_repo(base / "moved")
        moved_baseline = add_commit(moved, "[BIZTRUST-GUIDE-WP-900] the baseline")
        add_commit(moved, "[BIZTRUST-GUIDE-WP-902] a sibling package landed first")
        cls.verdicts["sibling_landed"] = reconcile(
            moved, record("BIZTRUST-GUIDE-WP-901", moved_baseline))

        # LAG_EXPECTED, the live shape: the recorded package's own merge is the head.
        landed = build_repo(base / "landed")
        landed_baseline = add_commit(landed, "[BIZTRUST-GUIDE-WP-900] the baseline")
        add_commit(landed, "[BIZTRUST-GUIDE-WP-901] the recorded package's own merge")
        cls.verdicts["landed"] = reconcile(landed, record("BIZTRUST-GUIDE-WP-901", landed_baseline))

        # LAG_EXPECTED still, with a later package on top. The record cannot record ANY merge that
        # followed it; the fact that decides the word is that its own package is among them.
        later = build_repo(base / "later")
        later_baseline = add_commit(later, "[BIZTRUST-GUIDE-WP-900] the baseline")
        add_commit(later, "[BIZTRUST-GUIDE-WP-901] the recorded package's own merge")
        add_commit(later, "[BIZTRUST-GUIDE-WP-902] and the next package after it")
        cls.verdicts["landed_then_more"] = reconcile(
            later, record("BIZTRUST-GUIDE-WP-901", later_baseline))

        # A commit that MENTIONS the package without landing it stays CONSISTENT: the id is matched
        # at the start of the subject, not anywhere in it.
        mention = build_repo(base / "mention")
        mention_baseline = add_commit(mention, "[BIZTRUST-GUIDE-WP-900] the baseline")
        add_commit(mention, "[BIZTRUST-GUIDE-WP-902] revert of [BIZTRUST-GUIDE-WP-901] groundwork")
        cls.verdicts["mentioned_only"] = reconcile(
            mention, record("BIZTRUST-GUIDE-WP-901", mention_baseline))

        # DIVERGED: the recorded baseline exists but is on a history main never took.
        apart = build_repo(base / "apart")
        root_commit = add_commit(apart, "[BIZTRUST-GUIDE-WP-900] the root")
        git_ok(apart, "checkout", "--quiet", "-b", "elsewhere")
        stranded = add_commit(apart, "[BIZTRUST-GUIDE-WP-903] a commit main never took")
        git_ok(apart, "checkout", "--quiet", "main")
        add_commit(apart, "[BIZTRUST-GUIDE-WP-904] main went its own way")
        cls.verdicts["not_an_ancestor"] = reconcile(
            apart, record("BIZTRUST-GUIDE-WP-901", stranded))
        assert root_commit != stranded

        # UNKNOWN, four ways.
        plain = base / "plain"
        plain.mkdir()
        cls.verdicts["not_a_repository"] = reconcile(plain, record("BIZTRUST-GUIDE-WP-901", "0" * 40))

        absent = build_repo(base / "absent")
        add_commit(absent, "[BIZTRUST-GUIDE-WP-900] the only commit")
        cls.verdicts["baseline_absent"] = reconcile(
            absent, record("BIZTRUST-GUIDE-WP-901", "0" * 40))

        # A tree that is not itself a repository but sits INSIDE one. Without a guard, git answers
        # about the enclosing repository and the verdict looks authoritative about the wrong
        # history - which is the shape of every unpacked copy of this tree.
        enclosing = build_repo(base / "enclosing")
        enclosing_baseline = add_commit(enclosing, "[BIZTRUST-GUIDE-WP-900] the enclosing history")
        nested = enclosing / "nested"
        nested.mkdir()
        cls.verdicts["inside_another_repository"] = reconcile(
            nested, record("BIZTRUST-GUIDE-WP-901", enclosing_baseline))

        nameless = build_repo(base / "nameless", branch="work")
        nameless_baseline = add_commit(nameless, "[BIZTRUST-GUIDE-WP-900] on a branch called work")
        cls.verdicts["no_main_ref"] = reconcile(
            nameless, record("BIZTRUST-GUIDE-WP-901", nameless_baseline))

        # A GENUINELY shallow clone - `--depth 1` over file://, because git ignores --depth on a
        # plain local path. This is the CI shape: main resolves, and the history behind it does not
        # exist.
        deep = build_repo(base / "deep")
        deep_baseline = add_commit(deep, "[BIZTRUST-GUIDE-WP-900] the baseline")
        add_commit(deep, "[BIZTRUST-GUIDE-WP-901] the recorded package's own merge")
        shallow = base / "shallow"
        clone = subprocess.run(
            ["git", *GIT_SETTINGS, "clone", "--quiet", "--depth", "1", deep.as_uri(), str(shallow)],
            capture_output=True, text=True, timeout=120)
        assert clone.returncode == 0, clone.stdout + clone.stderr
        assert git_ok(shallow, "rev-parse", "--is-shallow-repository") == "true", "the clone is not shallow"
        cls.verdicts["shallow"] = reconcile(shallow, record("BIZTRUST-GUIDE-WP-901", deep_baseline))

        cls.verdicts["no_record"] = reconcile(still, {})
        cls.verdicts["no_baseline"] = reconcile(
            still, {"active_work_package": {"id": "BIZTRUST-GUIDE-WP-901"}, "source": {}})

    def verdict(self, case: str) -> str:
        return self.verdicts[case][0]

    def reason(self, case: str) -> str:
        return self.verdicts[case][1]

    def test_consistent_when_the_main_line_is_still_at_the_baseline(self) -> None:
        self.assertEqual("CONSISTENT", self.verdict("at_baseline"), self.reason("at_baseline"))

    def test_consistent_when_a_sibling_package_landed_first(self) -> None:
        """Movement is not lag. Calling it lag would make every normal merge look like a fault."""
        self.assertEqual("CONSISTENT", self.verdict("sibling_landed"), self.reason("sibling_landed"))

    def test_consistent_when_a_commit_only_mentions_the_recorded_package(self) -> None:
        self.assertEqual("CONSISTENT", self.verdict("mentioned_only"), self.reason("mentioned_only"))

    def test_lag_expected_when_the_recorded_package_has_landed(self) -> None:
        self.assertEqual("LAG_EXPECTED", self.verdict("landed"), self.reason("landed"))

    def test_lag_expected_does_not_read_as_work_in_progress(self) -> None:
        """The record may not be read as in-flight work: the branch may still exist."""
        self.assertIn("has already landed", self.reason("landed"))
        self.assertIn("does NOT describe work still in progress", self.reason("landed"))

    def test_lag_expected_survives_a_package_landing_after_it(self) -> None:
        self.assertEqual("LAG_EXPECTED", self.verdict("landed_then_more"),
                         self.reason("landed_then_more"))

    def test_diverged_when_the_baseline_is_not_an_ancestor_of_the_main_line(self) -> None:
        self.assertEqual("DIVERGED", self.verdict("not_an_ancestor"), self.reason("not_an_ancestor"))

    def test_unknown_outside_a_repository(self) -> None:
        self.assertEqual("UNKNOWN", self.verdict("not_a_repository"))

    def test_unknown_when_the_baseline_is_not_in_the_object_database(self) -> None:
        self.assertEqual("UNKNOWN", self.verdict("baseline_absent"))
        self.assertIn("object database", self.reason("baseline_absent"))

    def test_unknown_when_the_tree_merely_sits_inside_another_repository(self) -> None:
        """An enclosing repository is not this one, and its history is not an answer about this."""
        self.assertEqual("UNKNOWN", self.verdict("inside_another_repository"),
                         self.reason("inside_another_repository"))

    def test_unknown_when_no_main_ref_resolves(self) -> None:
        self.assertEqual("UNKNOWN", self.verdict("no_main_ref"))

    def test_unknown_on_a_shallow_clone_and_the_reason_says_shallow(self) -> None:
        """The CI shape. The reason must name shallowness, not the absent baseline it implies."""
        self.assertEqual("UNKNOWN", self.verdict("shallow"), self.reason("shallow"))
        self.assertIn("shallow", self.reason("shallow"))

    def test_unknown_when_the_record_carries_neither_field(self) -> None:
        self.assertEqual("UNKNOWN", self.verdict("no_record"))
        self.assertEqual("UNKNOWN", self.verdict("no_baseline"))

    def test_every_vocabulary_value_is_reached_by_a_constructed_condition(self) -> None:
        reached = {verdict for verdict, _ in self.verdicts.values()}
        self.assertEqual(set(VOCABULARY), reached,
                         "a word nothing constructs is a word nothing measures")

    def test_no_case_produces_a_word_outside_the_vocabulary(self) -> None:
        for case, (verdict, reason) in self.verdicts.items():
            self.assertIn(verdict, VOCABULARY, case)
            self.assertTrue(reason.strip(), f"{case} carries no reason")
            self.assertNotIn("\n", reason, f"{case}: the reason must fit one printed line")


if __name__ == "__main__":
    unittest.main()
