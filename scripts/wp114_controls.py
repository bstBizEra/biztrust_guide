#!/usr/bin/env python3
"""Negative controls for BIZTRUST-GUIDE-WP-114's stale-main-ref repair (#353, #357).

`scripts/wp112_controls.py` is the model and this file follows it, including the one difference
that file exists for: THE SUBJECT IS GIT HISTORY, so each control CLONES the repository rather than
copying it. A copy without `.git` answers UNKNOWN to everything, which is the answer these controls
most need to tell apart from a real one.

A clone carries COMMITTED state. Run this against a committed tree, or it will measure the previous
commit and say so by disagreeing with the suite you just ran.

`check_source_main_line` below is WP-112's, unchanged in behaviour: it refuses a source whose local
`main` carries commits its `origin/main` does not, and allows the opposite direction. That guard
exists because a stray command once committed onto the shared checkout's local `main` and every
control went red for a reason that had nothing to do with the code.

WHAT THE DEFECT WAS. `reconcile_recorded_state` returned DIVERGED whenever the recorded baseline was
in the object database but was not an ancestor of the observed main line. One ordering produces that
shape innocently and it is the commonest state of a long-lived checkout: a main ref that has simply
not been fetched sits BEHIND the baseline. Measured on a clone with `origin/main` set to the commit
before the recorded baseline, before the repair:

    STATE_RECONCILIATION=DIVERGED
    STATE_RECONCILIATION_REASON=... the recorded baseline ... is present in this clone but is not
    an ancestor of refs/remotes/origin/main ..., so the main line does not descend from where the
    record says it branched

and after it, on the same clone:

    STATE_RECONCILIATION=UNKNOWN
    STATE_RECONCILIATION_REASON=... refs/remotes/origin/main ... is an ancestor of the recorded
    baseline ..., so this clone's main ref is BEHIND the record rather than parted from it - it has
    not been fetched ...

SCRIPT CONTROLS 1 TO 4 ARE THAT MEASUREMENT, run as controls rather than quoted. Each is a pair
whose second member removes the guard that makes the first member's answer what it is, so neither
verdict is what it is by accident.

FOUR KINDS OF CONTROL.

  SUITE controls mutate `scripts/validate_continuity.py` - or, in one case, the test module's own
  fixture - in a full clone, run

      python -m unittest discover -s tests -p test_resume_reconciliation.py -v

  from that clone's root, and assert the NAMED test fails.

  ONE SUITE CONTROL EXPECTS GREEN. It is a DECLARED HOLE - limit 10 of
  `tests/test_resume_reconciliation.py` - and it is here so that limit is demonstrated rather than
  claimed. If it starts failing the hole has closed and the limit must be re-derived, not deleted.

  SCRIPT controls run `python scripts/validate_continuity.py` in a clone whose `origin/main` has
  been moved, and assert the printed verdict and the exit code. Both of #353's acceptance criteria
  are demonstrated here rather than asserted: a behind main ref reports UNKNOWN, and a genuinely
  divergent one still reports DIVERGED.

  A MEASUREMENT control proves a SENTENCE rather than a guard. #357 is a docstring sentence that was
  false when written, and correcting it without measuring it would repeat the error that produced
  it; this control re-runs the sentence's own filter against a fresh clone and compares.

WHY EVERY CLONE READS THE BEHIND CASE ON ITS LIVE TREE, which is worth knowing before reading the
isolation column. A clone's `origin/main` IS the source's `refs/heads/main`, and a shared checkout
whose local `main` has been fetched but not pulled is behind its own `origin/main`. So a clone made
from such a source carries a record whose baseline is AHEAD of the clone's `origin/main` - #353's
exact shape - and `test_the_live_reading_agrees_with_the_history_measured_here` takes its BEHIND
branch. That is why several controls below trip the live test as well as the fixture test they are
named for: they are not isolated, and the runner prints so.

THE ROT RISK, stated plainly because this file is committed. A control script that nothing runs
looks like evidence and is not. It is DELIBERATELY NOT WIRED INTO CI: every control makes a fresh
clone and runs a suite or a validator inside it, which is minutes of work repeated on every push,
and `scripts/validate_continuity.py` is the instrument every other gate in this repository is read
through - a CI step that flaked here would be removed rather than fixed. Run this before changing
the reconciliation, and before believing any sentence the test module's docstring states about what
it catches.

It lives in `scripts/` and not `tests/` on purpose: `unittest discover -s tests` must not collect
it, and it clones repositories, which is not a thing `tests/` should do on every push.

Usage:  python scripts/wp114_controls.py [<repository>] [<scratch>]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PYTHON = sys.executable

VALIDATOR = "scripts/validate_continuity.py"
TEST_MODULE = "tests/test_resume_reconciliation.py"
STATE = "badf/current-state.json"

# --- the exact text each mutation replaces -------------------------------------------------------

REVERSE_QUESTION = (
    "        # #353: NOT-AN-ANCESTOR IS TWO CASES AND ONLY ONE OF THEM IS A FAULT, so ask the reverse\n"
)
BEHIND_CALL = '        behind = git(root, "merge-base", "--is-ancestor", tip_sha, baseline)\n'
BEHIND_TEST = "        if behind[0] == 0:\n"
BEHIND_VERDICT = '            return "UNKNOWN", (\n                f"{wp_id}: {tip_ref} ({tip_sha[:12]}) is an ancestor of the recorded baseline "\n'
BEHIND_STALENESS = (
    '                f"parted from it - it has not been fetched, and what landed after the baseline "\n'
    '                f"cannot be read from here"\n'
)
THIRD_OUTCOME = (
    "        if behind is None or behind[0] not in (0, 1):\n"
)
DIVERGED_ENTRY = (
    "                  observed main line, AND the observed main line is not an ancestor of the\n"
    "                  baseline either, so neither line contains the other. Nothing reachable from\n"
    "                  here says WHY the two parted, so this entry does not say. The second half of\n"
    "                  that test is #353's repair: not-an-ancestor ALONE is also true of a main ref\n"
    "                  that has simply not been fetched - it sits behind the baseline - and this\n"
    "                  word, the loudest of the four, was printed for a stale ref rather than a\n"
    "                  fault. Measured before the repair, with `origin/main` set to the commit\n"
    "                  before the recorded baseline: DIVERGED. Measured after it, on the same\n"
    "                  clone: UNKNOWN, naming the staleness.\n"
)
DIVERGED_ENTRY_AT_ONE_DIRECTION = (
    "                  observed main line, so the main line does not descend from it. Nothing\n"
    "                  reachable from here says WHY the two parted, so this entry does not say.\n"
)
UNKNOWN_ENTRY_BEHIND = (
    "                  clone, no main ref, a baseline commit this clone does not hold, or a main ref\n"
    "                  that sits BEHIND the recorded baseline because it has not been fetched, in\n"
    "                  which case the record is ahead of the observation and what landed after the\n"
    "                  baseline cannot be read from here at all (#353).\n"
)
REBASED_FIXTURE = (
    '        rebased = build_repo(base / "rebased")\n'
    '        add_commit(rebased, "[BIZTRUST-GUIDE-WP-900] the root")\n'
    '        git_ok(rebased, "checkout", "--quiet", "-b", "before")\n'
    '        rebased_baseline = add_commit(rebased, "[BIZTRUST-GUIDE-WP-901] the commit as it was")\n'
    '        git_ok(rebased, "checkout", "--quiet", "main")\n'
    '        add_commit(rebased, "[BIZTRUST-GUIDE-WP-901] the commit as it was, rewritten")\n'
)

# The whole #353 block, from its opening comment to the end of the BEHIND return. Deleting it
# restores the code exactly as it stood before this package: not-an-ancestor, and nothing else,
# reaching DIVERGED.
BEHIND_BLOCK_TAIL = '                f"cannot be read from here"\n            )\n'


def read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def edit(root: Path, rel: str, old: str, new: str) -> None:
    """Replace `old` with `new` exactly once, and refuse to be a no-op."""
    path = root / rel
    text = path.read_text(encoding="utf-8")
    found = text.count(old)
    if found != 1:
        raise AssertionError(f"{rel}: expected exactly one occurrence of {old[:70]!r}, found {found}")
    path.write_text(text.replace(old, new), encoding="utf-8", newline="")


def cut(root: Path, rel: str, opening: str, closing: str) -> None:
    """Delete from the start of `opening` to the end of `closing`, both required to be unique."""
    path = root / rel
    text = path.read_text(encoding="utf-8")
    for marker in (opening, closing):
        if text.count(marker) != 1:
            raise AssertionError(
                f"{rel}: expected exactly one occurrence of {marker[:70]!r}, "
                f"found {text.count(marker)}")
    start = text.index(opening)
    end = text.index(closing, start) + len(closing)
    path.write_text(text[:start] + text[end:], encoding="utf-8", newline="")


# --- the mutations -------------------------------------------------------------------------------


def the_reverse_question_never_asked(root: Path) -> None:
    """THE DEFECT RESTORED: the code exactly as it stood before this package.

    Not-an-ancestor alone reaches DIVERGED, so a main ref that has merely not been fetched gets
    the loudest word in the vocabulary for a stale ref. This is #353's first acceptance criterion
    demonstrated by removal.
    """
    cut(root, VALIDATOR, REVERSE_QUESTION, BEHIND_BLOCK_TAIL)


def the_reverse_question_asked_in_the_wrong_direction(root: Path) -> None:
    """The arguments swapped, which is the easy way to write this call wrongly.

    `merge-base --is-ancestor A B` asks whether A precedes B and the order is the whole meaning.
    Swapped, the call repeats the question already answered on the line above, always returns 1,
    and every behind ref falls through to DIVERGED - the defect, restored by a subtler route than
    the control above and tripping the same test, which is how the test is known to be about the
    ANSWER rather than about the presence of a second call.
    """
    edit(root, VALIDATOR, BEHIND_CALL,
         '        behind = git(root, "merge-base", "--is-ancestor", baseline, tip_sha)\n')


def a_divergence_reported_as_a_stale_ref(root: Path) -> None:
    """#353's SECOND acceptance criterion, demonstrated by breaking it.

    The repair must not swallow the word it narrows. With the behind test widened to accept both
    answers, DIVERGED becomes unreachable and a genuinely parted history - an orphan branch, a
    rebase - is reported as a clone that merely needs fetching, which is a worse error than the one
    being fixed: it tells a reader to run `git fetch` at a record that is actually wrong.
    """
    edit(root, VALIDATOR, BEHIND_TEST, "        if behind[0] in (0, 1):\n")


def the_behind_case_told_correctly_and_named_diverged(root: Path) -> None:
    """The right diagnosis under the wrong word: the reason names the staleness, the verdict does
    not. A reader who acts on the word rather than on the sentence is back where #353 started."""
    edit(root, VALIDATOR, BEHIND_VERDICT,
         '            return "DIVERGED", (\n'
         '                f"{wp_id}: {tip_ref} ({tip_sha[:12]}) is an ancestor of the recorded baseline "\n')


