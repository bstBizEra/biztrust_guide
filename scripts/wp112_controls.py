#!/usr/bin/env python3
"""Negative controls for BIZTRUST-GUIDE-WP-112's step-8 reconciliation (#345, #351).

`scripts/wp111_controls.py` is the model and this file follows it: one mutation per fresh copy,
the unmutated copy first, every mutation asserting that the text it replaces was actually there so
a control cannot quietly become a no-op.

ONE DIFFERENCE FROM THE MODEL, and it is the reason this file exists at all. WP-111's controls
copied the tree with `shutil.copytree` and dropped `.git`. The subject here IS git history, so a
copy without it measures nothing: every verdict in such a copy is UNKNOWN, which is the answer
these controls most need to distinguish from a real one. So each control CLONES the repository
instead, and the clone is genuine - full history for the suite controls, `--depth 1` over `file://`
for the shallow one, because git ignores `--depth` on a plain local path.

That has a consequence worth stating: a clone carries COMMITTED state. Run this against a
committed tree, or it will measure the previous commit and say so by disagreeing with the suite you
just ran.

THREE KINDS OF CONTROL.

  SUITE controls mutate `scripts/validate_continuity.py` in a full clone, run

      python -m unittest discover -s tests -p test_resume_reconciliation.py -v

  from that clone's root, and assert the NAMED test fails.

  ENVIRONMENT controls mutate nothing in the first of each pair. They put an UNMUTATED tree into a
  situation it must survive and assert the suite stays GREEN. Two situations, two pairs:

    * a working tree sitting in a SUBDIRECTORY of a clone of this repository. A test that goes red
      for where the tree was unpacked fails for an environment reason, which is the flakiness #311
      keeps out of this suite.
    * a clone whose `origin/main` carries ONE MORE Work Package than the record knows - the merge
      that is coming. Until review caught it, the live test required the main line's TIP to be the
      recorded package's merge, so merging this very package would have broken this very package's
      test, green in CI because CI is shallow.

  The second of each pair removes the check that makes the first green and shows the same
  environment go RED, so the green is known to come from the check rather than from luck.

  SCRIPT controls run `python scripts/validate_continuity.py` in a SHALLOW clone and assert the
  printed verdict and exit code. The brief for this package required the shallow case to be
  demonstrated rather than asserted, and a test module cannot demonstrate it end to end: the
  degradation is a property of the script's exit code, not of a return value. The first script
  control is the demonstration - UNKNOWN, exit 0, on a genuinely shallow clone. The second exists
  because the first is worthless alone: it weakens the shallow guard and shows the same clone then
  reports CONSISTENT, so the UNKNOWN in the first is produced by the guard rather than by accident.

TWO SUITE CONTROLS EXPECT GREEN. Each is a DECLARED HOLE - a real thing this guard does not catch -
and they are here so that limits 5 and 7 of `tests/test_resume_reconciliation.py` are demonstrated
rather than claimed. If either starts failing, that hole has closed and its limit must be
re-derived, not deleted.

THE ROT RISK, stated plainly because this file is committed. A control script that nothing runs
looks like evidence and is not. It is DELIBERATELY NOT WIRED INTO CI: every control makes a fresh
clone, and all but the two shallow-clone controls then run the whole module suite on top of it -
which is minutes of work, repeated, on every push. `scripts/validate_continuity.py` is also the
instrument every other gate in this repository is read through, and a CI step that flaked here
would be removed rather than fixed. Run this before changing the reconciliation, and before
believing any sentence the test module's docstring states about what it catches.

It lives in `scripts/` and not `tests/` on purpose: `unittest discover -s tests` must not collect
it, and it clones repositories, which is not a thing `tests/` should do on every push.

THE CLONE, THE MUTATION HELPER, THE SUITE RUN AND THE REPORTING LOOP now come from
`scripts/control_harness.py` (#368), which classified every divergence across the six runners as
need or drift before moving anything. Two of this runner's differences survive as arguments rather
than being flattened: `--depth`, which only this runner passes, and Python's own newline
translation on the mutation helper's write. `check_source_main_line` below is deliberately NOT
shared: its docstring is this package's own recorded measurement, wp114's says something different
about the same guard, and their bodies differ in what happens when `merge-base` returns neither 0
nor 1. Adoption was gated on this runner's full output being byte-identical before and after, not
on the suite staying green.

Usage:  python scripts/wp112_controls.py [<repository>] [<scratch>]
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from control_harness import (HOLE_DECLARED, VERDICT, arguments, clone, git_out, report_unmutated,
                             run_script, run_suite, suite_controls, summarise)
from control_harness import edit as harness_edit

VALIDATOR = "scripts/validate_continuity.py"
STATE = "badf/current-state.json"

# --- the exact text each mutation replaces -------------------------------------------------------

MAIN_REFS = 'MAIN_REFS = ("refs/remotes/origin/main", "refs/heads/main")'
TOPLEVEL_GUARD = (
    '    if os.path.normcase(os.path.realpath(top[1])) != os.path.normcase(os.path.realpath(root)):\n'
    '        return "UNKNOWN", f"{wp_id}: {root} is not the root of the git repository that contains it"\n'
)
SHALLOW_GUARD = (
    '    if shallow[1] == "true":\n'
    '        return "UNKNOWN", (\n'
    '            f"{wp_id}: this clone is shallow, so the history before HEAD is absent and no "\n'
    '            f"ancestry can be established (the Pages workflow checks out without fetch-depth)"\n'
    '        )\n'
)
LANDINGS = '    landings = [subject for subject in subjects if subject.startswith(f"[{wp_id}]")]'
LAG_RETURN = '        return "LAG_EXPECTED", ('
DIVERGED_RETURN = '        return "DIVERGED", ('
SIGNATURE = 'def reconcile_recorded_state(root: Path, current: dict) -> tuple[str, str]:'
PRINT_BLOCK = (
    '    print(f"STATE_RECONCILIATION={verdict}")\n'
    '    print(f"STATE_RECONCILIATION_REASON={reason}")\n'
)
PASS_LINE = '    print("CONTINUITY_VALIDATION=PASS")\n'
RETURN_ZERO = (
    '    print(f"STATE_RECONCILIATION_REASON={reason}")\n'
    '    return 0\n'
)
RECORDED_STATE = '"state": "ENGINEERING_READY",'


def edit(root: Path, rel: str, old: str, new: str) -> None:
    """Replace `old` with `new` exactly once, and refuse to be a no-op.

    `newline=None` is the argument this runner alone shares with wp111: Python translates every
    line ending in the file on the way out, not just the ones inside the replacement. That is a
    real difference in the bytes written, which is why it is passed rather than quietly aligned
    with the four runners that write `newline=""`.
    """
    harness_edit(root, rel, old, new, newline=None)


# --- the mutations -------------------------------------------------------------------------------


def a_landing_reported_as_consistent(root: Path) -> None:
    """The live defect restored: the record's own merge on the main line reads as agreement."""
    edit(root, VALIDATOR, LAG_RETURN, '        return "CONSISTENT", (')


