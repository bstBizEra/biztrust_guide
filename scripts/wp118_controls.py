#!/usr/bin/env python3
"""Negative controls for BIZTRUST-GUIDE-WP-118's fixture repair (#360).

THE SUBJECT IS A FIXTURE BUILDER, not a guard. `clone_with_a_later_package` in
`scripts/wp112_controls.py` builds the clone that WP-112's last pair of environment controls runs
against: a main line carrying ONE MORE Work Package than the record knows. It used to synthesise
that line on the clone's `origin/main`, which IS the source checkout's `refs/heads/main` - so the
fixture varied with how recently the source had been pulled, and against a fetched-but-not-pulled
source the pair's second half reported BAD for a reason that had nothing to do with the code it
measures.

So these controls vary THE ONE THING THE FIXTURE MUST NOT DEPEND ON. Each builds a source checkout
of the tree under test whose local `main` sits somewhere different, runs the repaired builder
against it, and then runs the pair WP-112 declares:

    the fixture unmutated                     -> the suite must stay GREEN
    the corroboration required to be the TIP  -> test_the_live_reading_agrees_with_the_history_
                                                 measured_here must FAIL

THREE SOURCES, every one of them a state `check_source_main_line` accepts - asserted by calling it
on each, so that no control here measures a source the real runner would refuse to run against:

  BEHIND       local `main` one commit before the recorded baseline, `origin/main` at it. The
               ordinary state of a checkout that has fetched and not pulled, and the state #360
               was measured in.
  AT BASELINE  both refs at the recorded baseline. A checkout that has pulled.
  AHEAD        both refs at a commit synthesised ON TOP of the baseline - the world after some
               other package merges. The fixture must be the same tree in all three.

TWO BUILDERS, SO SIX CELLS AND TWELVE CONTROLS: three sources by the repaired builder and the
builder AS IT STOOD BEFORE THE REPAIR, each cell running the pair above. A copy of the repository
has the one repaired line put back to what it was and the pre-repair builder is loaded from that
copy. The mutation asserts the repaired line is present before replacing it, so a revert of #360,
or a rewording of it, fails here rather than passing quietly.

FIVE OF THE SIX CELLS BEHAVE THE SAME WAY, AND RUNNING THE WHOLE GRID IS HOW THAT IS MEASURED
RATHER THAN CLAIMED. Two of the three PRE-REPAIR cells behave exactly as the repaired ones do: on
a source whose `main` is AT the recorded baseline the old start point IS the baseline, and on one
AHEAD of it the baseline is still an ancestor of the old start point, so the fixture reproduces
LAG_EXPECTED either way. The third - PRE-REPAIR against the BEHIND source - is the defect: both
halves stay GREEN, and the mutated half staying green is the whole of it, because green there
means the mutation was never reached. So the BEHIND source and the pre-repair builder together are
what tell the repaired builder from the broken one.

WHICH MAKES FOUR OF THE SIX REPAIRED CONTROLS INVARIANCE INSURANCE RATHER THAN EVIDENCE, and that
is worth saying because six controls look like six measurements. After the repair the builder
reads NO REF, so the three REPAIRED cells build ONE IDENTICAL HISTORY three times: `git log
--format='%T|%s'` over `baseline..origin/main` in all three prints the same tree and the same two
subjects. The AT BASELINE and AHEAD pairs therefore assert a property rather than measure the
repair - a fixture that no longer varies with the source does not vary with the source - at the
price of four clones and four suite runs. They are kept because that property is exactly what #360
bought and is worth asserting once the builder stops reading refs.

THE PRE-REPAIR ROW IS WHERE THE HISTORIES ACTUALLY DIFFER, so all six of its controls carry
information: AT BASELINE matches the repaired history exactly, AHEAD carries a THIRD commit in the
range - the source's own later package, which the old start point picked up - and still reads
LAG_EXPECTED, and BEHIND is built on a parted line and reads DIVERGED.

WHAT COMES FROM THE COPY IS ONE FUNCTION. `sys.path[0]` is this script's own directory, so the
copy's own `from control_harness import ...` binds THIS tree's harness; the copy supplies the
builder and nothing else. The copy is never cloned from and carries no `.git`.

THE BUILDER AND THE MUTATION ARE IMPORTED FROM `scripts/wp112_controls.py`, not copied into this
file. A control on a fixture builder that measured its own copy of that builder would measure
nothing. The one deliberate copy is the reverted line above, and it is written as a mutation of
the real file for exactly that reason.

NOT WIRED INTO CI, deliberately, as wp111 to wp117's runners are not: sixteen clones of this
repository - one unmutated, three source checkouts and twelve fixtures - a full copy of it for the
pre-repair builder, and thirteen runs of the module suite on top. Minutes of work on every push. A
control script that nothing runs looks like evidence and is not - run this before touching
`clone_with_a_later_package`, and before believing anything WP-112's runner reports about a source
that is not the one it was last run against.

Built on `scripts/control_harness.py` (#368) rather than copied from a sibling, as
`scripts/wp117_controls.py` is.

Stdlib only, no network beyond the git and unittest subprocesses it starts. Run it as:

    python scripts/wp118_controls.py [source] [holder]
"""
from __future__ import annotations

