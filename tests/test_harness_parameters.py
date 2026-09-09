#!/usr/bin/env python3
"""A harness parameter with no dissenting caller is a union in disguise.

`scripts/control_harness.py` (#368) holds the part of the six negative-control runners that
measurement showed is genuinely common. Every difference it did NOT flatten survives as a
parameter, and WP-117's whole case rests on one property:

    every parameter the harness gives a default has at least one runner passing something else.

That property was true when the harness was written and was verified by hand in review. Nothing
kept it true. The next edit can give a parameter a default that no caller ever dissents from, and
the parameter stops expressing a difference and starts hiding one - which is WP-110's failure
re-entering through the door WP-117 built. WP-110 replaced four private normalisers with one
shared, more lenient one; the suite passed, four re-run controls passed, and review then found
eight real divergences that were caught before the change and missed after it. The rule recorded
from it is exact: A QUESTION CAN HAVE TWO RIGHT ANSWERS, ONE PER CALLER - and a parameter with a
live caller on each side is how you say so. One with a caller on only one side says nothing.

THIS MODULE READS SOURCE, IT DOES NOT RUN ANYTHING. It parses `scripts/control_harness.py` and
every `scripts/wp*_controls.py` with `ast` and asks four questions of the text. It does not
import the harness and does not start a process, because the harness shells out by nature and the
suite is offline: exactly four modules under `tests/` call a subprocess, measured with

    grep -lnE "subprocess[.](run|Popen|check_output|check_call)" tests/*.py

and this module is not the fifth. Reading a file as text breaks neither property. WP-117's brief
said `tests/` gains nothing from the harness; the coordinator ruled that the sentence was aimed at
the import and the process, not at a reader, and this module is that reader.

FOUR CHECKS.

  A  EVERY NAME A RUNNER IMPORTS FROM THE HARNESS IS DEFINED THERE. The anchor. Without it, a
     harness function renamed out from under its importers would make check C look at a smaller
     parameter set and pass for the wrong reason, silently.

  B  EVERY DEFAULTED PARAMETER IS KEYWORD-ONLY. Not a style rule - a precondition of check C.
     Check C finds dissent by reading KEYWORD arguments at call sites. A defaulted parameter that
     can also be passed positionally could be dissented from in a way this reader cannot see, and
     the check would report a violation that is not there, or miss one that is.

  C  EVERY DEFAULTED PARAMETER HAS A DISSENTING CALLER. For each parameter of each imported
     harness function that carries a default, at least one call site in `scripts/wp*_controls.py`
     must pass that keyword with an argument whose source text differs from the default's source
     text. Import aliases are followed: `wp111_controls.py` does
     `from control_harness import edit as harness_edit`, and its `preview=60` counts.

  D  THIS MODULE STAYS A READER. Its own source carries no import of `control_harness` and no
     `subprocess` call, asserted against its own text rather than promised in this docstring.

THE PARAMETER LIST IS READ FROM THE HARNESS, NEVER LISTED HERE. A guard carrying its own copy of
the six parameters would go on passing after a seventh was added with no dissenter, which is the
defect class this repository keeps meeting - the same reason `tests/test_authority_citations.py`
reads its key set out of the record.

WHAT THIS DOES NOT DO. Every item is a real limit, not a caveat.

 1. DISSENT IS COMPARED AS SOURCE TEXT, NOT AS A VALUE. `ignore=IGNORE` differs from the default
    `COPY_IGNORE` because the two strings differ, and nothing here evaluates either. A caller
    passing a name that happens to hold the default value would be counted as dissenting and would
    be wrong; a caller passing the default's own name would correctly not count. Evaluating them
    means importing the harness, which check D forbids.
 2. IT COUNTS CALL SITES, NOT RUNS. A dissenting call inside a function nothing ever calls still
    satisfies check C. What is guarded is that the repository still SAYS two answers are needed,
    not that both are reached; whether a control runs is `scripts/wp117_controls.py`'s business and
    the other runners' own.
 3. ONE DISSENTER IS ENOUGH, AND THE FLOOR ON THE PARAMETER SET IS ONE. Check C is satisfied by a
    single dissenting call site per parameter, and `test_the_harness_exposes_defaulted_parameters`
    only refuses a harness with NO defaulted parameter at all. Neither is an equality, because the
    harness may legitimately gain or lose a parameter and an equality would make every future
    package edit this file. What is guarded is the shape, not the size.
 4. NOTHING HERE READS WHAT A PARAMETER MEANS. A parameter whose two callers pass two values that
    make no difference to behaviour passes every check. Whether a difference is real is the
    classification in the harness's own docstring, which is prose a human wrote and this module
    does not check.
 5. ONLY `scripts/wp*_controls.py` IS SEARCHED FOR CALL SITES. A dissenting caller written
    anywhere else - another script, a notebook, a future package's own file - does not count.
    That is deliberate: the harness exists for these runners, and a parameter kept alive only by
    something outside them is a parameter these runners no longer need.
 6. THE HARNESS'S OWN DEFAULTS ARE NOT JUDGED. Whether 70 rather than 60 is the right default for
    `edit`'s preview, or `""` rather than `None` for its newline, is not asked. The question is
    only whether some caller still needs the other answer.

NEGATIVE CONTROLS, run by `scripts/wp117_controls.py`, a committed script rather than a prose
claim. Each copies the repository, applies ONE mutation, runs this module from that copy's root
and asserts the NAMED test fails; the unmutated copy runs first and must be green.

ISOLATED - exactly one test fails:
  * wp111's `preview=60`, the only dissenter, changed to `preview=70`
                                                       -> test_every_defaulted_parameter_has_a_dissenting_caller
  * wp112's `depth=1`, the only dissenter, changed to `depth=0`
                                                       -> test_every_defaulted_parameter_has_a_dissenting_caller
  * a seventh defaulted parameter added to the harness that no caller passes
                                                       -> test_every_defaulted_parameter_has_a_dissenting_caller
  * `preview` moved in front of the `*` in the harness's own signature
                                                       -> test_every_defaulted_parameter_is_keyword_only
  * the harness's `git_out` renamed, leaving its two importers naming nothing
                                                       -> test_every_imported_name_is_defined_in_the_harness
  * an import of the harness added to this module, inside a function nothing calls
                                                       -> test_this_guard_neither_imports_the_harness_nor_shells_out

EXPECTED GREEN - the property is about the LAST dissenter, not about any dissenter:
  * wp116's `no_bytecode=True` dropped while wp115's and wp117's remain
                                                       -> nothing fails, by design

THE UNMUTATED RUN IS ITSELF THE PROOF THAT ALIASES ARE FOLLOWED. `preview` and `newline` have
exactly one and two dissenting call sites, and every one of them is written through
`wp111_controls.py`'s and `wp112_controls.py`'s `harness_edit` alias. A reader that did not resolve
`from control_harness import edit as harness_edit` would find no dissenter for either and this
module would already be red on a clean tree.

Stdlib only: no third-party import, no network, no subprocess.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "scripts" / "control_harness.py"
HARNESS_MODULE = "control_harness"
SUBPROCESS_CALLS = ("run", "Popen", "check_output", "check_call")


def runner_paths() -> list[Path]:
    """The runner scripts, in name order.

    The glob is `wp*_controls.py` and not `wp1??_controls.py`, which was what this read first:
    `wp1??` stops at wp199, so a wp200-series runner would have fallen out of every check below
    in silence. Measured at the time of the change, both patterns match the same seven files.
    """
    return sorted((ROOT / "scripts").glob("wp*_controls.py"))


def parsed(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def harness_functions() -> dict[str, ast.FunctionDef]:
    return {node.name: node for node in parsed(HARNESS).body
            if isinstance(node, ast.FunctionDef)}


def harness_bindings() -> set[str]:
    """Every name the harness defines at module level - functions and constants alike.

    Read from the file, never listed here: a guard carrying its own copy of the constant names
    would go on passing after one was renamed, which is the defect class this repository keeps
    meeting.
    """
    names = set()
    for node in parsed(HARNESS).body:
        if isinstance(node, ast.FunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(target.id for target in node.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def imported_names(tree: ast.Module) -> dict[str, str]:
    """`{local name: harness name}` for every `from control_harness import ...` in one runner."""
    names: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == HARNESS_MODULE:
            for alias in node.names:
                names[alias.asname or alias.name] = alias.name
    return names


def defaulted_parameters(function: ast.FunctionDef) -> list[tuple[str, str, bool]]:
    """`(parameter, the default's source text, is it keyword-only)` for each default it carries."""
    found = []
    positional = function.args.posonlyargs + function.args.args
    for argument, default in zip(positional[len(positional) - len(function.args.defaults):],
                                 function.args.defaults):
        found.append((argument.arg, ast.unparse(default), False))
    for argument, default in zip(function.args.kwonlyargs, function.args.kw_defaults):
        if default is not None:
            found.append((argument.arg, ast.unparse(default), True))
    return found


def keyword_arguments() -> list[tuple[str, str, str, str]]:
    """`(harness function, keyword, the argument's source text, runner)` at every runner call site.

    A call is attributed to the harness only when the name it calls was imported from the harness
    in that same file, so a runner's own `edit` or `run_validator` is never mistaken for one.
    """
    passed = []
    for path in runner_paths():
        tree = parsed(path)
        local = imported_names(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            target = local.get(node.func.id)
            if target is None:
                continue
            for keyword in node.keywords:
                if keyword.arg is not None:
                    passed.append((target, keyword.arg, ast.unparse(keyword.value), path.name))
    return passed


class HarnessParameters(unittest.TestCase):
    """Four questions asked of the source of the harness and of the runners that call it."""

    def setUp(self) -> None:
        self.functions = harness_functions()
        self.runners = runner_paths()
        self.imports = {path.name: imported_names(parsed(path)) for path in self.runners}

    def test_the_harness_exposes_defaulted_parameters(self) -> None:
        """The floor, so no check below can pass because its subject has gone.

        A floor and not an equality, per limit 3: the harness may gain or lose a parameter without
        this file being edited, but it may not lose all of them and leave the checks vacuous.
        """
        self.assertTrue(HARNESS.is_file(), f"{HARNESS} is missing")
        self.assertTrue(self.runners, "no scripts/wp*_controls.py runner was found")
        total = sum(len(defaulted_parameters(function))
                    for function in self.functions.values())
        self.assertGreater(total, 0, "the harness exposes no defaulted parameter at all, so "
                                     "test_every_defaulted_parameter_has_a_dissenting_caller "
                                     "would pass over an empty set")

    def test_every_imported_name_is_defined_in_the_harness(self) -> None:
        """The anchor: a renamed harness function must report itself rather than shrink the set."""
        defined = harness_bindings()
        missing = sorted({f"{runner} imports {name}"
                          for runner, names in self.imports.items()
                          for name in names.values() if name not in defined})
        self.assertEqual(missing, [], "these names are imported from scripts/control_harness.py "
                                      "and are not defined there")

    def test_every_defaulted_parameter_is_keyword_only(self) -> None:
        """Check C reads keyword arguments, so a defaulted parameter must not be passable another
        way. A positional default is not a style complaint here; it is a hole in the reader."""
        positional = sorted(f"{name}({parameter}=)"
                            for name, function in self.functions.items()
                            for parameter, _default, kwonly in defaulted_parameters(function)
                            if not kwonly)
        self.assertEqual(positional, [], "these harness parameters carry a default and can be "
                                         "passed positionally, which "
                                         "test_every_defaulted_parameter_has_a_dissenting_caller "
                                         "cannot see; put them after the `*`")

    def test_every_defaulted_parameter_has_a_dissenting_caller(self) -> None:
        """WP-117's whole property: a default nobody dissents from is a union in disguise."""
        passed = keyword_arguments()
        undissented = []
        for name, function in sorted(self.functions.items()):
            for parameter, default, _kwonly in defaulted_parameters(function):
                dissent = [runner for (target, keyword, value, runner) in passed
                           if target == name and keyword == parameter and value != default]
                if not dissent:
                    undissented.append(f"{name}({parameter}={default})")
        self.assertEqual(
            sorted(undissented), [],
            "no runner passes anything but the default for these harness parameters, so each of "
            "them expresses no difference between callers and could be deleted - or, worse, is "
            "the more lenient of two behaviours with the other one already gone. Either give the "
            "parameter a dissenting caller or remove it; do not leave a default standing in for "
            "a question that used to have two answers.")

    def test_this_guard_neither_imports_the_harness_nor_shells_out(self) -> None:
        """Asserted against this file's own source rather than promised in its docstring."""
        tree = parsed(Path(__file__).resolve())
        imports = [alias.name for node in ast.walk(tree)
                   if isinstance(node, ast.ImportFrom) and node.module == HARNESS_MODULE
                   for alias in node.names]
        imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
                    for alias in node.names if alias.name == HARNESS_MODULE]
        self.assertEqual(imports, [], "this module must READ scripts/control_harness.py, never "
                                      "import it: the harness shells out, and the suite is "
                                      "offline")
        shells = [ast.unparse(node.func) for node in ast.walk(tree)
                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                  and node.func.attr in SUBPROCESS_CALLS
                  and isinstance(node.func.value, ast.Name)
                  and node.func.value.id == "subprocess"]
        self.assertEqual(shells, [], "four modules under tests/ start a process by declared "
                                     "precedent and this must not become the fifth")


if __name__ == "__main__":
    unittest.main()