def any_movement_counted_as_a_landing(root: Path) -> None:
    """The easy wrong answer: every commit since the baseline read as this package landing.

    It would call every ordinary merge a lag, which is the reason LAG_EXPECTED is a separate word
    from DIVERGED rather than a synonym for "the main line moved".
    """
    edit(root, VALIDATOR, LANDINGS, "    landings = list(subjects)")


def the_package_id_matched_anywhere_in_the_subject(root: Path) -> None:
    """A commit that MENTIONS the package - a revert, a follow-up - is not that package landing."""
    edit(root, VALIDATOR, LANDINGS,
         '    landings = [subject for subject in subjects if f"[{wp_id}]" in subject]')


def the_shallow_guard_removed(root: Path) -> None:
    """A shallow clone still answers UNKNOWN by the absent baseline - with the WRONG reason.

    The verdict alone cannot see this. The reason is what tells a reader whether the answer is
    about their clone or about their record, so the reason is what the suite asserts.
    """
    edit(root, VALIDATOR, SHALLOW_GUARD, "")


def the_enclosing_repository_guard_removed(root: Path) -> None:
    """Without it, a tree unpacked inside some other checkout is judged against THAT history."""
    edit(root, VALIDATOR, TOPLEVEL_GUARD, "")


def a_foreign_baseline_reported_as_consistent(root: Path) -> None:
    edit(root, VALIDATOR, DIVERGED_RETURN, '        return "CONSISTENT", (')