import importlib.util
import json
from collections.abc import Callable
from pathlib import Path

from control_harness import (HOLE_PLAIN, arguments, clone, edit, fresh, git_out, report_unmutated,
                             run_suite, suite_controls, summarise)
from wp112_controls import (STATE, check_source_main_line, clone_with_a_later_package,
                            the_corroboration_required_to_be_the_tip)

WP112 = "scripts/wp112_controls.py"
LIVE_TEST = "test_the_live_reading_agrees_with_the_history_measured_here"

# The branch each constructed source is left standing on, so that moving its `main` never moves
# the commit a clone of it checks out. Without it, a source whose HEAD happened to BE `main` would
# hand the fixture builder the record of whatever commit `main` was pointed at, and the three
# sources would differ in their records as well as in their refs - two variables, one measurement.
TREE_BRANCH = "wp118-tree-under-test"

LATER_IN_SOURCE = "[BIZTRUST-GUIDE-WP-997] a package lands in the SOURCE checkout (#360) (#997)"

# The one line #360 repaired, and what it said before. `edit` refuses to be a no-op, so the first
# of these must still be in the file for the control that restores the second to run at all.
REPAIRED = "    tip = baseline\n"
BEFORE_THE_REPAIR = '    tip = git_out(root, "rev-parse", "refs/remotes/origin/main")\n'


def unmutated(root: Path) -> None:
    """No mutation: the first half of each pair is the fixture with nothing done to it.

    `suite_controls` calls `mutate` unconditionally, so the no-op is written out rather than
    signalled with None the way wp112's own environment loop signals it.
    """


def suite(root: Path) -> tuple[int, set[str]]:
    """The module WP-112's controls run, run inside `root` exactly as that runner runs it."""
    return run_suite(root, "test_resume_reconciliation.py")


def source_checkout(source: Path, holder: Path, label: str) -> Path:
    """A clone of `source` to be used as a SOURCE for the fixture builder, standing on its own
    branch so that `main` is free to be pointed anywhere without moving the working tree."""
    root = clone(source, holder, f"source_{label}")
    git_out(root, "checkout", "--quiet", "-b", TREE_BRANCH)
    return root


def point_main(root: Path, *, local: str, published: str) -> Path:
    """Point the source's two main refs, and REFUSE a source the real runner would refuse.

    `check_source_main_line` is called here rather than trusted: a control that constructed a
    source WP-112's own runner would exit on would be measuring a state that cannot occur.
    """
    for ref, at in (("refs/heads/main", local), ("refs/remotes/origin/main", published)):
        git_out(root, "update-ref", ref, git_out(root, "rev-parse", f"{at}^{{commit}}"))
    check_source_main_line(root)
    return root