def the_staleness_dropped_from_the_behind_reason(root: Path) -> None:
    """The right word with a reason that does not say what to do about it.

    UNKNOWN covers five distinct unavailabilities and only this one is repaired by fetching. #353
    requires the reason to name the staleness, not merely the verdict to be UNKNOWN, which is why
    the wording is asserted for this case and not for the degraded ones.
    """
    edit(root, VALIDATOR, BEHIND_STALENESS,
         '                f"parted from it"\n')


def the_diverged_docstring_left_at_one_direction(root: Path) -> None:
    """The prose that DOCUMENTS the branch held to the same claim as the prose it PRINTS.

    WP-112 lost a round to exactly this shape: the identical overclaim survived seventy lines above
    its repair because the guard that removed it read the reason and only the reason.
    """
    edit(root, VALIDATOR, DIVERGED_ENTRY, DIVERGED_ENTRY_AT_ONE_DIRECTION)


def the_unknown_docstring_silent_about_the_behind_case(root: Path) -> None:
    """UNKNOWN is now where a stale ref lands, and the entry that defines it must say so."""
    edit(root, VALIDATOR, UNKNOWN_ENTRY_BEHIND,
         "                  clone, no main ref, or a baseline commit this clone does not hold.\n")


def a_diverged_fixture_that_is_merely_behind(root: Path) -> None:
    """A FIXTURE mutation, not a code one, and it is what makes the DIVERGED tests worth anything.

    It rebuilds the `rebased` fixture as a main ref that is simply behind its baseline. Before
    #353 the two conditions were indistinguishable to the code, so a fixture of this shape would
    have satisfied a test named for divergence while reproducing the opposite condition. The
    two-way assertion added to `test_the_diverged_reason_is_true_of_the_condition_that_reaches_it`
    is what refuses it, and this control is that assertion's demonstration.
    """
    edit(root, TEST_MODULE, REBASED_FIXTURE,
         '        rebased = build_repo(base / "rebased")\n'
         '        rebased_first = add_commit(rebased, "[BIZTRUST-GUIDE-WP-900] the root")\n'
         '        rebased_baseline = add_commit(rebased, "[BIZTRUST-GUIDE-WP-901] the commit as it was")\n'
         '        git_ok(rebased, "branch", "fetched", rebased_baseline)\n'
         '        git_ok(rebased, "update-ref", "refs/heads/main", rebased_first)\n')


