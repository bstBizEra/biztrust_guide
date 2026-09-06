#!/usr/bin/env python3
"""landing/roadmap.html projects PLAN-001 sections 2, 8 and 10.1, and must keep projecting them.

The page carries three tables copied cell for cell from the plan: the five phases (section 2),
the labels (section 10.1) and the expansion streams (section 8). Each is read from the plan and
compared with the page after a normalisation copied from the plan-rendering tests, with tags
dropped and the plan's bold markers stripped as well: backticks stripped, whitespace collapsed, case folded. The plan is the source; the page is a
projection, and a projection that drifts is the defect issue #32 measured.

Positive controls: the plan must yield five phases, five labels and eight streams; the page must
parse at least one row per table.

Negative controls (run 2026-09-06 under WP-065, on in-memory copies):
  * Change P2's purpose on the page              -> test_phases_match_the_plan FAILS
  * Drop label D's row from the page             -> test_labels_match_the_plan FAILS
  * Rename E7 on the page                        -> test_streams_match_the_plan FAILS

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest
from pathlib import Path
try:
    from showcase_parity import section, md_rows, page_table
except ModuleNotFoundError:  # invoked by module name from the repository root rather than by discovery
    from tests.showcase_parity import section, md_rows, page_table

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "landing" / "roadmap.html"
PLAN = ROOT / "docs" / "architecture" / "BIZTRUST-PLAN-001.md"


def plan_phases() -> dict[str, tuple[str, ...]]:
    return md_rows(section(PLAN, "\n## 2. The five phases", "\n## 3. "), r"Architecture|P[0-3]")


def plan_labels() -> dict[str, tuple[str, ...]]:
    return md_rows(section(PLAN, "\n### 10.1 ", "\n### 10.2 "), r"[A-E]")


def plan_streams() -> dict[str, tuple[str, ...]]:
    rows = md_rows(section(PLAN, "\n## 8. Continuous Operations", "\n## 9. "), r"E[1-8] .+")
    return {k: v[:1] for k, v in rows.items()}  # the page shows the capability column only


class TestCorpusIsPresent(unittest.TestCase):
    """Positive controls. Without these the comparisons below can pass over nothing."""

    def test_plan_yields_its_tables(self) -> None:
        self.assertEqual(5, len(plan_phases()), "PLAN-001 section 2 no longer yields five phases; re-derive this test")
        self.assertEqual(5, len(plan_labels()), "PLAN-001 section 10.1 no longer yields five labels; re-derive this test")
        self.assertEqual(8, len(plan_streams()), "PLAN-001 section 8 no longer yields eight streams; re-derive this test")

    def test_page_parses(self) -> None:
        self.assertTrue(PAGE.is_file(), "landing/roadmap.html is missing")
        for table in ("phases", "labels", "streams"):
            with self.subTest(table=table):
                self.assertGreaterEqual(len(page_table(PAGE, table)), 1, f"no rows parsed from the {table} table")


class TestParityWithThePlan(unittest.TestCase):
    def test_phases_match_the_plan(self) -> None:
        self.assertEqual(plan_phases(), page_table(PAGE, "phases"), "the phases table disagrees with PLAN-001 section 2")

    def test_labels_match_the_plan(self) -> None:
        self.assertEqual(plan_labels(), page_table(PAGE, "labels"), "the labels table disagrees with PLAN-001 section 10.1")

    def test_streams_match_the_plan(self) -> None:
        self.assertEqual(plan_streams(), page_table(PAGE, "streams"), "the streams table disagrees with PLAN-001 section 8")


if __name__ == "__main__":
    unittest.main()
