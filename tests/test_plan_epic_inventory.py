#!/usr/bin/env python3
"""Section 9.1's epic inventory agrees with the epic rows BIZTRUST-PLAN-001 actually holds.

Section 9.1 is the plan's canonical inventory, and the all-phase guide's map makes every index,
denominator, percentage and ticket total depend on it. Nothing held it to the plan until this test:
an epic added to a phase section and not to 9.1 would leave the table quietly wrong, which is how
three different figures came to be in circulation before WP-098 settled them.

The counting rule is the whole point, so it is stated here rather than left in the code. **Each
phase is counted inside its own section, by its own identifiers.** The plan's section 9 is a mapping
table from the previous plan to this one, and its first column holds the previous plan's retired
`P2.n` and `P3.n` identifiers. A count that matches an identifier prefix across the whole file reads
those retired rows as live ones and gives 10 and 11 where the true figures are 9 and 10. That is the
error this test exists to make impossible to repeat, so it must never grow a whole-file search.

Section 8's rows are expansion streams, not epics. Continuous Operations contributes nothing to any
denominator: a stream has no completion state. Its table's header line is not a stream either, which
is where the figure 62 came from.

Identifiers are counted, not rows, because an epic is its identifier; but the rows are counted too, and
the two must agree. `md_rows` keys its result by first cell, so one identifier written on two rows would
otherwise collapse into one entry and go unnoticed.

Positive controls: the readers must find epics in every phase, streams in section 8, a row for every
phase in 9.1, and both totals.

Negative controls. Six are tests here, on in-memory copies of the plan: an epic added to a phase, one
identifier written on two rows, a row shown inside a fence, the same for every fence syntax, a fence left
open, and section 8's header. Three more were
run by hand against the file under WP-099 on 2026-09-06, each failing for its own reason:

  * an epic row added to section 6 and not to 9.1        -> test_every_phase_agrees FAILS, and the totals
  * 9.1's P3 count changed to 11                         -> test_every_phase_agrees FAILS, and the control
  * a phase grown, 9.1 following, the totals left at 64  -> test_the_totals_are_the_sum FAILS

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from showcase_parity import md_row_count, md_rows

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "architecture" / "BIZTRUST-PLAN-001.md"

# key, section start, section end, the identifier pattern that phase's own rows use.
PHASES: tuple[tuple[str, str, str, str], ...] = (
    ("p0", "\n## 4. P0", "\n## 5. ", r"P0\.\d+"),
    ("p1a", "\n### 5.1 ", "\n### 5.2 ", r"P1A\.\d+"),
    ("p1b", "\n### 5.2 ", "\n### 5.3 ", r"P1B\.\d+"),
    ("p1c", "\n### 5.3 ", "\n### 5.4 ", r"P1C\.\d+"),
    ("p2", "\n## 6. P2", "\n## 7. ", r"P2[A-Z]?\.\d+"),
    ("p3", "\n## 7. P3", "\n## 8. ", r"P3[A-Z]?\.\d+"),
)
STREAMS = ("\n## 8. Continuous Operations", "\n## 9. ", r"E\d+ .+")
INVENTORY = ("\n### 9.1 ", "\n## 10. ", r"The architecture phase|Continuous Operations|P0|P1[A-C]|P2|P3")
TOTALS = re.compile(r"\*\*(\d+) epics across the five phases, of which (\d+) lie beyond P0\.\*\*")

# The letter each phase's identifiers may carry is open on purpose: a new P2G or P3K sub-stream must
# be counted, not skipped. A pattern that named only the letters in use today would pass while the
# plan grew past it, which is the failure this test is for.


FENCE_MARK = r"^ {0,3}(?:```|~~~)"
FENCE = re.compile(rf"{FENCE_MARK}.*?{FENCE_MARK}[^\n]*$", re.M | re.S)
FENCE_OPEN = re.compile(FENCE_MARK, re.M)


def between(text: str, start: str, end: str) -> str:
    """The text between the first `start` and the next `end`, fenced blocks removed.

    Text rather than a path, so a control can modify the plan before it is read. Fenced blocks go
    because a table row shown as an example inside one is not an epic; the plan already carries a
    fence in section 5.5, and a documentation example in a phase section would otherwise be counted.
    Backtick and tilde fences both count, indented up to three spaces as CommonMark allows, and a fence
    left open is named as itself rather than left to surface as a miscount.
    """
    assert start in text, f"no {start!r} in the plan"
    rest = text.split(start, 1)[1]
    assert end in rest, f"no {end!r} after {start!r}"
    stripped = FENCE.sub("", rest.split(end, 1)[0])
    assert not FENCE_OPEN.search(stripped), (
        f"a fenced block is opened and not closed between {start!r} and {end!r}; the counts would be read "
        f"through it, so the plan's fence is the thing to fix, not the count")
    return stripped


def epic_ids(plan: str) -> dict[str, set[str]]:
    """Each phase's epic identifiers, read inside that phase's own section."""
    return {key: set(md_rows(between(plan, start, end), pattern)) for key, start, end, pattern in PHASES}


def epic_rows(plan: str) -> dict[str, int]:
    """Each phase's epic *rows*, duplicates included.

    `md_rows` keys its result by first cell, so two rows carrying one identifier collapse into one
    entry and the count comes up short. Counting the rows as well as the identifiers is what notices
    that, and both readings come from the same seam so they cannot drift apart.
    """
    return {key: md_row_count(between(plan, start, end), pattern) for key, start, end, pattern in PHASES}


def epic_counts(plan: str) -> dict[str, int]:
    """Each phase's epic count: the identifiers it lists, inside its own section."""
    return {key: len(ids) for key, ids in epic_ids(plan).items()}