def the_third_outcome_falling_through_to_diverged(root: Path) -> None:
    """THE DECLARED HOLE, and this control asserts the suite stays GREEN.

    `git merge-base --is-ancestor` answers 0, 1 or an error, and this replaces the error branch's
    UNKNOWN with a fall-through to DIVERGED - the other reasonable decision, and the one the code
    argues against in its own comment. Nothing in the suite notices, because no fixture reaches
    that branch and none can without mocking: the identical call in the opposite direction has
    already succeeded by then, so only a timeout or an unrunnable git gets here. Limit 10 of
    `tests/test_resume_reconciliation.py` is written from this control.

    If it ever goes red the hole has closed and that limit must be re-derived, not deleted.
    """
    edit(root, VALIDATOR, THIRD_OUTCOME,
         "        if behind is None or behind[0] not in (0, 1):\n"
         "            behind = (1, \"\")\n"
         "        if False:\n")


SUITE_CONTROLS = [
    ("THE DEFECT RESTORED: the reverse question never asked", the_reverse_question_never_asked,
     "test_a_main_ref_behind_the_recorded_baseline_is_unknown_and_not_diverged"),
    ("the reverse question asked in the wrong direction",
     the_reverse_question_asked_in_the_wrong_direction,
     "test_a_main_ref_behind_the_recorded_baseline_is_unknown_and_not_diverged"),
    ("a genuine divergence reported as a stale ref", a_divergence_reported_as_a_stale_ref,
     "test_diverged_when_the_baseline_is_not_an_ancestor_of_the_main_line"),
    ("the behind case diagnosed correctly and still called DIVERGED",
     the_behind_case_told_correctly_and_named_diverged,
     "test_a_main_ref_behind_the_recorded_baseline_is_unknown_and_not_diverged"),
    ("the staleness dropped from the behind reason", the_staleness_dropped_from_the_behind_reason,
     "test_the_behind_reason_names_the_staleness_and_not_a_divergence"),
    ("the DIVERGED docstring entry left at one direction",
     the_diverged_docstring_left_at_one_direction,
     "test_the_diverged_entry_of_the_docstring_makes_the_same_claim"),
    ("the UNKNOWN docstring entry silent about the behind case",
     the_unknown_docstring_silent_about_the_behind_case,
     "test_the_unknown_entry_of_the_docstring_names_the_behind_case"),
    ("a DIVERGED fixture that is merely behind", a_diverged_fixture_that_is_merely_behind,
     "test_diverged_after_a_rebase_too"),
    # HOLE, not a defect: expected GREEN. See the_third_outcome_falling_through_to_diverged.
    ("DECLARED HOLE: the third outcome falling through to DIVERGED",
     the_third_outcome_falling_through_to_diverged, None),
]