def the_builder_before_the_repair(source: Path, holder: Path) -> Callable[..., Path]:
    """`clone_with_a_later_package` with #360's repair taken back out, loaded from a copy.

    The copy is a whole tree because `edit` mutates one file inside a root and asserts the text it
    replaces was really there; what is loaded out of it is a single function. Nothing clones from
    this copy and it carries no `.git`.
    """
    copy = fresh(source, holder, "before_the_repair")
    edit(copy, WP112, REPAIRED, BEFORE_THE_REPAIR)
    spec = importlib.util.spec_from_file_location("wp112_controls_before_wp118", copy / WP112)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.clone_with_a_later_package


def pair(source_label: str, builder_label: str,
         *, defect_cell: bool) -> list[tuple[str, Callable[[Path], None], str | None]]:
    """The two controls WP-112 declares, named for one cell of the source-by-builder grid.

    `defect_cell` is the ONE cell #360 is about, and it inverts the second control's expectation:
    everywhere else the mutation must fail the test it targets, and there it must not, because the
    reading never reaches the line the mutation edits.
    """
    head = f"{source_label} SOURCE, {builder_label} BUILDER"
    tail = (" - GREEN, and THAT is the defect: the mutation is never reached"
            if defect_cell else "")
    return [
        (f"{head}: the later-merge fixture, unmutated", unmutated, None),
        (f"{head}: the same fixture with the corroboration required to be the TIP{tail}",
         the_corroboration_required_to_be_the_tip, None if defect_cell else LIVE_TEST),
    ]


def slug(*parts: str) -> str:
    """A directory-safe tag, so two cells never build a fixture at the same path."""
    return "_".join(part.lower().replace(" ", "_").replace("-", "_") for part in parts)


def main() -> int:
    source, holder = arguments(__file__)
    check_source_main_line(source)
    baseline = json.loads((source / STATE).read_text(encoding="utf-8"))["source"]["baseline_commit"]

    code, failures = suite(clone(source, holder, "control_00_unmutated"))
    bad = report_unmutated(code, failures, "clone")

    behind = point_main(source_checkout(source, holder, "behind"),
                        local=f"{baseline}~1", published=baseline)
    at_baseline = point_main(source_checkout(source, holder, "at_baseline"),
                             local=baseline, published=baseline)
    ahead = source_checkout(source, holder, "ahead")
    later = git_out(ahead, "-c", "user.name=WP-118 control",
                    "-c", "user.email=wp118@invalid.example",
                    "commit-tree", f"{baseline}^{{tree}}", "-p", baseline, "-m", LATER_IN_SOURCE)
    point_main(ahead, local=later, published=later)

    # THE WHOLE GRID, and not only the cell the defect lives in. Running the pre-repair builder
    # against all three sources is what turns "the AT BASELINE and AHEAD pairs cannot see this
    # defect" from a sentence into a measurement: those two sources behave IDENTICALLY under both
    # builders, so only the BEHIND one tells the repaired builder from the broken one, and a
    # reader who assumed all three sources were measuring the repair can see from the output that
    # they are not.
    total = 0
    for builder_label, build in (("REPAIRED", clone_with_a_later_package),
                                 ("PRE-REPAIR", the_builder_before_the_repair(source, holder))):
        for source_label, built_from in (("BEHIND", behind), ("AT BASELINE", at_baseline),
                                         ("AHEAD", ahead)):
            defect_cell = builder_label == "PRE-REPAIR" and source_label == "BEHIND"
            controls = pair(source_label, builder_label, defect_cell=defect_cell)
            total += len(controls)
            bad += suite_controls(
                controls,
                lambda name, root=built_from, builder=build,
                tag=slug(builder_label, source_label):
                    builder(root, holder, f"{tag}_{name}"),
                suite, hole=HOLE_PLAIN)

    return summarise(total, bad)


if __name__ == "__main__":
    raise SystemExit(main())