def head_added_as_a_fallback_main_ref(root: Path) -> None:
    """HEAD is a Work Package branch's own tip; reading it as the main line reports the branch."""
    edit(root, VALIDATOR, MAIN_REFS,
         'MAIN_REFS = ("refs/remotes/origin/main", "refs/heads/main", "HEAD")')


def the_reconciliation_not_printed(root: Path) -> None:
    """Computed and dropped. Step 8 is only performed if step 7's reader can see the answer."""
    edit(root, VALIDATOR, PRINT_BLOCK, "")


def the_reconciliation_printed_away_from_the_resume_decision(root: Path) -> None:
    """Printed, but above the verdict line rather than beside the two lines step 7 already reads."""
    edit(root, VALIDATOR, PRINT_BLOCK, "")
    edit(root, VALIDATOR, PASS_LINE, PRINT_BLOCK + PASS_LINE)


def the_advisory_made_fatal(root: Path) -> None:
    """An advisory word given the power to fail CI is the flakiness #311 exists to keep out.

    The condition is `verdict in RECONCILIATION_VOCABULARY`, which is ALWAYS true, so the run
    always fails. It read `verdict == "CONSISTENT"` once, which was fatal only while the live tree
    read something else - and when this package's own record rolled forward to an unlanded package
    the live verdict became CONSISTENT, the mutated run exited 0, and the control quietly stopped
    demonstrating anything. A control whose mutation depends on the record it runs against is not
    a control.
    """
    edit(root, VALIDATOR, RETURN_ZERO,
         '    print(f"STATE_RECONCILIATION_REASON={reason}")\n'
         '    return 1 if verdict in RECONCILIATION_VOCABULARY else 0\n')


def the_reconciliation_raises(root: Path) -> None:
    """`reconcile_safely` must turn a validator defect into UNKNOWN, never into a lost verdict.

    Two things are measured at once here: the live reading goes to UNKNOWN and the suite notices,
    AND the validator still prints its verdict and exits 0 - so the tests that assert the run
    survives stay green while the tests that assert the READING go red.
    """
    edit(root, VALIDATOR, SIGNATURE, SIGNATURE + '\n    raise RuntimeError("wp112 control")')


def a_recorded_state_that_contradicts_the_verdict(root: Path) -> None:
    """THE DECLARED HOLE, and this control asserts the suite stays GREEN.

    The reconciliation reads two fields - the package id and the baseline commit - and says nothing
    about the rest of the record. A record whose package has LANDED while its own `state` still
    reads IN_PROGRESS is exactly the contradiction step 8 is asked about, and this guard does not
    see it. Limit 5 of the test module is written from this control. Reconciling the record
    itself is a records edit and not this guard's business; the point of the control is that
    the gap is measured rather than asserted.
    """
    edit(root, STATE, RECORDED_STATE, '"state": "IN_PROGRESS",')


DIVERGED_DOC_TAIL = "WHY the two parted, so this entry does not say."


def a_cause_claimed_in_the_diverged_docstring(root: Path) -> None:
    """THE SECOND DECLARED HOLE, and this control asserts the suite stays GREEN.

    The docstring guard forbids the ABSENCE claims - the ones DIVERGED's own precondition makes
    false - and requires the presence claim. It does NOT forbid claims about the CAUSE, which the
    reason guard does forbid. That asymmetry is deliberate and limit 7 of the test module states
    it: a docstring paragraph may legitimately name causes in order to say they cannot be
    distinguished, and the code comment beside this very branch does exactly that, while the
    printed reason is one terse assertion in which naming a cause IS asserting it.

    The price is this hole: a docstring that asserts a cause outright passes. Measured, not
    assumed - if this control ever goes red the asymmetry has been closed and limit 7 must be
    re-derived rather than deleted.
    """
    edit(root, VALIDATOR, DIVERGED_DOC_TAIL,
         "WHY the two parted; a force-push moved the main line away.")