def stream_count(plan: str) -> int:
    start, end, pattern = STREAMS
    return len(md_rows(between(plan, start, end), pattern))


def inventory(plan: str) -> dict[str, int]:
    """Section 9.1's table: phase -> the count it claims."""
    start, end, pattern = INVENTORY
    rows = md_rows(between(plan, start, end), pattern)
    return {phase: int(cells[0]) for phase, cells in rows.items()}


def totals(plan: str) -> tuple[int, int]:
    """The sentence's two figures: across the five phases, and beyond P0."""
    m = TOTALS.search(plan)
    assert m, "section 9.1 no longer states its totals in the form the test reads"
    return int(m.group(1)), int(m.group(2))


def plan_text() -> str:
    return PLAN.read_text(encoding="utf-8")


class TestTheReadersFindSomething(unittest.TestCase):
    """Positive controls. Without these, every comparison below can pass over nothing."""

    def test_every_phase_has_epics(self) -> None:
        counts = epic_counts(plan_text())
        self.assertEqual(len(PHASES), len(counts))
        for key, n in counts.items():
            with self.subTest(phase=key):
                self.assertGreater(n, 0, f"no epic rows found in the {key} section; the section markers have moved")

    def test_section_8_has_streams(self) -> None:
        self.assertGreater(stream_count(plan_text()), 0, "no expansion streams found in section 8")

    def test_the_inventory_has_a_row_for_every_phase(self) -> None:
        rows = inventory(plan_text())
        for key in [k for k, *_ in PHASES] + ["the architecture phase", "continuous operations"]:
            with self.subTest(phase=key):
                self.assertIn(key, rows, f"section 9.1 has no row for {key}")

    def test_the_totals_are_stated(self) -> None:
        across, beyond = totals(plan_text())
        self.assertGreater(across, beyond)