FAILED = re.compile(r"^(?:FAIL|ERROR): (\w+) ", re.M)
VERDICT = re.compile(r"^STATE_RECONCILIATION=(\w+)$", re.M)


def clone(source: Path, into: Path, name: str) -> Path:
    root = into / name
    done = subprocess.run(["git", "clone", "--quiet", str(source), str(root)],
                          capture_output=True, text=True, timeout=600)
    if done.returncode != 0:
        raise AssertionError(f"clone of {source} failed: {done.stdout}{done.stderr}")
    return root


def git_out(root: Path, *args: str) -> str:
    """One git command at `root`, refusing to return silence on failure."""
    done = subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=120)
    if done.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed in {root}: {done.stdout}{done.stderr}")
    return done.stdout.strip()


def ancestry(root: Path, earlier: str, later: str) -> int:
    """`merge-base --is-ancestor`, as an exit code, refusing anything but 0 or 1."""
    done = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", earlier, later],
                          capture_output=True, text=True, timeout=120)
    if done.returncode not in (0, 1):
        raise AssertionError(f"merge-base --is-ancestor failed in {root}: {done.stdout}{done.stderr}")
    return done.returncode


def recorded_baseline(root: Path) -> str:
    """READ FROM THE RECORD, never written literally.

    WP-112 lost three of nineteen controls to expectations that depended on the record they
    happened to run against, and the rule it left is that a control which pins a recorded value
    is not a control.
    """
    return json.loads(read(root, STATE))["source"]["baseline_commit"]


