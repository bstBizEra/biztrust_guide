#!/usr/bin/env python3
"""Step 8 of the resume protocol has a tool, and this is what holds it to its four words (#351).

`AGENTS.md` section 3 step 7 runs `scripts/validate_continuity.py`; step 8 says "Reconcile observed
state with recorded state" and until WP-112 nothing performed it - the validator made no `git` call
at all. The consequence was live when this was written: `badf/current-state.json` named
BIZTRUST-GUIDE-WP-111 as the active package in a pre-merge state while that package's merge commit
was already on the main line. Whether it is still the main line's HEAD is not a claim this module
makes - it stops being true the moment anything merges after it, which is exactly the mistake the
live test was repaired for.

THIS MODULE SHELLS OUT. It runs `git` to build fixture repositories, and `sys.executable` to run
the validator. FOUR modules under `tests/` call a subprocess - `test_resume_reconciliation.py`,
`test_resume_schema_identity.py`, `test_validator_fails_closed.py` and
`test_wp024_fixtures_are_sealed.py`, the last being this module's precedent - measured with

    grep -lnE "subprocess[.](run|Popen|check_output|check_call)" tests/*.py

This sentence said "the rest of `tests/` is subprocess-free", which was false when it was written:
both unaccounted modules predate this one and were calling subprocesses at its own baseline. That
is #357, and the phrase propagated by being copied into three further places before it was caught.
Grepping for the WORD `subprocess` returns SIX, because two modules only mention it in prose, so
re-run the command above rather than restating the set from memory - a count is only as good as
its filter. Nothing here touches the network - no `requests`, `urllib` or `socket`, and every
`git` invocation names a local path. #311 keeps the suite offline and this module stays inside
that rule.

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
  DIVERGED      the recorded baseline is not an ancestor of the main line AND the main line is
                not an ancestor of the baseline: neither line contains the other, which is the
                disagreement no ordering explains. The second half of that test is #353's
                repair; until it landed, a main ref that had simply not been fetched sat behind
                the baseline and got this word too. Limit 9.
  UNKNOWN       the history needed to judge is unavailable - including a main ref that sits
                BEHIND the recorded baseline, which is #353's case and is measured here.

WHAT THIS DOES NOT DO. Every item is a limit, not a caveat.

 1. The live-tree assertion is CONDITIONAL on the environment, and the condition is MEASURED here
    by this module's own `git` calls rather than asked of the code under test. Where the history
    needed to judge is absent - CI checks out with `actions/checkout@v7` and no `fetch-depth`, so
    every CI run is shallow - the verdict must be exactly UNKNOWN and must carry a non-empty
    reason. Where it is present, the verdict must be the word the measured facts imply - FOUR
    facts since #353, the reverse ancestry being the fourth - across five branches, because
    UNKNOWN is reached two ways and only one of them is a degraded environment. No branch is a
    skip: every one of them asserts.
    Two things follow, and both are limits rather than caveats. In CI only the degraded-UNKNOWN
    branch ever runs, which is why the other words are constructed in fixture repositories that CI
    can run. And that branch checks only that a reason exists, not that it names the right missing
    fact; the fixture case `test_unknown_on_a_shallow_clone_and_the_reason_says_shallow` is where
    that wording is held. The BEHIND branch is the exception and does assert its wording, because
    a stale ref reported with a divergence's reason is the whole of #353.
 2. The live reading takes whichever branch the history puts it in, and NOTHING here pins which
    branch that is. It is therefore no longer a ratchet on the current divergence: if the record
    rolls forward to a package that has not landed, this test asserts CONSISTENT and says
    nothing about the change. That is the price of the repair below and it is paid on purpose -
    the alternative failed ordinary bookkeeping as though it were a code defect.

    THE REPAIR. This module hardcoded `BIZTRUST-GUIDE-WP-111` and corroborated LAG_EXPECTED by
    requiring the main line's TIP subject to be that package's merge. LAG_EXPECTED claims no such
    thing: it claims the package landed SOMEWHERE since the recorded baseline. Tip and range agree
    only until the next package merges, so **merging WP-112 would have broken WP-112's own test**,
    and it would have landed green because CI is shallow and takes the UNKNOWN branch. The id and
    the baseline are now read from the record, the corroboration is over the range, and a control
    simulates the next package merging and shows the test pass with the verdict still LAG_EXPECTED.
 3. `git` must be on PATH. If it is not, this module ERRORS rather than skipping. A skip here
    would report a green suite for an environment in which nothing was measured.
 4. The reconciliation is checked for its VERDICT and for the presence of a one-line reason. The
    reason's WORDING is asserted for three facts and no others: that a shallow clone says
    "shallow", that an absent baseline says "object database", and that a landing reads as "has
    already landed" and explicitly not as work in progress. Everything else a reason says is
    unchecked prose.
 5. Nothing here checks that the recorded package is the RIGHT one, or that the record's
    `state`, `resume_decision` or `stop_reason` agree with the verdict. That is a hole, not a
    caveat, and `scripts/wp112_controls.py` demonstrates it rather than this sentence asserting
    it: a record whose package has LANDED while its own `state` still reads IN_PROGRESS leaves
    this suite GREEN. The control expects green and reports if it ever goes red, because a hole
    that has closed needs its limit re-derived. Reconciling the record itself is a records edit
    and not this module's business.
 6. A tree that is not the root of the repository containing it DEGRADES here rather than failing.
    `full_history_is_present` checks that case itself, because without it the probe read the
    enclosing repository's toplevel, shallowness, main ref and object database - all present, all
    about the wrong root - answered "judgeable", and then demanded LAG_EXPECTED while the code
    correctly answered UNKNOWN. A test that goes red for where the tree was unpacked is a test
    failing for an environment reason, which is what #311 exists to keep out. Measured by a
    control that copies the tree into a subdirectory of a clone and expects GREEN, paired with one
    that removes the check and shows the same tree go RED.

 7. The DIVERGED prose is guarded in TWO places and against TWO different lists, and the
    asymmetry is deliberate. The printed reason may not carry an absence claim NOR a cause -
    `rebase`, `force-push` - because a reason is one terse assertion in which naming a cause is
    asserting it. The docstring entry is held only to the absence claims and to stating that the
    baseline is present, because a docstring paragraph may legitimately name causes in order to
    say they cannot be distinguished, which is what the comment beside that branch does.

    That leaves a hole: a docstring entry that asserts a cause outright passes. It is
    demonstrated rather than asserted - `scripts/wp112_controls.py` writes "a force-push moved the
    main line away" into that entry and expects the suite to stay GREEN. If it goes red the
    asymmetry has closed and this limit must be re-derived.

    The guard reads the entry through `vocabulary_entry`, which MEASURES the entry's indent rather
    than assuming it: CPython 3.13 strips a docstring's common leading whitespace at compile time
    and earlier versions do not, so the same source yields entries at column 0 on one interpreter
    and column 4 on another. Which version CI runs is not asserted here, because nothing in this
    repository pins it. Both shapes were exercised before this limit was written.

 8. The live test measures WIRING; the fixture tests measure RULES. Its branches re-derive the
    classification from the same three facts the code reads, with this module's own git calls, so
    it can catch the function reading the wrong record, resolving the wrong ref, or answering over
    a history it cannot see - and it cannot catch a rule that is wrong in both places at once.
    The non-circular half is `TestVocabulary`, where every word is reached by constructing the
    condition in a repository built for it.

 9. DIVERGED NOW REQUIRES BOTH DIRECTIONS, and what it no longer covers is measured rather than
    described. A clone whose main ref has not been fetched sits BEHIND the recorded baseline, so
    the baseline is not an ancestor of it, and until #353 was closed that alone printed DIVERGED -
    the loudest word - for a stale ref. Measured on a clone with `origin/main` at the commit
    before the recorded baseline: DIVERGED before the repair, UNKNOWN naming the BEHIND relation
    after it, both with the commands in `scripts/wp114_controls.py`'s docstring. The word DIVERGED is
    now reached only where NEITHER line contains the other, which is what the two fixtures here
    construct, and both of them are checked in both directions rather than in one.

    WHAT THIS STILL DOES NOT SETTLE: a fifth word. UNKNOWN is what a behind main ref reports, and
    UNKNOWN means "the history needed to judge is unavailable" - accurate for an unfetched clone,
    because what landed after the baseline genuinely cannot be read from there. #353 fixed the
    vocabulary at four and `test_the_vocabulary_is_exactly_four_words` holds it there. A reader
    who wants "behind" told apart from the other four unavailabilities reads the REASON, and the
    reason's wording is asserted for that case here.

    AND IT DOES NOT SETTLE WHY THE REF IS BEHIND, which the reason may therefore not claim. An
    unfetched ref is the common cause and not the only one: a baseline recorded from a branch
    that never merged gives the same shape with the main ref fully current, and fetching would
    fix nothing there. The printed reason offers the cause as common and leads with the relation,
    under the same rule that forbids the DIVERGED reason from naming a rebase - limit 7's
    asymmetry, applied to the word this package added a route to. That rule is checkable and is
    checked: if the reason mentions fetching, it must also say the cause is the common one.

10. THE THIRD OUTCOME OF THE REVERSE CALL IS UNMEASURED, and that is a hole rather than a caveat.
    `git merge-base --is-ancestor` answers 0, 1 or an error. The error branch returns UNKNOWN
    rather than falling through to DIVERGED, and it is reachable only by a timeout or an
    unrunnable git - the same call in the opposite direction has already succeeded by then. No
    fixture here constructs it and none can without mocking, which this module does not do.
    `scripts/wp114_controls.py` DEMONSTRATES the hole instead of this sentence asserting it: it
    replaces that branch's UNKNOWN with a fall-through to DIVERGED and expects the suite to stay
    GREEN. If that control ever goes red the hole has closed and this limit must be re-derived,
    not deleted.

MEASURED, on fresh clones, BY TWO RUNNERS. Neither is wired into CI: each control makes a fresh
clone and runs this suite or the validator on top of it, and `scripts/validate_continuity.py` is
the instrument every other gate in this repository is read through.

`scripts/wp114_controls.py` - FIFTEEN controls, run only after an unmutated clone that must be
green first. NINE mutations each trip the test named for them and FOUR of those trip nothing
else; one is the declared hole at limit 10 and expects the suite to stay GREEN. Four run the
validator itself on a clone whose `origin/main` has been moved, in two pairs: a ref set BEHIND the
recorded baseline prints UNKNOWN and exits 0, and the same clone with the reverse question removed
prints DIVERGED - which is how the first is known to come from the repair rather than by accident -
then a ref on a history sharing no commit with the baseline prints DIVERGED, and the same clone
with the behind test widened prints UNKNOWN. The fifteenth re-measures the subprocess sentence at
the top of this docstring against the tree it describes.

`scripts/wp112_controls.py` - nineteen controls, ALL NINETEEN behaving as declared since #360 was
repaired. THIRTEEN mutations trip the test named for them and SIX of those trip nothing else, two
are the declared holes at limits 5 and 7 and stay GREEN, two are unmutated trees in environments
they must survive and stay GREEN, and the two shallow-clone script controls print UNKNOWN and
CONSISTENT. It was twelve and five while the nineteenth control could not reach its mutation.

IT WAS EIGHTEEN OF NINETEEN WHEN WP-114 RE-RAN IT, and what that cost is worth recording. The one
that did not behave was `the same later merge with the corroboration required to be the TIP`, and
WP-114 read the cause as the SOURCE: that control built its fixture on the clone's `origin/main`,
which is the source's `refs/heads/main`, so a checkout that had fetched without pulling had a local
main BEHIND the recorded baseline, the fixture landed in the DIVERGED branch, and the reading
returned there without ever reaching the corroboration the mutation targets. The mechanism was
right and the attribution was not. The cause was the FIXTURE: WP-118 (#360) synthesises that chain
on the RECORDED BASELINE, which no pull moves, and the control now behaves on a source whose local
main is behind the baseline, at it, or ahead of it. Measured before and after on one such source
with nothing else changed - nineteen controls one not behaving, then nineteen controls none - and
the grid that separates the two builders is `scripts/wp118_controls.py`. `check_source_main_line`
is unchanged by that repair: it allows the behind direction and promises only that the run is not
measuring drift, never that it will be green.

Run: `python -m unittest discover -s tests -p test_resume_reconciliation.py -v`
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "scripts/validate_continuity.py"
STATE = REPO / "badf/current-state.json"

# NO RECORDED VALUES LIVE HERE. The Work Package id and the baseline commit are READ FROM
# `badf/current-state.json` every time they are needed. They were constants once - the module was
# written against BIZTRUST-GUIDE-WP-111 at baseline 372cf217098e, and that is stated here as
# history rather than asserted anywhere - and pinning them meant this suite would go red when the
# record rolled forward, which is ordinary Work Package bookkeeping and not a defect here.
VOCABULARY = ("CONSISTENT", "LAG_EXPECTED", "DIVERGED", "UNKNOWN")

# Claims that the repository LACKS the baseline. DIVERGED is reachable only after `cat-file -e`
# proves it is present, so any of these is false wherever DIVERGED is described - in the printed
# reason and in the docstring entry alike.
ABSENCE_CLAIMS = ("does not carry", "does not have", "does not hold")

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


def vocabulary_entry(word: str) -> str:
    """The paragraph `reconcile_recorded_state`'s docstring gives to one vocabulary word.

    The docstring lays the four words out as a definition list - four spaces, the word, two or
    more spaces, then the text, continued on lines indented past it. This reads one entry: from
    its opening line to the next line that opens another entry or ends the list.

    An entry this cannot find is a FAILURE at the call site, never a skip. A reader that returns
    nothing quietly is how a check comes to pass hardest at the moment it stops checking, and this
    module already carries one finding of exactly that shape.
    """
    doc = VALIDATOR_MODULE.reconcile_recorded_state.__doc__ or ""
    lines = doc.splitlines()
    # The entry's own indent is MEASURED, not assumed: CPython 3.13 strips the common leading
    # whitespace from a docstring at compile time and earlier versions do not, so the same source
    # gives entries at column 0 on one interpreter and at column 4 on another. A reader that
    # hard-coded either would pass on one and find nothing on the other - silently, since finding
    # nothing is indistinguishable from finding a clean entry unless somebody asserts otherwise.
    # That is what `test_the_docstring_reader_can_tell_the_entries_apart` is for. Both shapes were
    # exercised: the first version of this reader found nothing on either.
    opening = re.compile(rf"^(\s*){re.escape(word)} {{2,}}(.*)$")
    for index, line in enumerate(lines):
        found = opening.match(line)
        if not found:
            continue
        indent = len(found.group(1))
        collected = [found.group(2)]
        for following in lines[index + 1:]:
            # A continuation is indented PAST the word. Anything else - the next entry, or the
            # prose that follows the list - ends this entry.
            if following.strip() and len(following) - len(following.lstrip()) <= indent:
                break
            collected.append(following)
        return "\n".join(collected).strip()
    return ""


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

    def test_the_record_carries_the_two_fields_the_reconciliation_reads(self) -> None:
        """SHAPE, not values. This test used to pin the id and the baseline to the strings the
        module was written against, which would have failed the suite for a records change - the
        rolling-forward every Work Package does. What the module needs is that the two fields are
        there and well formed; which package they name is the record's business.
        """
        current = json.loads(STATE.read_text(encoding="utf-8"))
        work_package = current["active_work_package"]["id"]
        baseline = current["source"]["baseline_commit"]
        self.assertRegex(work_package, r"^BIZTRUST-GUIDE-WP-\d+$")
        self.assertRegex(baseline, r"^[0-9a-f]{40}$")


class TestTheLiveTree(unittest.TestCase):
    """The reading this whole change exists to produce, on the records and history as they are."""

    def recorded(self) -> tuple[dict, str, str]:
        """The record, and the two fields the reconciliation reads, READ FROM IT.

        Neither is a constant. This module carried the Work Package id and the baseline as
        hardcoded strings until review measured what that costs: the corroboration below then
        demanded that the id it had been written with be the one in the record, so the record
        rolling forward would have turned this suite red for ordinary bookkeeping.
        """
        current = json.loads(STATE.read_text(encoding="utf-8"))
        return current, current["active_work_package"]["id"], current["source"]["baseline_commit"]

    def full_history_is_present(self, baseline: str) -> tuple[bool, str]:
        """Measured here, with this module's own git calls, not asked of the code under test.

        The enclosing-repository case is checked HERE and not only in the code, and that is a
        repair rather than a flourish. Without it this probe answered "judgeable" for a tree
        unpacked inside another checkout of this repository - toplevel resolves, the clone is not
        shallow, a main ref resolves, the baseline is in the enclosing repository's object
        database - and then demanded LAG_EXPECTED while the code correctly answered UNKNOWN. A
        test that goes red because of where the tree was unpacked is a test failing for an
        environment reason, which is what #311 exists to keep out of this suite. Measured by a
        control that copies the tree into a subdirectory of a clone and expects GREEN.
        """
        top = git(REPO, "rev-parse", "--show-toplevel")
        if top.returncode != 0:
            return False, "not a git repository"
        if os.path.normcase(os.path.realpath(top.stdout.strip())) != \
                os.path.normcase(os.path.realpath(REPO)):
            return False, "inside another repository rather than at its root"
        if git(REPO, "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
            return False, "shallow"
        if not any(git(REPO, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode == 0
                   for ref in VALIDATOR_MODULE.MAIN_REFS):
            return False, "no main ref"
        if git(REPO, "cat-file", "-e", f"{baseline}^{{commit}}").returncode != 0:
            return False, "the recorded baseline is not in the object database"
        return True, "full history"

    def test_the_live_reading_agrees_with_the_history_measured_here(self) -> None:
        """The live reading, corroborated against what the verdict actually rests on.

        THE CORROBORATION IS A RANGE, NOT A TIP, and that is this test's whole subject. An earlier
        version asserted that the main line's TIP subject landed the recorded package. LAG_EXPECTED
        does not claim that: it claims the package landed SOMEWHERE in the main line since the
        recorded baseline. The two agree only until the next package merges - so merging WP-112
        would have broken WP-112's own test, and it would have landed green because CI is shallow
        and takes the UNKNOWN branch. Measured by a control that simulates exactly that merge.

        Every branch asserts; none is a skip. What each one is worth differs, and limit 8 says so:
        the fixture tests hold the RULES, and this test holds the WIRING - that the function reads
        the record this module reads, resolves the ref this module resolves, and answers over the
        history this module can see.
        """
        current, work_package, baseline = self.recorded()
        verdict, reason = reconcile(REPO, current)

        judgeable, why = self.full_history_is_present(baseline)
        if not judgeable:
            # Limit 1. Not a skip: the degraded environment is held to UNKNOWN and to a reason.
            self.assertEqual("UNKNOWN", verdict, f"{why}: {reason}")
            self.assertTrue(reason.strip(), "UNKNOWN must carry its reason")
            return

        ref, tip = main_line_tip(REPO)
        ancestry = git(REPO, "merge-base", "--is-ancestor", baseline, tip).returncode
        self.assertIn(ancestry, (0, 1), f"git could not decide whether {baseline[:12]} precedes {ref}")
        if ancestry == 1:
            # BOTH DIRECTIONS, because one of them alone is two different states. This branch
            # asserted DIVERGED outright until #353, and the case that made that wrong is not
            # hypothetical here: `git clone` of this repository takes its `origin/main` from the
            # source's `refs/heads/main`, so a clone made while the source's local main is behind
            # its own origin/main lands in exactly this branch with the record ahead of the ref.
            # Every control run in `scripts/wp114_controls.py` is such a clone.
            behind = git(REPO, "merge-base", "--is-ancestor", tip, baseline).returncode
            self.assertIn(behind, (0, 1),
                          f"git could not decide whether {ref} precedes {baseline[:12]}")
            if behind == 0:
                self.assertEqual("UNKNOWN", verdict, reason)
                self.assertIn("BEHIND the record", reason)
                return
            self.assertEqual("DIVERGED", verdict, reason)
            self.assertIn("is present in this clone", reason)
            return

        subjects = [line for line in
                    git_ok(REPO, "log", "--format=%s", f"{baseline}..{tip}").splitlines()
                    if line.strip()]
        landings = [line for line in subjects if line.startswith(f"[{work_package}]")]
        if not landings:
            self.assertEqual("CONSISTENT", verdict, reason)
            return

        # The landing is NOT required to be the tip. That is the whole repair, and it is proved by
        # a control that puts a later package on the main line rather than by anything assertable
        # here: two assertions that used to sit at this spot said nothing at all - a filter is
        # always no longer than what it filters, and an empty range has already returned
        # CONSISTENT above, so neither could fail.
        self.assertEqual("LAG_EXPECTED", verdict, reason)
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
    # The DIVERGED fixtures, kept so the reason can be checked against what git says about them.
    diverged_repositories: dict[str, tuple[Path, str]] = {}
    # The #353 fixtures - a main ref BEHIND the recorded baseline - kept for the same reason.
    behind_repositories: dict[str, tuple[Path, str]] = {}

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
        cls.diverged_repositories = {"not_an_ancestor": (apart, stranded)}

        # DIVERGED again, from an ORPHAN history: the baseline shares no commit at all with main.
        # Kept as a second fixture because the two differ in exactly the way the reason must not
        # claim to know - one branched from main, one never touched it - and the reason has to be
        # true of both.
        orphan = build_repo(base / "orphan")
        add_commit(orphan, "[BIZTRUST-GUIDE-WP-900] the main root")
        git_ok(orphan, "checkout", "--quiet", "--orphan", "elsewhere")
        orphan_baseline = add_commit(orphan, "[BIZTRUST-GUIDE-WP-903] an unrelated history")
        git_ok(orphan, "checkout", "--quiet", "--force", "main")
        cls.verdicts["orphan_history"] = reconcile(
            orphan, record("BIZTRUST-GUIDE-WP-901", orphan_baseline))
        cls.diverged_repositories["orphan_history"] = (orphan, orphan_baseline)

        # DIVERGED after a REBASE, which is the other ordering #353 names. The recorded baseline
        # is the pre-rebase commit; main carries the rewritten one. Neither contains the other,
        # and no call made by the reconciliation can tell this apart from the orphan case - which
        # is why the reason says nothing about the cause.
        rebased = build_repo(base / "rebased")
        add_commit(rebased, "[BIZTRUST-GUIDE-WP-900] the root")
        git_ok(rebased, "checkout", "--quiet", "-b", "before")
        rebased_baseline = add_commit(rebased, "[BIZTRUST-GUIDE-WP-901] the commit as it was")
        git_ok(rebased, "checkout", "--quiet", "main")
        add_commit(rebased, "[BIZTRUST-GUIDE-WP-901] the commit as it was, rewritten")
        cls.verdicts["rebased"] = reconcile(
            rebased, record("BIZTRUST-GUIDE-WP-901", rebased_baseline))
        cls.diverged_repositories["rebased"] = (rebased, rebased_baseline)

        # #353: A MAIN REF THAT IS MERELY BEHIND. Two fixtures, one per entry in MAIN_REFS,
        # because the stale ref in the field is `origin/main` and the one a bare fixture has is
        # `refs/heads/main`; the reconciliation reads the first that resolves and both must
        # answer the same way. The baseline stays REACHABLE from a second branch, so it is in the
        # object database rather than merely unreferenced and still findable - `cat-file -e` has
        # to accept it or the run stops one branch earlier, at a different UNKNOWN entirely.
        behind_local = build_repo(base / "behind_local")
        behind_local_first = add_commit(behind_local, "[BIZTRUST-GUIDE-WP-900] the baseline's parent")
        behind_local_baseline = add_commit(behind_local, "[BIZTRUST-GUIDE-WP-901] the recorded baseline")
        git_ok(behind_local, "branch", "fetched", behind_local_baseline)
        git_ok(behind_local, "update-ref", "refs/heads/main", behind_local_first)
        cls.verdicts["behind_local_main"] = reconcile(
            behind_local, record("BIZTRUST-GUIDE-WP-901", behind_local_baseline))
        cls.behind_repositories = {
            "behind_local_main": (behind_local, behind_local_baseline)}

        behind_origin = build_repo(base / "behind_origin")
        behind_origin_first = add_commit(behind_origin, "[BIZTRUST-GUIDE-WP-900] the baseline's parent")
        behind_origin_baseline = add_commit(behind_origin, "[BIZTRUST-GUIDE-WP-901] the recorded baseline")
        # `origin/main` is set to the older commit and `main` is left at the newer one, so the
        # fixture also proves the verdict is about the ref MAIN_REFS picks first and not about
        # whichever ref happens to be stale.
        git_ok(behind_origin, "update-ref", "refs/remotes/origin/main", behind_origin_first)
        cls.verdicts["behind_origin_main"] = reconcile(
            behind_origin, record("BIZTRUST-GUIDE-WP-901", behind_origin_baseline))
        cls.behind_repositories["behind_origin_main"] = (behind_origin, behind_origin_baseline)

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

    def test_diverged_from_an_orphan_history_too(self) -> None:
        self.assertEqual("DIVERGED", self.verdict("orphan_history"), self.reason("orphan_history"))

    def test_diverged_after_a_rebase_too(self) -> None:
        """The other ordering #353 names, and it must still reach the loud word."""
        self.assertEqual("DIVERGED", self.verdict("rebased"), self.reason("rebased"))

    def test_a_main_ref_behind_the_recorded_baseline_is_unknown_and_not_diverged(self) -> None:
        """#353's first acceptance criterion, on both refs the reconciliation will read.

        This is not a rare shape: it is a checkout that has not fetched, and until #353 was
        closed it produced DIVERGED - the loudest of the four - which an agent following the
        resume protocol would read as the record being untrustworthy.
        """
        for case in ("behind_local_main", "behind_origin_main"):
            with self.subTest(case=case):
                self.assertEqual("UNKNOWN", self.verdict(case), self.reason(case))

    def test_the_behind_reason_names_the_staleness_and_not_a_divergence(self) -> None:
        """The verdict alone does not close #353; UNKNOWN with a divergence's reason would not.

        A reader is told WHICH unavailability this is, because UNKNOWN covers five of them. What
        the reason may NOT do is say why, and the last conjunct below is a repair rather than a
        precaution: this reason ended "it has not been fetched", which is a cause asserted in a
        sentence whose job is to assert what was measured - the same thing the DIVERGED reason is
        forbidden from doing with "rebase" and "force-push". It is also not always true. A
        baseline recorded from a branch that never merged gives exactly this shape with the main
        ref fully current, and fetching would fix nothing there.

        So the cause may be OFFERED as common and never ASSERTED as established, and the rule is
        checkable rather than a matter of taste: if the reason mentions fetching at all, it must
        also say that this is the common cause. Two controls trip this - one restoring the bare
        claim, one removing the measured half.
        """
        for case in ("behind_local_main", "behind_origin_main"):
            with self.subTest(case=case):
                reason = self.reason(case)
                self.assertIn("is an ancestor of the recorded baseline", reason)
                self.assertIn("BEHIND the record", reason)
                self.assertIn("cannot be read from here", reason)
                for overclaim in ("is present in this clone but is not",
                                  "neither line contains the other"):
                    self.assertNotIn(overclaim, reason)
                if "fetched" in reason:
                    self.assertIn(
                        "common cause", reason,
                        "a cause may be offered as the common one and never asserted as the "
                        "established one; nothing reached here establishes why the ref is behind")

    def test_the_behind_fixtures_really_are_behind_and_not_merely_unrelated(self) -> None:
        """Otherwise the two tests above pass on a fixture that reproduces the wrong condition.

        Three facts are measured with this module's own git calls: the baseline is in the object
        database, so the run reaches the ancestry branch at all rather than stopping earlier; the
        baseline is NOT an ancestor of the main ref, which is what used to print DIVERGED; and
        the main ref IS an ancestor of the baseline, which is the fact that separates the two.
        """
        for case, (root, baseline) in self.behind_repositories.items():
            with self.subTest(case=case):
                ref, tip = main_line_tip(root)
                self.assertEqual(0, git(root, "cat-file", "-e", f"{baseline}^{{commit}}").returncode,
                                 f"{case}: the baseline must be in the object database")
                self.assertEqual(1, git(root, "merge-base", "--is-ancestor", baseline, tip).returncode,
                                 f"{case}: the baseline must NOT be an ancestor of {ref}")
                self.assertEqual(0, git(root, "merge-base", "--is-ancestor", tip, baseline).returncode,
                                 f"{case}: {ref} must be an ancestor of the baseline")

    def test_the_diverged_reason_is_true_of_the_condition_that_reaches_it(self) -> None:
        """The sentence is held to what git says about the fixture, not to what it sounds like.

        This test exists because the previous wording was measured FALSE: it said "the record was
        branched from a history this repository does not carry", and DIVERGED is reachable only
        AFTER `cat-file -e` proves the baseline IS in the object database. Both fixtures print it,
        so both are checked here, and the check is that the baseline is PRESENT - the opposite of
        what the sentence used to assert.
        """
        for case, (root, baseline) in self.diverged_repositories.items():
            with self.subTest(case=case):
                self.assertEqual("DIVERGED", self.verdict(case), self.reason(case))
                present = git(root, "cat-file", "-e", f"{baseline}^{{commit}}")
                self.assertEqual(0, present.returncode,
                                 f"{case}: DIVERGED can only be reached with the baseline present")
                tip = main_line_tip(root)[1]
                ancestry = git(root, "merge-base", "--is-ancestor", baseline, tip)
                self.assertEqual(1, ancestry.returncode,
                                 f"{case}: the fixture must not be an ancestor of the main line")
                # THE SECOND DIRECTION, added with #353. Not-an-ancestor alone is also true of a
                # main ref that is merely behind, and asserting only the first direction let a
                # fixture that reproduced THAT condition satisfy a test named for divergence.
                # Both fixtures must be genuinely two-way, or the word is being checked against
                # the wrong history.
                self.assertEqual(1, git(root, "merge-base", "--is-ancestor", tip, baseline).returncode,
                                 f"{case}: the main line must not be an ancestor of the baseline "
                                 f"either, or this fixture is a stale ref rather than a divergence")
                self.assertIn("is present in this clone", self.reason(case))
                self.assertIn("is not an ancestor of", self.reason(case))
                self.assertIn("neither line contains the other", self.reason(case))
                # The two facts above are all the code has established at that point. Anything
                # about WHY they parted - a rebase, a force-push, an unrelated line of work - is
                # not distinguishable by any call this function makes, so it may not be claimed.
                for overclaim in ABSENCE_CLAIMS + ("rebase", "force-push"):
                    self.assertNotIn(overclaim, self.reason(case))

    def test_the_diverged_entry_of_the_docstring_makes_the_same_claim(self) -> None:
        """The prose that DOCUMENTS the branch is held to the same claim as the prose it PRINTS.

        Written from a review finding rather than from foresight. The identical overclaim - "the
        record was branched from a history this repository does not have" - survived seventy lines
        above the repair, in the docstring entry for the same branch, because the check that
        removed it read the REASON and only the reason. A guard scoped to one string's LOCATION
        cannot see the same claim written somewhere else, and the reason and this entry are two
        statements of one fact.
        """
        entry = vocabulary_entry("DIVERGED")
        self.assertTrue(entry, "the DIVERGED entry of the docstring could not be read at all")
        self.assertIn("IS in this clone", entry,
                      "the entry must state that the baseline is PRESENT, which is what "
                      "`cat-file -e` established before this branch can be reached")
        self.assertIn("neither line contains the other", entry,
                      "the entry must state BOTH directions, because not-an-ancestor alone is "
                      "also true of a main ref that is merely behind - which is #353")
        for overclaim in ABSENCE_CLAIMS:
            self.assertNotIn(overclaim, entry)

    def test_the_unknown_entry_of_the_docstring_names_the_behind_case(self) -> None:
        """The word a stale ref now reports must document that it covers a stale ref.

        UNKNOWN carries five distinct unavailabilities and a reader meeting it needs the entry to
        name the one #353 moved here, or the repair is invisible in the prose that documents it.
        """
        entry = vocabulary_entry("UNKNOWN")
        self.assertTrue(entry, "the UNKNOWN entry of the docstring could not be read at all")
        self.assertIn("BEHIND", entry)
        self.assertIn("#353", entry)

    def test_the_docstring_reader_can_tell_the_entries_apart(self) -> None:
        """Without this the check above passes hardest when the reader stops finding anything."""
        self.assertEqual("", vocabulary_entry("NO_SUCH_WORD"))
        for word in VOCABULARY:
            self.assertTrue(vocabulary_entry(word), f"no docstring entry for {word}")
        # UNKNOWN legitimately says the clone does NOT hold a commit - that is what UNKNOWN means.
        # It is the reason the forbidden strings are scoped to one entry rather than swept over
        # the whole docstring, and this asserts the reader really does separate them.
        self.assertIn("does not hold", vocabulary_entry("UNKNOWN"))
        self.assertNotIn("does not hold", vocabulary_entry("DIVERGED"))

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