SUITE_CONTROLS = [
    # Named against a FIXTURE test, not the live reading. The live reading only takes the
    # LAG_EXPECTED branch while the record happens to lag, and this package's own record rolling
    # forward moved it to CONSISTENT - at which point this control stopped tripping the test it
    # named, while the defect it injects was as real as ever.
    ("a landing reported as CONSISTENT", a_landing_reported_as_consistent,
     "test_lag_expected_when_the_recorded_package_has_landed"),
    ("any movement counted as a landing", any_movement_counted_as_a_landing,
     "test_consistent_when_a_sibling_package_landed_first"),
    ("the package id matched anywhere in the subject",
     the_package_id_matched_anywhere_in_the_subject,
     "test_consistent_when_a_commit_only_mentions_the_recorded_package"),
    ("the shallow guard removed", the_shallow_guard_removed,
     "test_unknown_on_a_shallow_clone_and_the_reason_says_shallow"),
    ("the enclosing-repository guard removed", the_enclosing_repository_guard_removed,
     "test_unknown_when_the_tree_merely_sits_inside_another_repository"),
    ("a foreign baseline reported as CONSISTENT", a_foreign_baseline_reported_as_consistent,
     "test_diverged_when_the_baseline_is_not_an_ancestor_of_the_main_line"),
    ("HEAD added as a fallback main ref", head_added_as_a_fallback_main_ref,
     "test_the_main_line_is_read_from_a_main_ref_and_never_from_head"),
    ("the reconciliation computed and not printed", the_reconciliation_not_printed,
     "test_the_reconciliation_is_printed_beside_the_resume_decision"),
    ("the reconciliation printed away from RESUME_DECISION",
     the_reconciliation_printed_away_from_the_resume_decision,
     "test_the_reconciliation_is_printed_beside_the_resume_decision"),
    ("the advisory verdict made fatal", the_advisory_made_fatal,
     "test_the_reconciliation_is_printed_beside_the_resume_decision"),
    ("the reconciliation raises", the_reconciliation_raises,
     "test_the_live_reading_agrees_with_the_history_measured_here"),
    # HOLE, not a defect: expected GREEN. See a_recorded_state_that_contradicts_the_verdict.
    ("DECLARED HOLE: a recorded state that contradicts the verdict",
     a_recorded_state_that_contradicts_the_verdict, None),
    # HOLE, not a defect: expected GREEN. See a_cause_claimed_in_the_diverged_docstring.
    ("DECLARED HOLE: a cause asserted in the DIVERGED docstring entry",
     a_cause_claimed_in_the_diverged_docstring, None),
]

# --- the mutations the ENVIRONMENT controls use -----------------------------------------------
#
# Each removes the check that makes one expected-green environment green, so that the green is
# known to come from the check. The list they belong to is beside its builders, further down.

TEST_MODULE = "tests/test_resume_reconciliation.py"
PROBE_GUARD = (
    '        if os.path.normcase(os.path.realpath(top.stdout.strip())) != \\\n'
    '                os.path.normcase(os.path.realpath(REPO)):\n'
    '            return False, "inside another repository rather than at its root"\n'
)


def the_probe_guard_removed(root: Path) -> None:
    """`full_history_is_present` stops noticing that it is not at the repository root.

    Without it the probe answers "judgeable" for a tree inside another checkout of this repository
    - toplevel resolves, not shallow, a main ref resolves, the baseline is in the enclosing
    repository's object database - and then demands LAG_EXPECTED while the code correctly answers
    UNKNOWN.
    """
    edit(root, TEST_MODULE, PROBE_GUARD, "")


RANGE_CORROBORATION = (
    '        landings = [line for line in subjects if line.startswith(f"[{work_package}]")]\n'
)


def the_corroboration_required_to_be_the_tip(root: Path) -> None:
    """Put back the rule that made merging this package break this package's own test.

    LAG_EXPECTED claims the recorded package landed SOMEWHERE since the baseline. The version this
    restores required the main line's TIP to be that package's merge, which is the same thing only
    until the next package merges. Paired with the control above so that the green there is known
    to come from the range corroboration and not from the fixture being too weak to tell.
    """
    edit(root, TEST_MODULE, RANGE_CORROBORATION,
         '        landings = ([subjects[0]] if subjects\n'
         '                    and subjects[0].startswith(f"[{work_package}]") else [])\n')


SCRIPT_CONTROLS = [
    ("THE SHALLOW-CLONE DEMONSTRATION: `git clone --depth 1`, unmutated", None, "UNKNOWN"),
    ("the same shallow clone with the shallow guard weakened to CONSISTENT",
     lambda root: edit(root, VALIDATOR, SHALLOW_GUARD,
                       SHALLOW_GUARD.replace('return "UNKNOWN", (', 'return "CONSISTENT", (')),
     "CONSISTENT"),
]

