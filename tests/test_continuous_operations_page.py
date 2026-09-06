#!/usr/bin/env python3
"""reference/continuous-operations.html is a rendering of PLAN-001 sections 8 and 11, and must stay one.

The page carries two tables: the eight expansion streams (PLAN-001 section 8) and their
entry conditions (section 11). Each is read cell for cell from the plan and compared with
the page after the same normalisation the phase-page test uses: tags and backticks
stripped, whitespace collapsed, case folded. The plan is the source; the page is a second
rendering, and a page that drifts from the plan is a defect (issue #32 measured what a
page that restated a record cost).

Two positive controls guard the parsers: the plan must yield exactly E1 to E8 in both
sections, and the page must parse at least one row per table. Two link checks hold the
page in the guide: the phase overview's Continuous Operations row and the P3 manual's
After section must reach it, since the page exists so that both have one place to point.

Negative controls (run 2026-09-06 under WP-056, on in-memory copies):
  * Change E4's capability on the page            -> test_streams_match_the_plan FAILS
  * Drop E8's row from the conditions table        -> test_conditions_match_the_plan FAILS
  * Remove the overview's link                     -> test_overview_and_p3_link_here FAILS

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import html as html_mod
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "reference" / "continuous-operations.html"
PLAN = ROOT / "docs" / "architecture" / "BIZTRUST-PLAN-001.md"
OVERVIEW = ROOT / "phases" / "overview.html"
P3 = ROOT / "phases" / "p3.html"

STREAM_IDS = {f"E{n}" for n in range(1, 9)}


def _norm(fragment: str) -> str:
    s = re.sub(r"<[^>]+>", " ", fragment)
    s = html_mod.unescape(s).replace("`", "")
    return re.sub(r"\s+", " ", s).strip().lower()


def _plan_section(start: str, end: str) -> str:
    text = PLAN.read_text(encoding="utf-8")
    return text.split(start, 1)[1].split(end, 1)[0]


def plan_rows(start: str, end: str) -> dict[str, tuple[str, str, str]]:
    """`| E1 Tenant Scale | cell | cell |` -> {"E1": ("tenant scale", cell, cell)}."""
    out: dict[str, tuple[str, str, str]] = {}
    for line in _plan_section(start, end).splitlines():
        m = re.match(r"^\|\s*(E[1-8])\s+([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$", line)
        if m:
            out[m.group(1)] = (_norm(m.group(2)), _norm(m.group(3)), _norm(m.group(4)))
    return out


def page_rows(section_id: str) -> dict[str, tuple[str, str, str]]:
    text = PAGE.read_text(encoding="utf-8")
    m = re.search(rf'<section id="{section_id}".*?</section>', text, re.S)
    assert m, f"section {section_id} missing from the page"
    out: dict[str, tuple[str, str, str]] = {}
    for row in re.finditer(r"<tr><td><strong>(E[1-8])</strong>\s*<small>(.*?)</small></td><td>(.*?)</td><td>(.*?)</td></tr>", m.group(0), re.S):
        out[row.group(1)] = (_norm(row.group(2)), _norm(row.group(3)), _norm(row.group(4)))
    return out


def plan_streams() -> dict[str, tuple[str, str, str]]:
    return plan_rows("\n## 8. Continuous Operations", "\n## 9. ")


def plan_conditions() -> dict[str, tuple[str, str, str]]:
    return plan_rows("\n## 11. Expansion streams", "\n## 12. ")


class TestCorpusIsPresent(unittest.TestCase):
    """Positive controls. Without these every assertion below can pass over nothing."""

    def test_plan_yields_eight_streams_in_both_sections(self) -> None:
        self.assertEqual(STREAM_IDS, set(plan_streams()), "PLAN-001 section 8 no longer lists exactly E1 to E8; re-derive this test")
        self.assertEqual(STREAM_IDS, set(plan_conditions()), "PLAN-001 section 11 no longer lists exactly E1 to E8; re-derive this test")

    def test_page_parses(self) -> None:
        self.assertTrue(PAGE.is_file(), "reference/continuous-operations.html is missing")
        self.assertGreaterEqual(len(page_rows("streams")), 1, "no stream rows parsed; the table shape changed or the parser is wrong")
        self.assertGreaterEqual(len(page_rows("conditions")), 1, "no condition rows parsed; the table shape changed or the parser is wrong")


class TestParityWithThePlan(unittest.TestCase):
    def test_streams_match_the_plan(self) -> None:
        self.assertEqual(plan_streams(), page_rows("streams"), "the streams table disagrees with PLAN-001 section 8")

    def test_conditions_match_the_plan(self) -> None:
        self.assertEqual(plan_conditions(), page_rows("conditions"), "the entry-conditions table disagrees with PLAN-001 section 11")

    def test_page_names_no_gate_the_plan_does_not(self) -> None:
        gates = set(re.findall(r"\bBT-G[0-9]\b", PAGE.read_text(encoding="utf-8")))
        plan = set(re.findall(r"\bBT-G[0-9]\b", _plan_section("\n## 8. Continuous Operations", "\n## 9. ") + _plan_section("\n## 11. Expansion streams", "\n## 12. ")))
        self.assertLessEqual(gates, plan, f"the page names gates the plan's sections 8 and 11 do not: {sorted(gates - plan)}")


class TestThePageIsReachable(unittest.TestCase):
    def test_overview_and_p3_link_here(self) -> None:
        for path in (OVERVIEW, P3):
            with self.subTest(page=path.name):
                self.assertIn('href="../reference/continuous-operations.html"', path.read_text(encoding="utf-8"),
                              f"{path.name} does not link the Continuous Operations page")


if __name__ == "__main__":
    unittest.main()
