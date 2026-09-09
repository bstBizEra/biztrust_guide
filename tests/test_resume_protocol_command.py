#!/usr/bin/env python3
"""The mandatory resume protocol must not instruct a bare `python3` command (#348).

THE DEFECT. AGENTS.md section 3, the mandatory resume protocol every session and handoff must
execute, told the reader to run `python3 -m unittest discover -s tests` then
`python3 scripts/validate_continuity.py` with no platform qualification. On Windows `python3`
resolves to the Microsoft Store app-execution alias: it prints a sentence that reads like a
diagnosis of a missing interpreter and is not one, so an agent following the charter literally on
that platform must silently substitute a different command - which is exactly what section 3's own
closing line forbids ("An agent must not continue from chat recollection alone"). The fix names the
requirement and shows both invocations - `python3` on POSIX, `python` on Windows - rather than
hardcoding a path or adding a runner script, which #348's acceptance criteria forbid outright.

WHAT THIS GUARD CHECKS, exactly. Not the sentence's wording - the brief that opened #348 is explicit
that "the section's wording will change and a guard pinned to a sentence will fail for the wrong
reason." It checks the COMMAND STRING: within section 3, every line that names `python3` must also
name the bare Windows form (`python`, without the `3`) and the word `Windows`, on the same line. A
step that only ever says `python3` - the original defect, and the shape of the most likely
regression, a copy-paste of the POSIX half without its Windows sibling - fails. A step naming both
forms together, however it is worded, passes.

WHY A LINE, NOT THE WHOLE SECTION. AGENTS.md's mandatory-resume-protocol steps are each one Markdown
list line with no internal wrapping - true of every step in section 3 today, checked by
test_anchors_exist below. Scoping the check to one line rather than "anywhere in section 3" is what
stops it from being satisfied by a Windows caveat parked in some OTHER step while the python3-only
step stands unchanged; the pairing must be local to the instruction that names it.

STDLIB ONLY, NO SUBPROCESS. This repository has exactly four subprocess-calling modules under
tests/ by declared precedent - test_resume_reconciliation.py, test_resume_schema_identity.py,
test_validator_fails_closed.py and test_wp024_fixtures_are_sealed.py, measured with
`grep -lnE "subprocess[.](run|Popen|check_output|check_call)" tests/*.py` - and this module is not
the fifth. Everything it needs is one file read as text.

ANCHORS ARE ASSERTED, NOT ASSUMED, as tests/test_stale_records.py requires of its own readers.
section_3() returns "" when AGENTS.md or its section-3 heading is missing, rather than raising, so
test_anchors_exist owns the diagnosis and a renamed heading reports the heading rather than an
IndexError from the middle of a reader. THE CORPUS FLOOR IS NOT ZERO: test_anchors_exist also
asserts that section 3 still mentions `python3` at all, because a guard satisfied by its subject's
having vanished entirely is worthless - this repository has already paid for that shape of hole
once (tests/test_stale_records.py's docstring, limit 8's absence pair). If section 3 is ever
rewritten to name no interpreter at all, this floor fails loudly and the module must be re-derived,
not left passing over nothing.

NEGATIVE CONTROL, run by `scripts/wp116_controls.py`, a committed script rather than a prose claim,
on fresh copies with the unmutated copy run first and green:

  * step 7 reverted to a bare `python3 -m unittest discover -s tests`, with no Windows or bare
    `python` anywhere on the same line     -> test_no_bare_python3_command FAILS
  * a second, properly-paired POSIX/Windows sentence added elsewhere in section 3, naming
    `python3`, `python` and `Windows` together on its own line   -> EXPECTED GREEN: this guard does
    not ration legitimate dual-platform content, it only refuses a python3 mention with no Windows
    sibling on the same line
  * the section 3 heading renamed      -> test_anchors_exist FAILS

Defect 2 (#361, AGENTS.md section 10.3's stale page count) gets no guard here or anywhere else in
this module: its repair deletes the hand-maintained number rather than correcting it, and a deleted
claim cannot drift. A guard is for a claim that can go stale; this module is scoped to the one claim
in AGENTS.md that still can.

Stdlib only: no third-party import, no network, no subprocess.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS = ROOT / "AGENTS.md"

SECTION_HEADING = "## 3. Mandatory resume protocol"
NEXT_HEADING = re.compile(r"\n## ", re.M)

# One token per match: "python3" is preferred over "python" wherever the trailing "3" is present,
# so a line naming both forms yields the two-element set {"python3", "python"} rather than one.
PYTHON_TOKEN = re.compile(r"\bpython3?\b")
WINDOWS_TOKEN = re.compile(r"\bWindows\b")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section_3() -> str:
    """Section 3's text, or "" when AGENTS.md or its heading is missing.

    Empty rather than raising, as tests/test_stale_records.py's section_14() is, so
    test_anchors_exist owns the diagnosis rather than a reader crashing on a renamed heading.
    """
    if not AGENTS.is_file():
        return ""
    text = read(AGENTS)
    if SECTION_HEADING not in text:
        return ""
    start = text.index(SECTION_HEADING)
    m = NEXT_HEADING.search(text, start + 1)
    return text[start: m.start() if m else len(text)]


def python_lines(section: str) -> list[str]:
    """Every line of the section naming python3 or python at all."""
    return [line for line in section.splitlines() if PYTHON_TOKEN.search(line)]


def bare_python3_lines(section: str) -> list[str]:
    """Lines that name `python3` without also naming the bare Windows `python` form and the word
    `Windows`, on that same line. This is the whole check: scoped to the command string a line
    carries, not to the section's surrounding prose."""
    bad = []
    for line in python_lines(section):
        tokens = set(PYTHON_TOKEN.findall(line))
        if "python3" in tokens and not ("python" in tokens and WINDOWS_TOKEN.search(line)):
            bad.append(line.strip())
    return bad


class TestAnchorsExist(unittest.TestCase):
    """A reader scoped to nothing reads everything, and a floor is not the same as non-empty."""

    def test_anchors_exist(self) -> None:
        self.assertTrue(AGENTS.is_file(), AGENTS)
        self.assertIn(
            SECTION_HEADING, read(AGENTS),
            "AGENTS.md's mandatory resume protocol heading moved; this guard is scoped to it by "
            "name and has nothing to check without it")
        section = section_3()
        self.assertTrue(section, "section_3() returned empty despite the heading being present")
        self.assertTrue(
            python_lines(section),
            "section 3 no longer mentions python3 or python at all; this guard's subject has "
            "vanished. If the resume protocol genuinely no longer names a Python interpreter by "
            "either form, this test should be re-derived rather than left passing over nothing.")


class TestNoBarePython3(unittest.TestCase):
    """The command string, not the surrounding prose. See the module docstring for the full case."""

    def test_no_bare_python3_command(self) -> None:
        bad = bare_python3_lines(section_3())
        self.assertFalse(
            bad,
            f"AGENTS.md section 3 instructs `python3` on a line with no bare `python` (Windows) "
            f"form and no mention of Windows beside it. On Windows, python3 resolves to a "
            f"non-functional Microsoft Store alias, so an agent following this line literally "
            f"there must silently substitute a different command - which is the #348 defect. "
            f"Line(s): {bad}")


if __name__ == "__main__":
    unittest.main()