def nested_inside_a_clone(source: Path, into: Path, name: str) -> Path:
    """A working tree of `source` sitting in a SUBDIRECTORY of a clone of `source`.

    Not a repository itself, but inside one that holds this repository's objects and its
    `origin/main` - which is exactly what makes the case interesting: every fact a naive probe
    reads comes back present, and every one of them is about the wrong root.
    """
    enclosing = clone(source, into, name)
    nested = enclosing / "nested"
    shutil.copytree(enclosing, nested,
                    ignore=shutil.ignore_patterns(".git", "_site", "node_modules", "__pycache__"))
    top = subprocess.run(["git", "-C", str(nested), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True, timeout=60)
    if top.returncode != 0 or Path(top.stdout.strip()).name == "nested":
        raise AssertionError(f"the nested tree is not inside the clone: {top.stdout}{top.stderr}")
    return nested


def check_source_main_line(source: Path) -> str:
    """Refuse to run when the source's local `main` carries commits its `origin/main` does not.

    A clone's `origin/main` IS the source's `refs/heads/main`, so every control below reads the
    source's LOCAL main line whatever the source's own `origin/main` says.

    ONE DIRECTION ONLY, and the other direction is the reason this sentence is narrow. Both of
    these were measured, on scratch clones built for the purpose:

      local `main` AHEAD of `origin/main`   -> REFUSED. This is the incident that produced the
                                               check: a stray command committed onto local `main`,
                                               the worktree suite stayed green because it reads
                                               `origin/main`, and every clone went red on the
                                               live-tree test's corroboration - which reads the
                                               main-line TIP and found a commit landing no Work
                                               Package. Diagnosing that cost far more than this.
      local `main` BEHIND `origin/main`     -> ALLOWED. Built as a scratch source and run: the
                                               unmutated-clone control came back exit 0 with no
                                               failures. That is the ordinary state of a checkout
                                               that has fetched and not pulled, and refusing it
                                               would be a false failure of exactly the kind the
                                               check exists to prevent. The first version of this
                                               check compared for inequality in BOTH directions
                                               and did refuse it; review measured that, and this
                                               is the repair.

    WHAT IT DOES NOT PROMISE. It is not a guarantee that the run will be green: it reads two refs
    and says nothing about the record the controls are built against. This paragraph used to say
    more - that a local `main` far enough behind, before the merge the record's package landed in,
    satisfies this check and STILL FAILS the live-tree corroboration - and #360 is the measurement
    that retired that sentence. Such a source does fail one control, and the cause is not the
    source: it was the fixture builder below synthesising its commits on THIS ref rather than on
    the recorded baseline. Measured at WP-118 on a source whose local `main` sat one commit behind
    the recorded baseline, before and after that repair with everything else held identical: the
    one control moved from BAD to behaving and no other line of this runner's output changed. NO
    COUNT OF THIS RUNNER'S OWN CONTROLS IS RESTATED HERE, because a count written into the file it
    counts goes stale the day someone adds a control to it; `scripts/wp118_controls.py` is the
    standing evidence and runs the comparison as a grid. What a behind `main` costs the ordinary
    controls is nothing, because #353 gave a main ref behind the record its own UNKNOWN verdict
    and the live-tree test asserts it.

    The check stays this narrow all the same. Pinning which commit the record's package landed in
    is the tests' business and not this runner's, and a fixture that has to be told is a fixture
    that can be told wrong.
    """
    def ref(name: str) -> str:
        done = subprocess.run(["git", "-C", str(source), "rev-parse", "--verify", "--quiet",
                               f"{name}^{{commit}}"], capture_output=True, text=True, timeout=60)
        return done.stdout.strip() if done.returncode == 0 else ""

    local, published = ref("refs/heads/main"), ref("refs/remotes/origin/main")
    if not local or not published or local == published:
        return local or published
    behind = subprocess.run(["git", "-C", str(source), "merge-base", "--is-ancestor",
                             local, published], capture_output=True, text=True, timeout=60)
    if behind.returncode == 0:
        return local
    subject = subprocess.run(["git", "-C", str(source), "log", "-1", "--format=%s", local],
                             capture_output=True, text=True, timeout=60).stdout.strip()
    raise SystemExit(
        f"REFUSING TO RUN. {source}: refs/heads/main is {local[:12]} {subject!r}, which carries "
        f"commits refs/remotes/origin/main ({published[:12]}) does not. Every clone below would "
        f"take its origin/main from that local branch, so the live-tree control would measure the "
        f"drift rather than this package's code. Reconcile the source's main first.")


def clone_with_a_later_package(source: Path, into: Path, name: str) -> Path:
    """A clone whose `origin/main` has ONE MORE Work Package on it than the record knows.

    This is the merge that is coming: when this package lands, main's tip is its merge and no
    longer the recorded package's. Both commits are made with `commit-tree` and NOTHING IS CHECKED
    OUT, so the clone's working tree is still the tree under test - the module and the record this
    run is about. Checking either commit out would replace it with the baseline's tree, which is
    the PREVIOUS package's, and the run would measure that instead.

    THE CHAIN IS SYNTHESISED ON THE RECORDED BASELINE, and that is #360's repair. It used to be
    synthesised on the clone's `origin/main`, which IS the source checkout's `refs/heads/main` -
    so the fixture varied with how recently the source had been pulled. Measured on a source
    whose local `main` sat one commit behind the recorded baseline: the baseline was not an
    ancestor of the two new commits, the reading went DIVERGED rather than LAG_EXPECTED, the
    mutation this builder is paired with was therefore never reached, and the control reported BAD
    for a reason that had nothing to do with the code it measures. The baseline is in the record,
    it is the thing the reconciliation is measured against, and it does not move when someone
    pulls. `scripts/wp118_controls.py` holds the controls.

    WHAT THE THREE ASSERTIONS ARE WORTH, AND #360 CHANGED NONE OF IT. Only the first can fail for
    a reason outside this function: a source whose record names a baseline its object database
    does not hold - a shallow source, or a baseline recorded on a branch this repository never
    received - cannot have a fixture built on it at all, and must say so rather than surface as a
    raw `git commit-tree` error. The other two are CONSTRUCTION CHECKS, and have been since the
    two-commit repair above rather than since #360: both commits are synthesised here in a fixed
    order, so the tip's subject is the later package's and the recorded package's landing is in
    the range BY CONSTRUCTION. The second of those was MEASURED on the pre-repair builder against
    a PARTED history, which is the one case that could have falsified it, and it held anyway -
    `baseline..origin/main` is reachability and not descent, so a freshly synthesised commit is in
    that range whether or not the two lines contain one another. They are kept because the order
    of the two subjects, or a start that is not the baseline, would both make this fixture stop
    reproducing the case - but neither reports anything about the source, and neither did before.
    """
    root = clone(source, into, name)
    record = json.loads((root / STATE).read_text(encoding="utf-8"))
    work_package = record["active_work_package"]["id"]
    baseline = record["source"]["baseline_commit"]

    held = subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"{baseline}^{{commit}}"],
                          capture_output=True, text=True, timeout=60)
    if held.returncode != 0:
        raise AssertionError(
            f"the recorded baseline {baseline[:12]} is not in this clone, so no fixture can be "
            f"built on it: the source's history does not reach the commit its own record names")

    # BOTH commits are synthesised, and that is the earlier repair. This first built only the
    # later package and relied on the recorded one having already landed - true while the record
    # named WP-111, and false the moment the record rolled forward to WP-112, at which point the
    # builder's own guard fired and the control could not run at all. A fixture for "a later
    # package lands on top of the recorded one" must not depend on whether the recorded one has
    # landed yet.
    tip = baseline
    for subject in (f"[{work_package}] the recorded package lands (#351) (#998)",
                    "[BIZTRUST-GUIDE-WP-999] a later package lands on the main line (#351) (#999)"):
        tip = git_out(root, "-c", "user.name=WP-112 control",
                      "-c", "user.email=wp112@invalid.example",
                      "commit-tree", f"{tip}^{{tree}}", "-p", tip, "-m", subject)
    git_out(root, "update-ref", "refs/remotes/origin/main", tip)

    now = git_out(root, "log", "-1", "--format=%s", "refs/remotes/origin/main")
    if now.startswith(f"[{work_package}]"):
        raise AssertionError(f"the simulated tip still lands the recorded package: {now!r}")
    landings = [line for line in git_out(root, "log", "--format=%s",
                                         f"{baseline}..refs/remotes/origin/main").splitlines()
                if line.startswith(f"[{work_package}]")]
    if not landings:
        raise AssertionError(
            f"{work_package} is not in {baseline[:12]}..origin/main, so this fixture does not "
            f"reproduce a LAG_EXPECTED tree at all")
    return root


