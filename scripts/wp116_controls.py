#!/usr/bin/env python3
"""Negative controls for BIZTRUST-GUIDE-WP-116's resume-protocol guard (#348).

`scripts/wp115_controls.py` is the model and this file follows it: one mutation per fresh copy,
the unmutated copy first and green, every mutation asserting that what it replaces was really
there so a control cannot quietly become a no-op.

A COPY, NOT A CLONE, for the same reason wp115's runner gives: the subject is one tracked
Markdown file and one test module, not git history, so `shutil.copytree` is right and cheaper.

Each control copies the repository, applies ONE mutation, runs

    python -m unittest discover -s tests -p test_resume_protocol_command.py -v

from that copy's root, and asserts the NAMED test fails. Two controls expect the suite to stay
GREEN and say why in their own docstrings - a guard that rejects legitimate content gets switched
off, and a false failure is worse than a miss. The runner fails if either goes red, exactly as
wp115's runner does for its own GREEN-expecting controls.

FIX ROUND 1 added control 3. Review measured that the pre-round-1 guard required the literal word
"Windows" and the literal bare token "python" on the same line as "python3", and a legitimate
rewrite of step 7 using `py -m unittest ...` and the word "PowerShell" instead - correct content,
worded differently - turned it red. Control 3 is that exact rewrite, committed so the guard's
current looser property (some OTHER interpreter token beside python3, not a fixed vocabulary) stays
measured rather than merely claimed.

FOUR CONTROLS:
  1. Step 7 reverted to a bare `python3 -m unittest discover -s tests`, the pre-fix text, with no
     other interpreter token anywhere on that line -> test_no_bare_python3_command FAILS. This is
     the control #348's own brief names by name: "a control that puts `python3 -m unittest` back
     into that section must turn it red."
  2. EXPECTS GREEN: a second, properly-paired POSIX/Windows sentence added elsewhere in section 3,
     naming `python3` and `python` together on its own line. Proves the guard checks the PAIRING,
     not the mere presence of the word `python3` anywhere in the section - a guard that flagged
     every python3 mention regardless of context would also flag the fix itself.
  3. EXPECTS GREEN, FIX ROUND 1's OWN CONTROL: step 7 rewritten with `py -m unittest ...` /
     `py scripts/validate_continuity.py` and the word "PowerShell" in place of `python` and
     "Windows". Proves the guard checks a PROPERTY - some other interpreter token beside python3 -
     rather than a fixed vocabulary a correct rewrite might reasonably not use.
  4. The section 3 heading renamed -> test_anchors_exist FAILS. Proves the anchor is asserted rather
     than assumed: a renamed heading must report itself, not raise out of the middle of a reader.

NOT WIRED INTO CI, deliberately, as wp111 to wp115's runners are not: this is a control on a guard
rather than the guard itself, and its result is evidence about the tree at the commit someone last
ran it against.

THE COPY, THE MUTATION HELPER, THE SUITE RUN AND THE REPORTING LOOP now come from
`scripts/control_harness.py` (#368), which classified every divergence across the six runners as
need or drift before moving anything. Adoption was gated on this runner's full output being
byte-identical before and after, not on the suite staying green.

Stdlib only, no network beyond the subprocess it runs. Run it as:

    python scripts/wp116_controls.py [source] [holder]
"""
from __future__ import annotations

from pathlib import Path

from control_harness import (HOLE_PLAIN, arguments, edit, fresh, report_unmutated, run_suite,
                             suite_controls, summarise)

MODULE = "tests/test_resume_protocol_command.py"
AGENTS = "AGENTS.md"

FIXED_STEP7 = (
    "7. Run the validator's own self-tests, then `scripts/validate_continuity.py`, with a "
    "Python 3 interpreter: `python3 -m unittest discover -s tests` then "
    "`python3 scripts/validate_continuity.py` on POSIX; `python -m unittest discover -s tests` "
    "then `python scripts/validate_continuity.py` on Windows, where `python3` may resolve to a "
    "Microsoft Store alias that reports Python is absent. `.github/workflows/pages.yml` runs on "
    "`ubuntu-latest`, where `python3` is the real interpreter and is not to be \"fixed\" to match "
    "this line."
)