def clone_with_a_stale_main_ref(source: Path, into: Path, name: str) -> Path:
    """A clone whose `origin/main` sits at the commit BEFORE the recorded baseline.

    #353's measured shape. Three facts are asserted before the control is allowed to mean
    anything, because a fixture that reproduces the wrong condition reports PASS: the baseline is
    in the object database, so the run reaches the ancestry branch rather than stopping earlier;
    the baseline is NOT an ancestor of the moved ref, which is what used to print DIVERGED; and
    the moved ref IS an ancestor of the baseline, which is the fact that separates the two.
    """
    root = clone(source, into, name)
    baseline = recorded_baseline(root)
    stale = git_out(root, "rev-parse", f"{baseline}~1^{{commit}}")
    git_out(root, "update-ref", "refs/remotes/origin/main", stale)
    if subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"{baseline}^{{commit}}"],
                      capture_output=True, timeout=120).returncode != 0:
        raise AssertionError(f"{name}: the recorded baseline is not in the clone's object database")
    if ancestry(root, baseline, stale) != 1:
        raise AssertionError(f"{name}: the baseline is an ancestor of the moved ref, so this "
                             f"fixture does not reproduce the not-an-ancestor branch at all")
    if ancestry(root, stale, baseline) != 0:
        raise AssertionError(f"{name}: the moved ref is not an ancestor of the baseline, so this "
                             f"fixture is a divergence rather than a stale ref")
    return root


def clone_with_a_divergent_main_ref(source: Path, into: Path, name: str) -> Path:
    """A clone whose `origin/main` is a root commit sharing no history with the recorded baseline.

    Built with `commit-tree` over the existing tip's own tree and NO parent, so the working tree
    is untouched and the clone still carries the module under test. The same three facts are
    asserted, with the third inverted: NEITHER line contains the other, which is what DIVERGED
    must continue to mean after #353 narrows it.
    """
    root = clone(source, into, name)
    baseline = recorded_baseline(root)
    unrelated = git_out(root, "-c", "user.name=WP-114 control",
                        "-c", "user.email=wp114@invalid.example",
                        "commit-tree", f"{baseline}^{{tree}}",
                        "-m", "[BIZTRUST-GUIDE-WP-999] a main line that shares no history")
    git_out(root, "update-ref", "refs/remotes/origin/main", unrelated)
    if ancestry(root, baseline, unrelated) != 1:
        raise AssertionError(f"{name}: the baseline is an ancestor of the synthesised ref")
    if ancestry(root, unrelated, baseline) != 1:
        raise AssertionError(f"{name}: the synthesised ref is an ancestor of the baseline, so this "
                             f"fixture is a stale ref rather than a divergence")
    return root


# (name, how to build the clone, how to mutate it, the verdict the validator must print)
#
# Two pairs. In each, the first member is the demonstration and the second removes the guard that
# makes the first member's verdict what it is, so neither is what it is by accident. Together they
# are both acceptance criteria of #353, measured end to end on the script rather than on a return
# value - the same reason WP-112 demonstrated its shallow case with a script control.
SCRIPT_CONTROLS = [
    ("THE STALE-REF DEMONSTRATION: origin/main at the commit before the recorded baseline",
     clone_with_a_stale_main_ref, None, "UNKNOWN"),
    ("the same clone with the reverse question never asked, as the code stood before #353",
     clone_with_a_stale_main_ref, the_reverse_question_never_asked, "DIVERGED"),
    ("THE DIVERGENCE DEMONSTRATION: origin/main on a history sharing no commit with the baseline",
     clone_with_a_divergent_main_ref, None, "DIVERGED"),
    ("the same clone with the behind test widened to swallow a divergence",
     clone_with_a_divergent_main_ref, a_divergence_reported_as_a_stale_ref, "UNKNOWN"),
]