ENVIRONMENT_CONTROLS = [
    ("THE ENCLOSING-REPOSITORY DEGRADATION: the tree inside another checkout, unmutated",
     nested_inside_a_clone, None, None),
    ("the same tree with the test probe's enclosing-repository check removed",
     nested_inside_a_clone, the_probe_guard_removed,
     "test_the_live_reading_agrees_with_the_history_measured_here"),
    ("THE MERGE THAT IS COMING: a later package lands on top of the recorded one, unmutated",
     clone_with_a_later_package, None, None),
    ("the same later merge with the corroboration required to be the TIP",
     clone_with_a_later_package, the_corroboration_required_to_be_the_tip,
     "test_the_live_reading_agrees_with_the_history_measured_here"),
]


def suite(root: Path) -> tuple[int, set[str]]:
    """The subject module, run inside `root` as this runner has always run it."""
    return run_suite(root, "test_resume_reconciliation.py")


def run_validator(root: Path) -> tuple[int, str]:
    """The validator inside `root`, reduced to its ONE reconciliation verdict.

    STDOUT ONLY, and `VERDICT` is anchored with `re.M`: searching stderr as well would let a
    traceback's echo of the line count as a verdict. wp115's runner joins the two streams because
    it is looking for something else; see `scripts/control_harness.py`'s table.
    """
    code, out, _ = run_script(root, VALIDATOR, timeout=600)
    found = VERDICT.findall(out)
    return code, found[0] if len(found) == 1 else f"<{len(found)} verdict lines>"