# FIX ROUND 1's OWN CONTROL, expecting GREEN. The pre-round-1 guard required the literal word
# "Windows" and the literal bare token "python"; this rewrite is correct dual-invocation content
# that uses neither, and must not be rejected.
PY_AND_POWERSHELL_STEP7 = (
    "7. Run the validator's own self-tests, then `scripts/validate_continuity.py`, with a "
    "Python 3 interpreter: `python3 -m unittest discover -s tests` then "
    "`python3 scripts/validate_continuity.py` in a POSIX shell; `py -m unittest discover -s "
    "tests` then `py scripts/validate_continuity.py` in PowerShell, where `python3` may resolve "
    "to a Microsoft Store alias that reports Python is absent. `.github/workflows/pages.yml` "
    "runs on `ubuntu-latest`, where `python3` is the real interpreter and is not to be \"fixed\" "
    "to match this line."
)

BARE_STEP7 = (
    "7. Run `python3 -m unittest discover -s tests` — the validator's own self-tests — "
    "then `python3 scripts/validate_continuity.py`."
)

SECTION_HEADING = "## 3. Mandatory resume protocol"


# --- primitives ----------------------------------------------------------------------------------


# --- the mutations -------------------------------------------------------------------------------


def step7_reverted_to_bare_python3(root: Path) -> None:
    """THE CONTROL THE BRIEF NAMES BY NAME. Putting a bare python3 command back must turn the
    guard red. Asserts the fixed text was really there before reverting to the pre-fix wording."""
    edit(root, AGENTS, FIXED_STEP7, BARE_STEP7)


def a_paired_sentence_added_elsewhere_in_section_3(root: Path) -> None:
    """EXPECTS GREEN. A second, correctly-paired POSIX/Windows sentence must not trip the guard -
    it checks the pairing, not the mere presence of the word python3 anywhere in the section."""
    edit(
        root, AGENTS,
        "An agent must not continue from chat recollection alone.",
        "A resuming agent may also confirm the interpreter directly: `python3 --version` on "
        "POSIX, `python --version` on Windows.\n\nAn agent must not continue from chat "
        "recollection alone.",
    )


def step7_rewritten_with_py_and_powershell(root: Path) -> None:
    """FIX ROUND 1's OWN CONTROL. EXPECTS GREEN. Correct dual-invocation content, worded with
    `py` and "PowerShell" instead of `python` and "Windows" - the exact rewrite that held real
    content and false-reded under the pre-round-1 guard, which required that specific vocabulary
    rather than the property (some other interpreter token beside python3) the guard now checks."""
    edit(root, AGENTS, FIXED_STEP7, PY_AND_POWERSHELL_STEP7)


def the_section_3_heading_renamed(root: Path) -> None:
    """Proves the anchor is asserted, not assumed: a renamed heading reports itself."""
    edit(root, AGENTS, SECTION_HEADING, "## 3. Resume protocol (renamed by a control)")


# (name, mutation, the test that must fail - or None where the suite must stay GREEN)
CONTROLS = [
    ("step 7 reverted to a bare python3 command - the pre-fix text",
     step7_reverted_to_bare_python3, "test_no_bare_python3_command"),
    ("EXPECTS GREEN: a properly-paired POSIX/Windows sentence added elsewhere in section 3",
     a_paired_sentence_added_elsewhere_in_section_3, None),
    ("EXPECTS GREEN (FIX ROUND 1): step 7 rewritten with py and PowerShell instead of python "
     "and Windows", step7_rewritten_with_py_and_powershell, None),
    ("the section 3 heading renamed", the_section_3_heading_renamed, "test_anchors_exist"),
]

def suite(root: Path) -> tuple[int, set[str]]:
    """The subject module, run inside `root` under `-B` as this runner has always run it."""
    return run_suite(root, "test_resume_protocol_command.py", no_bytecode=True)


def main() -> int:
    source, holder = arguments(__file__)

    code, failures = suite(fresh(source, holder, "control_00_unmutated"))
    bad = report_unmutated(code, failures, "copy")
    bad += suite_controls(CONTROLS, lambda name: fresh(source, holder, name), suite,
                          hole=HOLE_PLAIN)
    return summarise(len(CONTROLS), bad)


if __name__ == "__main__":
    raise SystemExit(main())