# --- the measurement control ---------------------------------------------------------------------
#
# #357: `tests/test_resume_reconciliation.py`'s docstring said "the rest of tests/ is
# subprocess-free", which was false when written and propagated by being copied into three further
# places. The corrected sentence names four modules and carries the command that measures them. A
# sentence corrected without being measured is the same defect written out again, so this control
# re-measures it.
#
# THE PATTERN IS READ OUT OF THE DOCSTRING rather than repeated here, so the control cannot drift
# from the command the sentence prints. The filter is applied with Python's `re` rather than by
# invoking `grep`, because `grep` is not on every runner this repository is used from; what is
# proved is the sentence's PATTERN against the tree, not the availability of a POSIX tool.
SUBPROCESS_PATTERN = re.compile(r"grep -lnE \"([^\"]+)\" tests/\*\.py")
NAMED_MODULE = re.compile(r"`?(test_[a-z0-9_]+\.py)`?")


def the_subprocess_sentence_measured(root: Path) -> tuple[bool, str]:
    """Read the sentence's own pattern and its own list, then measure the tree against both."""
    doc = read(root, TEST_MODULE)
    opening = doc.index('"""')
    head = doc[opening + 3:doc.index('"""', opening + 3)]
    found = SUBPROCESS_PATTERN.search(head)
    if not found:
        return False, "the docstring carries no `grep -lnE ... tests/*.py` command to measure"
    pattern = re.compile(found.group(1))
    measured = sorted(path.name for path in sorted((root / "tests").glob("*.py"))
                      if pattern.search(path.read_text(encoding="utf-8")))
    # The names the sentence itself lists, taken from the paragraph the command sits in.
    claimed = sorted(set(NAMED_MODULE.findall(head[:found.start()] + head[found.end():])))
    if measured != claimed:
        return False, f"the docstring names {claimed}; the tree measures {measured}"
    # And the word, which is the wrong filter and returns more. If it ever returns the same set the
    # warning in the docstring has stopped being about anything.
    word = sorted(path.name for path in sorted((root / "tests").glob("*.py"))
                  if "subprocess" in path.read_text(encoding="utf-8"))
    if len(word) <= len(measured):
        return False, (f"grepping for the WORD returns {word}, which is no larger than the "
                       f"measured set {measured}; the docstring's warning describes nothing")
    return True, f"{len(measured)} modules call one, {len(word)} mention the word: {measured}"


