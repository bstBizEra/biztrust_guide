#!/usr/bin/env python3
"""The mandatory resume protocol must not instruct a bare `python3` command (#348).

THE DEFECT. AGENTS.md section 3, the mandatory resume protocol every session and handoff must
execute, told the reader to run `python3 -m unittest discover -s tests` then
`python3 scripts/validate_continuity.py` with no platform qualification. On some Windows machines
`python3` resolves to the Microsoft Store app-execution alias, which prints a sentence that reads
like a diagnosis of a missing interpreter and is not one, so an agent following the charter
literally there must silently substitute a different command - which is exactly what section 3's
own closing line forbids ("An agent must not continue from chat recollection alone"). Whether that
alias is live is a fact about ONE machine's configuration, not the charter: on the machine this
package was written on, the alias was measured to resolve to a real Python 3.13 interpreter rather
than the broken shim, so the symptom did not reproduce there in that session - recorded in DEC-122
and the WP-116 checkpoint, not glossed over. The fix names the requirement and shows both
invocations - `python3` on POSIX and `python` on Windows - rather than hardcoding a path or adding a
runner script, which #348's acceptance criteria forbid outright, and it is worth keeping regardless
of any one machine's current alias state: the charter must not depend on it, because that state is
reversible (a Python installer can register over the alias, a user can toggle it off in Windows
Settings) and machine-local.

WHAT THIS GUARD CHECKS, exactly. Not the sentence's wording - the brief that opened #348 is explicit
that "the section's wording will change and a guard pinned to a sentence will fail for the wrong
reason." FIX ROUND 1 measured that the first version of this guard was pinned tighter than that: it
required the literal word "Windows" and the literal bare token "python" on the same line as
"python3", and a legitimate rewrite of step 7 using `py -m unittest` and the word "PowerShell"
instead - correct content, differently worded - turned it red. A guard that rejects legitimate
content gets switched off, and a false failure is worse than a miss, so the check now tests the
PROPERTY #348 actually names rather than a vocabulary: a line naming `python3` must also name SOME
other interpreter-invocation token on that same line - `python` (bare) or `py`, the two forms this
repository's own documents use for the non-python3 case (see docs/LIVE_PREVIEW.md and README.md's
local-preview sections) - so that the line is never a bare, single-path instruction. It does not
require the word "Windows", "POSIX" or "PowerShell" anywhere; those are prose choices, and pinning to
them is the exact mistake FIX ROUND 1 corrected.

A LIMIT, DECLARED RATHER THAN CHASED. The property is "some other interpreter token on the same
line," not "a second, actually-runnable invocation." A line reading "Run python3 -m unittest
discover -s tests; any python interpreter of 3.11 or later will do" passes this guard: the word
"python" inside that prose satisfies ALTERNATIVE_INTERPRETER_TOKEN even though the sentence never
shows a second command a Windows reader could run. That is a real false-green, found by the final
whole-branch review, and it is declared here rather than fixed by widening the pattern to demand a
backticked command, a leading verb, or some other shape: every such widening this module's own fix
round 1 tried first turned out to reject legitimate prose the reviewer or a future author could
reasonably write (see FIX ROUND 1 above - a vocabulary requirement traded a false red for nothing
and had to be removed). Chasing this hole would very likely trade it for a new false red; declaring
it, and trusting that AGENTS.md section 3's own review keeps prose honest, is the safer choice. See
`declared_non_coverage` in this package's checkpoint for the same limit recorded against the guard's
evidence.

WHY A LINE, NOT THE WHOLE SECTION. AGENTS.md's mandatory-resume-protocol steps are each one Markdown
list line with no internal wrapping - true of every step in section 3 today, checked by
test_anchors_exist below. Scoping the check to one line rather than "anywhere in section 3" is what
stops it from being satisfied by an alternative-invocation mention parked in some OTHER step while
the python3-only step stands unchanged; the pairing must be local to the instruction that names it.

STDLIB ONLY, NO SUBPROCESS. This repository has exactly four subprocess-calling modules under
tests/ by declared precedent - test_resume_reconciliation.py, test_resume_schema_identity.py,
test_validator_fails_closed.py and test_wp024_fixtures_are_sealed.py, measured with
`grep -lnE "subprocess[.](run|Popen|check_output|check_call)" tests/*.py` - and this module is not
the fifth. Everything it needs is one file read as text.

ANCHORS ARE ASSERTED, NOT ASSUMED, as tests/test_stale_records.py requires of its own readers.
section_3() returns "" when AGENTS.md or its section-3 heading is missing, rather than raising, so
test_anchors_exist owns the diagnosis and a renamed heading reports the heading rather than an
IndexError from the middle of a reader. THE CORPUS FLOOR IS NOT ZERO: test_anchors_exist also
asserts that section 3 still mentions `python3` or an alternative-interpreter token at all, because
a guard satisfied by its subject's having vanished entirely is worthless - this repository has
already paid for that shape of hole once (tests/test_stale_records.py's docstring, limit 8's absence
pair). If section 3 is ever rewritten to name no interpreter at all, this floor fails loudly and the
module must be re-derived, not left passing over nothing.

NEGATIVE CONTROLS, run by `scripts/wp116_controls.py`, a committed script rather than a prose claim,
on fresh copies with the unmutated copy run first and green:

  * step 7 reverted to a bare `python3 -m unittest discover -s tests`, with no other interpreter
    token anywhere on the same line          -> test_no_bare_python3_command FAILS
  * a second, properly-paired POSIX/Windows sentence added elsewhere in section 3, naming `python3`
    and `python` together on its own line    -> EXPECTED GREEN
  * FIX ROUND 1's OWN CONTROL: step 7 rewritten using `py -m unittest ...` / `py
    scripts/validate_continuity.py` and the word "PowerShell" rather than "python" and "Windows" -
    the exact rewrite that held real content and false-reded under the pre-round-1 guard
                                              -> EXPECTED GREEN: the guard checks the property
    (another interpreter token beside python3), not a fixed vocabulary
  * the section 3 heading renamed            -> test_anchors_exist FAILS

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

# "python3" is its own token, never conflated with the alternative-interpreter tokens below - a
# line can name python3 with or without also naming one of them, and that distinction is the whole
# check.
PYTHON3_TOKEN = re.compile(r"\bpython3\b")

# THE PROPERTY, NOT A VOCABULARY. FIX ROUND 1 measured that requiring the literal word "Windows"
# and the literal bare token "python" false-redded a legitimate rewrite of step 7 that used
# `py -m unittest ...` and the word "PowerShell" instead - correct content, worded differently, and
# a guard that rejects correct content is exactly the failure this repository refuses to keep. So
# the check is: does this line name ANY interpreter-invocation token other than python3 itself?
# "python" (bare) and "py" are the two this repository's own documents already use for the
# non-python3 case (docs/LIVE_PREVIEW.md's Windows PowerShell blocks, README.md's local-preview
# section) - not an exhaustive vocabulary, just the two forms a line needs at least one of to avoid
# being a single, bare, unqualified python3 instruction.
#
# `(?<!\.)` GUARDS THE SECOND FORM ONLY, and FIX ROUND 1's own control caught the reason: the bare
# `\bpy\b` alternative matched the file extension in `scripts/validate_continuity.py` - the "py" in
# "continuity.py" sits between a "." and a backtick, both non-word characters, so `\b` holds on
# both sides with nothing to stop it. That false match made the reverted, pre-fix step 7 (which
# names only `python3`, twice, and never `py` as a command) read as already having an alternative
# token, and the control that was supposed to prove the guard can fail passed over a guard that no
# longer could. The lookbehind refuses a `py` immediately preceded by `.`; a `py` used as a command
# word - preceded by whitespace, a backtick or the start of the line - is untouched.
ALTERNATIVE_INTERPRETER_TOKEN = re.compile(r"\bpython\b|(?<!\.)\bpy\b")


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


def interpreter_lines(section: str) -> list[str]:
    """Every line of the section naming python3 or an alternative-interpreter token at all."""
    return [
        line for line in section.splitlines()
        if PYTHON3_TOKEN.search(line) or ALTERNATIVE_INTERPRETER_TOKEN.search(line)
    ]


def bare_python3_lines(section: str) -> list[str]:
    """Lines that name `python3` without also naming SOME other interpreter-invocation token
    (`python` or `py`) on that same line. This is the whole check: the property #348 names -
    python3 must never be the only invocation a line offers - not a fixed vocabulary of words
    like "Windows" that a correct rewrite might reasonably not use."""
    bad = []
    for line in section.splitlines():
        if PYTHON3_TOKEN.search(line) and not ALTERNATIVE_INTERPRETER_TOKEN.search(line):
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
            interpreter_lines(section),
            "section 3 no longer names python3 or an alternative interpreter token at all; this "
            "guard's subject has vanished. If the resume protocol genuinely no longer names a "
            "Python interpreter by any form, this test should be re-derived rather than left "
            "passing over nothing.")


class TestNoBarePython3(unittest.TestCase):
    """The property, not the vocabulary. See the module docstring for the full case, including
    FIX ROUND 1's correction of the pre-round-1 version of this check."""

    def test_no_bare_python3_command(self) -> None:
        bad = bare_python3_lines(section_3())
        self.assertFalse(
            bad,
            f"AGENTS.md section 3 instructs `python3` on a line with no other interpreter "
            f"invocation (`python` or `py`) beside it. python3 may resolve to a Microsoft Store "
            f"alias that reports Python is absent on some Windows machines, so an agent following "
            f"this line literally there must silently substitute a different command - which is "
            f"the #348 defect. Line(s): {bad}")


if __name__ == "__main__":
    unittest.main()
