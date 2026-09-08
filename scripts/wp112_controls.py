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

TWO KINDS OF CONTROL.

  SUITE controls mutate `scripts/validate_continuity.py` in a full clone, run

      python -m unittest discover -s tests -p test_resume_reconciliation.py -v

  from that clone's root, and assert the NAMED test fails.

  SCRIPT controls run `python scripts/validate_continuity.py` in a SHALLOW clone and assert the
  printed verdict and exit code. The brief for this package required the shallow case to be
  demonstrated rather than asserted, and a test module cannot demonstrate it end to end: the
  degradation is a property of the script's exit code, not of a return value. The first script
  control is the demonstration - UNKNOWN, exit 0, on a genuinely shallow clone. The second exists
  because the first is worthless alone: it weakens the shallow guard and shows the same clone then
  reports CONSISTENT, so the UNKNOWN in the first is produced by the guard rather than by accident.

ONE SUITE CONTROL EXPECTS GREEN. It is a DECLARED HOLE - a real thing this guard does not catch -
and it is here so that limit 5 of `tests/test_resume_reconciliation.py` is demonstrated rather than
claimed. If it starts failing, the hole has closed and the limit must be re-derived, not deleted.

THE ROT RISK, stated plainly because this file is committed. A control script that nothing runs
looks like evidence and is not. It is DELIBERATELY NOT WIRED INTO CI: a dozen clones and suite runs
is far too slow for every push, and `scripts/validate_continuity.py` is the instrument every other
gate in this repository is read through - a workflow step that flaked here would be removed rather
than fixed. Run this before changing the reconciliation, and before believing any sentence the test
module's docstring states about what it catches.

It lives in `scripts/` and not `tests/` on purpose: `unittest discover -s tests` must not collect
it, and it clones repositories, which is not a thing `tests/` should do on every push.

Usage:  python scripts/wp112_controls.py [<repository>] [<scratch>]
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

PYTHON = sys.executable

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
    '    verdict, reason = reconcile_safely(ROOT, current)\n'
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
    """Replace `old` with `new` exactly once, and refuse to be a no-op."""
    path = root / rel
    text = path.read_text(encoding="utf-8")
    found = text.count(old)
    if found != 1:
        raise AssertionError(f"{rel}: expected exactly one occurrence of {old[:70]!r}, found {found}")
    path.write_text(text.replace(old, new), encoding="utf-8")


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
    edit(root, VALIDATOR, PRINT_BLOCK, "    reconcile_safely(ROOT, current)\n")


def the_reconciliation_printed_away_from_the_resume_decision(root: Path) -> None:
    """Printed, but above the verdict line rather than beside the two lines step 7 already reads."""
    edit(root, VALIDATOR, PRINT_BLOCK, "")
    edit(root, VALIDATOR, PASS_LINE,
         '    _verdict, _reason = reconcile_safely(ROOT, current)\n'
         '    print(f"STATE_RECONCILIATION={_verdict}")\n'
         '    print(f"STATE_RECONCILIATION_REASON={_reason}")\n' + PASS_LINE)


def the_advisory_made_fatal(root: Path) -> None:
    """An advisory word given the power to fail CI is the flakiness #311 exists to keep out."""
    edit(root, VALIDATOR, RETURN_ZERO,
         '    print(f"STATE_RECONCILIATION_REASON={reason}")\n'
         '    return 0 if verdict == "CONSISTENT" else 1\n')


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
    see it. Limit 5 of the test module is written from this control. The records half waits on
    #316; the point of the control is that the gap is measured rather than asserted.
    """
    edit(root, STATE, RECORDED_STATE, '"state": "IN_PROGRESS",')


SUITE_CONTROLS = [
    ("a landing reported as CONSISTENT", a_landing_reported_as_consistent,
     "test_the_current_tree_reports_lag_expected"),
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
     "test_the_current_tree_reports_lag_expected"),
    # HOLE, not a defect: expected GREEN. See a_recorded_state_that_contradicts_the_verdict.
    ("DECLARED HOLE: a recorded state that contradicts the verdict",
     a_recorded_state_that_contradicts_the_verdict, None),
]

SCRIPT_CONTROLS = [
    ("THE SHALLOW-CLONE DEMONSTRATION: `git clone --depth 1`, unmutated", None, "UNKNOWN"),
    ("the same shallow clone with the shallow guard weakened to CONSISTENT",
     lambda root: edit(root, VALIDATOR, SHALLOW_GUARD,
                       SHALLOW_GUARD.replace('return "UNKNOWN", (', 'return "CONSISTENT", (')),
     "CONSISTENT"),
]

FAILED = re.compile(r"^(?:FAIL|ERROR): (\w+) ", re.M)
VERDICT = re.compile(r"^STATE_RECONCILIATION=(\w+)$", re.M)


def clone(source: Path, into: Path, name: str, depth: int = 0) -> Path:
    root = into / name
    command = ["git", "clone", "--quiet"]
    if depth:
        # `--depth` is IGNORED on a plain local path; only the file:// transport honours it, and a
        # control that silently produced a full clone would demonstrate the opposite of its name.
        command += ["--depth", str(depth), source.as_uri()]
    else:
        command += [str(source)]
    done = subprocess.run(command + [str(root)], capture_output=True, text=True, timeout=600)
    if done.returncode != 0:
        raise AssertionError(f"clone of {source} failed: {done.stdout}{done.stderr}")
    if depth:
        shallow = subprocess.run(["git", "-C", str(root), "rev-parse", "--is-shallow-repository"],
                                 capture_output=True, text=True, timeout=60)
        if shallow.stdout.strip() != "true":
            raise AssertionError(f"clone --depth {depth} did not produce a shallow repository")
    return root


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


def main() -> int:
    source = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    holder = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(tempfile.mkdtemp())
    holder.mkdir(parents=True, exist_ok=True)
    bad = 0

    code, failures = run_suite(clone(source, holder, "control_00_unmutated"))
    print(f"[{'PASS' if code == 0 else 'BAD '}] unmutated clone: exit {code}, "
          f"failures {sorted(failures) or 'none'}")
    if code != 0:
        print("       the unmutated clone is already red; every control below proves nothing")
        bad += 1

    for index, (name, mutate, expected) in enumerate(SUITE_CONTROLS, start=1):
        root = clone(source, holder, f"control_{index:02d}")
        mutate(root)
        code, failures = run_suite(root)
        if expected is None:
            # A DECLARED HOLE. The mutation is a real contradiction and the suite is expected to
            # stay green, because nothing here reads the field it changes. A control that
            # demonstrates a limit cannot drift away from the code without this script noticing.
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

    total = len(SUITE_CONTROLS) + len(SCRIPT_CONTROLS)
    print(f"\n{total} controls, {bad} not behaving as declared")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
