#!/usr/bin/env python3
"""Negative controls for BIZTRUST-GUIDE-WP-117's harness-parameter guard (#368).

`scripts/wp116_controls.py` is the model and this file follows it: one mutation per fresh copy,
the unmutated copy first and green, every mutation asserting that what it replaces was really
there so a control cannot quietly become a no-op. It is also the first runner written on top of
`scripts/control_harness.py` rather than by copying its predecessor, which is the whole point of
that module - so this file is both a control on the guard and the first demonstration that the
harness can carry a runner it was not extracted from.

A COPY, NOT A CLONE, for the reason wp115's and wp116's runners give: the subject is source text -
one harness module, three runner modules and one test module - not git history, so
`shutil.copytree` is right and cheaper.

Each control copies the repository, applies ONE mutation, runs

    python -m unittest discover -s tests -p test_harness_parameters.py -v

from that copy's root, and asserts the NAMED test fails.

WHAT IS BEING GUARDED, and why a control on it is not optional. WP-117 extracted the part of the
six runners that measurement showed is common and left every real difference standing as a
PARAMETER WITH A LIVE CALLER ON EACH SIDE. That property was true when it was written and was
verified by hand in review; nothing kept it true. A parameter whose default nobody dissents from
has stopped expressing a difference between callers - it is the union of two behaviours with one
of them deleted, which is WP-110's failure exactly. `tests/test_harness_parameters.py` is the
guard; these are the controls that show it can fail, and fail for the right reason.

SEVEN CONTROLS:
  1. wp111's `preview=60` - the ONLY dissenting caller for `edit`'s preview width - changed to the
     default 70 -> test_every_defaulted_parameter_has_a_dissenting_caller FAILS. This is the
     control the guard exists for: the last dissenter gone, the parameter now saying nothing.
  2. wp112's `depth=1` - the ONLY dissenting caller for `clone`'s depth - changed to the default 0
     -> the same test FAILS. A second parameter, on a different function, so the check is not
     passing on one hardcoded case.
  3. EXPECTS GREEN: wp116's `no_bytecode=True` dropped while wp115's and this runner's remain ->
     the suite stays GREEN. Proves the guard is about the LAST dissenter rather than about any
     dissenter - a guard that reddened whenever a call site changed would be switched off inside a
     week, and a false failure is worse than a miss.
  4. A SEVENTH defaulted parameter added to the harness that no caller passes -> the same test
     FAILS. Proves the parameter set is READ FROM THE HARNESS rather than listed in the guard: a
     guard carrying its own copy of the six would go on passing after a seventh arrived.
  5. `preview` moved in front of the `*` in the harness's own signature ->
     test_every_defaulted_parameter_is_keyword_only FAILS. That check is a precondition of control
     1's check, not a style rule: the reader finds dissent by reading KEYWORD arguments, so a
     defaulted parameter that can also be passed positionally is a hole in the reader.
  6. The harness's `git_out` renamed, leaving its two importers naming nothing ->
     test_every_imported_name_is_defined_in_the_harness FAILS. The anchor: without it a renamed
     function would silently shrink the parameter set the other checks look at, and they would
     pass for the wrong reason.
  7. An import of the harness added to the guard module, inside a function nothing calls ->
     test_this_guard_neither_imports_the_harness_nor_shells_out FAILS. The suite is offline and
     the harness shells out; the guard reads it as text and must keep doing so.

Every one of the six failing controls trips exactly the test named for it and nothing else.

THE UNMUTATED RUN CARRIES A PROOF OF ITS OWN, and it is why no eighth control tests it: `preview`
and `newline` are dissented from only through `wp111_controls.py`'s and `wp112_controls.py`'s
`from control_harness import edit as harness_edit` alias. A guard that did not resolve that alias
would find no dissenter for either and would already be red on a clean tree, so control 0 - the
unmutated copy, green - is the measurement that alias resolution works.

NOT WIRED INTO CI, deliberately, as wp111 to wp116's runners are not: this is a control on a guard
rather than the guard itself, and its result is evidence about the tree at the commit someone last
ran it against. A control script nothing runs looks like evidence and is not.

Stdlib only, no network beyond the subprocess it runs. Run it as:

    python scripts/wp117_controls.py [source] [holder]
"""
from __future__ import annotations

from pathlib import Path

from control_harness import (HOLE_PLAIN, arguments, edit, fresh, report_unmutated, run_suite,
                             suite_controls, summarise)

HARNESS = "scripts/control_harness.py"
GUARD = "tests/test_harness_parameters.py"
WP111 = "scripts/wp111_controls.py"
WP112 = "scripts/wp112_controls.py"
WP116 = "scripts/wp116_controls.py"

# --- the exact text each mutation replaces --------------------------------------------------------

PREVIEW_DISSENT = "    harness_edit(root, rel, old, new, preview=60, newline=None)\n"
DEPTH_DISSENT = '        root = clone(source, holder, f"shallow_{index:02d}", depth=1)\n'
NO_BYTECODE_DISSENT = (
    '    return run_suite(root, "test_resume_protocol_command.py", no_bytecode=True)\n')

SUMMARISE_SIGNATURE = "def summarise(total: int, bad: int) -> int:\n"
EDIT_SIGNATURE = (
    "def edit(root: Path, rel: str, old: str, new: str, *,\n"
    '         preview: int = 70, newline: str | None = "") -> None:\n')