class TestTheReaderCanFail(unittest.TestCase):
    """Negative controls, on copies of the plan. A guard that cannot fail guards nothing."""

    def test_an_epic_added_to_a_phase_is_seen(self) -> None:
        plan = plan_text()
        before = epic_counts(plan)["p2"]
        grown = plan.replace("\n## 7. P3", "\n| P2Z.9 | An epic added by this control | — |\n\n## 7. P3", 1)
        self.assertEqual(before + 1, epic_counts(grown)["p2"],
                         "an epic added to a phase section was not counted; a new sub-stream letter would be missed")

    def test_one_identifier_on_two_rows_is_seen(self) -> None:
        plan = plan_text()
        doubled = plan.replace("\n## 7. P3", "\n| P2A.1 | The same identifier twice | — |\n\n## 7. P3", 1)
        self.assertEqual(epic_counts(plan)["p2"], epic_counts(doubled)["p2"],
                         "two rows carrying one identifier are one epic, so the identifier count must not move")
        self.assertEqual(epic_rows(plan)["p2"] + 1, epic_rows(doubled)["p2"],
                         "the row count must move, which is how the duplicate is noticed")

    def test_a_wrong_inventory_figure_is_seen(self) -> None:
        plan = plan_text()
        wrong = plan.replace("| P3 | 10 |", "| P3 | 11 |", 1)
        self.assertNotEqual(plan, wrong, "section 9.1 no longer states P3 as 10; re-derive this control")
        self.assertNotEqual(epic_counts(wrong)["p3"], inventory(wrong)["p3"])

    def test_a_row_shown_inside_a_fence_is_not_an_epic(self) -> None:
        plan = plan_text()
        example = "\n```text\n| P0.1 | An example, not an epic | — |\n```\n"
        illustrated = plan.replace("\n## 5. ", example + "\n## 5. ", 1)
        self.assertEqual(epic_counts(plan)["p0"], epic_counts(illustrated)["p0"],
                         "a table row shown as an example inside a fence was counted as an epic")
        self.assertEqual(epic_rows(plan)["p0"], epic_rows(illustrated)["p0"],
                         "the row counter read inside a fence, so it would disagree with the identifier count")

    def test_every_fence_syntax_is_skipped(self) -> None:
        plan = plan_text()
        row = "| P0.1 | An example, not an epic | — |"
        for opener, closer in (("```text", "```"), ("~~~text", "~~~"), ("   ```text", "   ```")):
            with self.subTest(fence=opener.strip()):
                illustrated = plan.replace("\n## 5. ", f"\n{opener}\n{row}\n{closer}\n\n## 5. ", 1)
                self.assertEqual(epic_rows(plan)["p0"], epic_rows(illustrated)["p0"],
                                 f"a row inside a {opener.strip()} fence was counted as an epic row")

    def test_a_fence_left_open_says_so(self) -> None:
        plan = plan_text()
        broken = plan.replace("\n## 5. ", "\n```text\n| P0.1 | An example | — |\n\n## 5. ", 1)
        with self.assertRaises(AssertionError) as caught:
            epic_rows(broken)
        self.assertIn("opened and not closed", str(caught.exception),
                      "an unclosed fence must name itself rather than surface as a miscount")

    def test_the_streams_header_is_not_a_stream(self) -> None:
        plan = plan_text()
        header = "| Stream | Capability | Carries from the previous plan |"
        self.assertIn(header, plan, "section 8's header has changed; re-derive this control")
        self.assertEqual(stream_count(plan), stream_count(plan.replace(header, "", 1)),
                         "the streams table's header row was counted as a stream, which is where 62 came from")


class TestTheInventoryAgreesWithThePlan(unittest.TestCase):
    def test_every_phase_agrees(self) -> None:
        plan = plan_text()
        counted, claimed = epic_counts(plan), inventory(plan)
        for key, n in counted.items():
            with self.subTest(phase=key):
                self.assertEqual(n, claimed[key],
                                 f"section 9.1 says the {key} phase has {claimed[key]} epics; its own section holds {n}. "
                                 f"The inventory is the thing to correct, unless the section is wrong.")

    def test_the_architecture_phase_and_continuous_operations_hold_no_epics(self) -> None:
        claimed = inventory(plan_text())
        self.assertEqual(0, claimed["the architecture phase"])
        self.assertEqual(0, claimed["continuous operations"],
                         "Continuous Operations is an operating lifecycle, not a build phase; its streams are not epics")

    def test_no_epic_identifier_is_listed_twice(self) -> None:
        plan = plan_text()
        counts, rows = epic_counts(plan), epic_rows(plan)
        for key in counts:
            with self.subTest(phase=key):
                self.assertEqual(rows[key], counts[key],
                                 f"the {key} section holds {rows[key]} epic rows for {counts[key]} identifiers; "
                                 f"one identifier is listed twice, and the inventory would count it once")

    def test_section_8_holds_streams_and_no_epics(self) -> None:
        plan = plan_text()
        start, end, _ = STREAMS
        body = between(plan, start, end)
        self.assertGreater(stream_count(plan), 0, "no expansion streams found in section 8")
        for _, _, _, pattern in PHASES:
            with self.subTest(pattern=pattern):
                self.assertEqual(0, md_row_count(body, pattern),
                                 "section 8 holds an epic identifier; its rows are streams, and streams are not epics")

    def test_the_totals_are_the_sum(self) -> None:
        plan = plan_text()
        counted = epic_counts(plan)
        across, beyond = totals(plan)
        self.assertEqual(sum(counted.values()), across, "the stated total is not the sum of the phase counts")
        self.assertEqual(across - counted["p0"], beyond, "the beyond-P0 figure is not the total less P0")


if __name__ == "__main__":
    unittest.main()