def main() -> int:
    source, holder = arguments(__file__)
    check_source_main_line(source)

    code, failures = suite(clone(source, holder, "control_00_unmutated"))
    bad = report_unmutated(code, failures, "clone")
    bad += suite_controls(SUITE_CONTROLS, lambda name: clone(source, holder, name), suite,
                          hole=HOLE_DECLARED)

    for index, (name, build, mutate, expected) in enumerate(ENVIRONMENT_CONTROLS, start=1):
        root = build(source, holder, f"environment_{index:02d}")
        if mutate is not None:
            mutate(root)
        code, failures = suite(root)
        if expected is None:
            ok = code == 0 and not failures
            bad += 0 if ok else 1
            print(f"[{'PASS' if ok else 'BAD '}] {name}")
            # "EXPECTED GREEN", not "DEGRADATION": one of these environments is degraded (a tree
            # unpacked inside another checkout) and the other is simply the future (a later
            # package on the main line). Calling both a degradation would misdescribe the case
            # this pair was added for.
            print(f"       EXPECTED GREEN: the suite must stay green here; exit {code}; "
                  f"failed: {sorted(failures) or 'nothing'}")
            continue
        ok = code != 0 and expected in failures
        isolated = failures == {expected}
        bad += 0 if ok else 1
        print(f"[{'PASS' if ok else 'BAD '}] {name}")
        print(f"       expected {expected} to fail; exit {code}; "
              f"failed: {sorted(failures) or 'NOTHING'}"
              f"{'' if isolated else '  <- NOT ISOLATED' if ok else ''}")

    for index, (name, mutate, expected) in enumerate(SCRIPT_CONTROLS, start=1):
        root = clone(source, holder, f"shallow_{index:02d}", depth=1)
        if mutate is not None:
            mutate(root)
        code, verdict = run_validator(root)
        ok = code == 0 and verdict == expected
        bad += 0 if ok else 1
        print(f"[{'PASS' if ok else 'BAD '}] {name}")
        print(f"       shallow clone: expected STATE_RECONCILIATION={expected} and exit 0; "
              f"got {verdict} and exit {code}")

    return summarise(len(SUITE_CONTROLS) + len(ENVIRONMENT_CONTROLS) + len(SCRIPT_CONTROLS), bad)


if __name__ == "__main__":
    raise SystemExit(main())
