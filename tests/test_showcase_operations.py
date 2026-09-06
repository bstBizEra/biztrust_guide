#!/usr/bin/env python3
"""landing/operations.html projects BIZTRUST-PLAN-001 sections 8 and 11, and must keep projecting them.

Two things on the page are copied from the plan and held here: the eight expansion streams
(section 8, cell for cell) and their entry conditions (section 11, cell for cell). The loop's
reading, the plain-words paragraph and the carried epics' summaries are the page's own restatements
and are not held; their source lines say so.

Positive controls: the plan must yield exactly eight rows in each section, and the page at least one
row per table; a row count of exactly eight per table catches an extra or duplicated row.

Negative controls (run 2026-09-06 under WP-071, on in-memory copies):
  * Change E4's capability on the page               -> test_streams_match_the_plan FAILS
  * Drop E8's row from the conditions table          -> test_conditions_match_the_plan FAILS
  * Add an E9 row to the streams table               -> test_each_table_has_exactly_eight_rows FAILS

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "landing" / "operations.html"
PLAN = ROOT / "docs" / "architecture" / "BIZTRUST-PLAN-001.md"

try:
    from showcase_parity import section, md_rows, page_table, page_row_count
except ModuleNotFoundError:  # invoked by module name from the repository root rather than by discovery
    from tests.showcase_parity import section, md_rows, page_table, page_row_count


STREAM = r"E[1-8] .+"


def plan_streams() -> dict[str, tuple[str, ...]]:
    return md_rows(section(PLAN, "\n## 8. Continuous Operations", "\n## 9. "), STREAM)


def plan_conditions() -> dict[str, tuple[str, ...]]:
    return md_rows(section(PLAN, "\n## 11. Expansion streams", "\n## 12. "), STREAM)


class TestCorpusIsPresent(unittest.TestCase):
    """Positive controls. Without these the comparisons below can pass over nothing."""

    def test_plan_yields_eight_streams_in_each_section(self) -> None:
        self.assertEqual(8, len(plan_streams()), "PLAN-001 section 8 no longer yields eight streams; re-derive this test")
        self.assertEqual(8, len(plan_conditions()), "PLAN-001 section 11 no longer yields eight conditions; re-derive this test")

    def test_page_parses(self) -> None:
        self.assertTrue(PAGE.is_file(), "landing/operations.html is missing")
        for table in ("streams", "conditions"):
            with self.subTest(table=table):
                self.assertGreaterEqual(len(page_table(PAGE, table)), 1)

    def test_each_table_has_exactly_eight_rows(self) -> None:
        for table in ("streams", "conditions"):
            with self.subTest(table=table):
                self.assertEqual(8, page_row_count(PAGE, table), f"the {table} table does not have exactly eight rows")


class TestParityWithTheRecords(unittest.TestCase):
    def test_streams_match_the_plan(self) -> None:
        self.assertEqual(plan_streams(), page_table(PAGE, "streams"), "the streams table disagrees with PLAN-001 section 8")

    def test_conditions_match_the_plan(self) -> None:
        self.assertEqual(plan_conditions(), page_table(PAGE, "conditions"), "the conditions table disagrees with PLAN-001 section 11")


if __name__ == "__main__":
    unittest.main()