GIT_OUT_SIGNATURE = "def git_out(root: Path, *args: str) -> str:\n"

GUARD_TAIL = 'if __name__ == "__main__":\n    unittest.main()\n'


# --- the mutations -------------------------------------------------------------------------------


def the_last_dissenting_caller_for_preview_removed(root: Path) -> None:
    """wp111 is the only runner that passes `edit`'s preview width. Make it pass the default.

    The mutation is deliberately not a deletion of the keyword: an author defending a default is
    far more likely to write the default out explicitly than to remove the argument, and the guard
    must catch the shape the mistake actually takes.
    """
    edit(root, WP111, PREVIEW_DISSENT,
         "    harness_edit(root, rel, old, new, preview=70, newline=None)\n")


def the_last_dissenting_caller_for_depth_removed(root: Path) -> None:
    """wp112's shallow controls are the only caller that clones with `--depth`."""
    edit(root, WP112, DEPTH_DISSENT,
         '        root = clone(source, holder, f"shallow_{index:02d}", depth=0)\n')


def one_of_several_dissenting_callers_for_no_bytecode_removed(root: Path) -> None:
    """EXPECTS GREEN. wp115 and this runner still pass `no_bytecode=True` after wp116 stops.

    A guard that fired here would be measuring call sites rather than the property, and would be
    turned off the first time a runner legitimately changed one.
    """
    edit(root, WP116, NO_BYTECODE_DISSENT,
         '    return run_suite(root, "test_resume_protocol_command.py")\n')


def a_seventh_defaulted_parameter_no_caller_passes(root: Path) -> None:
    """Add a default to the harness that nothing dissents from, and change nothing else.

    `summarise` is chosen because its two callers-in-shape - every runner - call it positionally
    and would go on working, which is exactly how such a parameter arrives in practice: harmless,
    unused, and indistinguishable from the surviving half of a flattened divergence.
    """
    edit(root, HARNESS, SUMMARISE_SIGNATURE,
         'def summarise(total: int, bad: int, *, banner: str = "") -> int:\n')


def a_defaulted_parameter_moved_in_front_of_the_star(root: Path) -> None:
    """`preview` becomes positional-or-keyword. Every existing call still works."""
    edit(root, HARNESS, EDIT_SIGNATURE,
         "def edit(root: Path, rel: str, old: str, new: str, preview: int = 70, *,\n"
         '         newline: str | None = "") -> None:\n')


def a_harness_function_renamed_out_from_under_its_importers(root: Path) -> None:
    """wp112 and wp114 both import `git_out`; the harness stops defining it."""
    edit(root, HARNESS, GIT_OUT_SIGNATURE, "def git_output(root: Path, *args: str) -> str:\n")


def an_import_of_the_harness_added_to_the_guard(root: Path) -> None:
    """Inside a function nothing calls, so the module still imports and the suite still runs.

    That is the shape this has to be caught in. An import at the top of the file would raise
    ModuleNotFoundError out of the loader - loud, but for the wrong reason and reported against a
    name no control could assert on.
    """
    edit(root, GUARD, GUARD_TAIL,
         "def _unused() -> None:\n"
         "    import control_harness  # noqa: F401\n"
         "\n"
         "\n" + GUARD_TAIL)


# (name, mutation, the test that must fail; None means the suite must stay GREEN)
CONTROLS = [
    ("the last dissenting caller for edit's preview width removed",
     the_last_dissenting_caller_for_preview_removed,
     "test_every_defaulted_parameter_has_a_dissenting_caller"),
    ("the last dissenting caller for clone's depth removed",
     the_last_dissenting_caller_for_depth_removed,
     "test_every_defaulted_parameter_has_a_dissenting_caller"),
    ("EXPECTS GREEN: one of several dissenting callers for no_bytecode removed",
     one_of_several_dissenting_callers_for_no_bytecode_removed, None),
    ("a seventh defaulted parameter added to the harness that no caller passes",
     a_seventh_defaulted_parameter_no_caller_passes,
     "test_every_defaulted_parameter_has_a_dissenting_caller"),
    ("a defaulted parameter moved in front of the `*` in the harness signature",
     a_defaulted_parameter_moved_in_front_of_the_star,
     "test_every_defaulted_parameter_is_keyword_only"),
    ("a harness function renamed out from under its importers",
     a_harness_function_renamed_out_from_under_its_importers,
     "test_every_imported_name_is_defined_in_the_harness"),
    ("an import of the harness added to the guard module",
     an_import_of_the_harness_added_to_the_guard,
     "test_this_guard_neither_imports_the_harness_nor_shells_out"),
]


def suite(root: Path) -> tuple[int, set[str]]:
    """The subject module, run inside `root` under `-B` as wp115's and wp116's runners run theirs."""
    return run_suite(root, "test_harness_parameters.py", no_bytecode=True)


def main() -> int:
    source, holder = arguments(__file__)

    code, failures = suite(fresh(source, holder, "control_00_unmutated"))
    bad = report_unmutated(code, failures, "copy")
    bad += suite_controls(CONTROLS, lambda name: fresh(source, holder, name), suite,
                          hole=HOLE_PLAIN)
    return summarise(len(CONTROLS), bad)


if __name__ == "__main__":
    raise SystemExit(main())