def run_suite(root: Path) -> tuple[int, set[str]]:
    done = subprocess.run(
        [PYTHON, "-m", "unittest", "discover", "-s", "tests",
         "-p", "test_resume_reconciliation.py", "-v"],
        cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    return done.returncode, set(FAILED.findall(done.stdout + done.stderr))


def run_validator(root: Path) -> tuple[int, str]:
    done = subprocess.run([PYTHON, "-B", str(root / VALIDATOR)], cwd=root,
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=600)
    found = VERDICT.findall(done.stdout)
    return done.returncode, found[0] if len(found) == 1 else f"<{len(found)} verdict lines>"


def check_source_main_line(source: Path) -> str:
    """Refuse to run when the source's local `main` carries commits its `origin/main` does not.

    WP-112's guard, kept unchanged. A clone's `origin/main` IS the source's `refs/heads/main`, so
    every control below reads the source's LOCAL main line whatever the source's own `origin/main`
    says.

    ONE DIRECTION ONLY. Local `main` AHEAD of `origin/main` is REFUSED: that is the incident that
    produced the check - a stray command committed onto local `main`, the worktree suite stayed
    green because it reads `origin/main`, and every clone went red on a corroboration that found a
    commit landing no Work Package. Local `main` BEHIND `origin/main` is ALLOWED, because it is the
    ordinary state of a checkout that has fetched and not pulled, and refusing it would be a false
    failure of exactly the kind the check exists to prevent.

    THAT ALLOWED DIRECTION IS NOW ALSO THE SUBJECT. Since #353 a clone made from such a source
    reads UNKNOWN rather than DIVERGED on its live tree, and the module's live test asserts the
    staleness. That is a reason to keep this guard narrow, not a reason to widen it.
    """
    def ref(name: str) -> str:
        done = subprocess.run(["git", "-C", str(source), "rev-parse", "--verify", "--quiet",
                               f"{name}^{{commit}}"], capture_output=True, text=True, timeout=60)
        return done.stdout.strip() if done.returncode == 0 else ""

    local, published = ref("refs/heads/main"), ref("refs/remotes/origin/main")
    if not local or not published or local == published:
        return local or published
    if ancestry(source, local, published) == 0:
        return local
    subject = subprocess.run(["git", "-C", str(source), "log", "-1", "--format=%s", local],
                             capture_output=True, text=True, timeout=60).stdout.strip()
    raise SystemExit(
        f"REFUSING TO RUN. {source}: refs/heads/main is {local[:12]} {subject!r}, which carries "
        f"commits refs/remotes/origin/main ({published[:12]}) does not. Every clone below would "
        f"take its origin/main from that local branch, so the live-tree control would measure the "
        f"drift rather than this package's code. Reconcile the source's main first.")


def main() -> int:
    source = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    holder = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(tempfile.mkdtemp())
    holder.mkdir(parents=True, exist_ok=True)
    check_source_main_line(source)
    bad = 0

    unmutated = clone(source, holder, "control_00_unmutated")
    code, failures = run_suite(unmutated)
    print(f"[{'PASS' if code == 0 else 'BAD '}] unmutated clone: exit {code}, "
          f"failures {sorted(failures) or 'none'}")
    if code != 0:
        print("       the unmutated clone is already red; every control below proves nothing")
        bad += 1

    ok, detail = the_subprocess_sentence_measured(unmutated)
    bad += 0 if ok else 1
    print(f"[{'PASS' if ok else 'BAD '}] MEASUREMENT: the #357 sentence against the tree it describes")
    print(f"       {detail}")

    for index, (name, mutate, expected) in enumerate(SUITE_CONTROLS, start=1):
        root = clone(source, holder, f"control_{index:02d}")
        mutate(root)
        code, failures = run_suite(root)
        if expected is None:
            # A DECLARED HOLE. The mutation is a real change of behaviour and the suite is expected
            # to stay green, because nothing in it reaches the branch the mutation changes. A
            # control that demonstrates a limit cannot drift away from the code without this
            # script noticing.
            ok = code == 0 and not failures
            bad += 0 if ok else 1
            print(f"[{'PASS' if ok else 'BAD '}] {name}")
            print(f"       DECLARED HOLE: expected the suite to stay GREEN; exit {code}; "
                  f"failed: {sorted(failures) or 'nothing'}"
                  f"{'' if ok else '  <- the hole has closed; re-derive the limit that declares it'}")
            continue
        ok = code != 0 and expected in failures
        isolated = failures == {expected}
        bad += 0 if ok else 1
        print(f"[{'PASS' if ok else 'BAD '}] {name}")
        print(f"       expected {expected} to fail; exit {code}; "
              f"failed: {sorted(failures) or 'NOTHING'}"
              f"{'' if isolated else '  <- NOT ISOLATED' if ok else ''}")

    for index, (name, build, mutate, expected) in enumerate(SCRIPT_CONTROLS, start=1):
        root = build(source, holder, f"script_{index:02d}")
        if mutate is not None:
            mutate(root)
        code, verdict = run_validator(root)
        ok = code == 0 and verdict == expected
        bad += 0 if ok else 1
        print(f"[{'PASS' if ok else 'BAD '}] {name}")
        print(f"       expected STATE_RECONCILIATION={expected} and exit 0; "
              f"got {verdict} and exit {code}")

    total = len(SUITE_CONTROLS) + len(SCRIPT_CONTROLS) + 1
    print(f"\n{total} controls, {bad} not behaving as declared")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
