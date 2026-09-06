#!/usr/bin/env python3
"""landing/p0.html projects BIZTRUST-PLAN-001 section 4 and FLOWS.md section 3, and must keep projecting them.

Three things on the page are copied from records and held here: the thirteen-epic table (plan
section 4, cell for cell), the seven lines of the mandatory proof (plan section 4, verbatim), and
the minimum negative proof matrix (FLOWS.md section 3, cell for cell). The six-step sequence, the
evidence-record paragraph and the gate slab are the page's own restatements and are not held; their
source lines say so.

Positive controls: the plan must yield thirteen epics and seven proof lines, the flows record eight
matrix rows, and the page at least one row per table and one item in the list.

Negative controls (run 2026-09-06 under WP-067, on in-memory copies):
  * Change P0.7's exit evidence on the page             -> test_epics_match_the_plan FAILS
  * Drop the fourth proof line from the page            -> test_proof_matches_the_plan FAILS
  * Reword the bypass row's database expectation        -> test_matrix_matches_the_flows_record FAILS

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "landing" / "p0.html"
PLAN = ROOT / "docs" / "architecture" / "BIZTRUST-PLAN-001.md"
FLOWS = ROOT / "docs" / "architecture" / "FLOWS.md"

try:
    from showcase_parity import norm, section, md_rows, page_table, page_list
except ModuleNotFoundError:  # invoked by module name from the repository root rather than by discovery
    from tests.showcase_parity import norm, section, md_rows, page_table, page_list


def plan_section_4() -> str:
    return section(PLAN, "\n## 4. P0", "\n## 5. ")


def plan_epics() -> dict[str, tuple[str, ...]]:
    return md_rows(plan_section_4(), r"P0\.\d{1,2}")


def plan_proof() -> list[str]:
    return [norm(line[2:]) for line in plan_section_4().splitlines() if line.startswith("- ")]


def flows_matrix() -> dict[str, tuple[str, ...]]:
    # every row but the header row, whose first cell is "Attempt"; the separator row is skipped by _md_rows
    return md_rows(section(FLOWS, "\n### Minimum negative proof matrix", "\n## 4. "), r"(?!Attempt$).+")


class TestCorpusIsPresent(unittest.TestCase):
    """Positive controls. Without these the comparisons below can pass over nothing."""

    def test_records_yield_their_tables(self) -> None:
        self.assertEqual(13, len(plan_epics()), "PLAN-001 section 4 no longer yields thirteen epics; re-derive this test")
        self.assertEqual(7, len(plan_proof()), "PLAN-001 section 4 no longer yields seven proof lines; re-derive this test")
        self.assertEqual(8, len(flows_matrix()), "FLOWS.md section 3 no longer yields eight matrix rows; re-derive this test")

    def test_page_parses(self) -> None:
        self.assertTrue(PAGE.is_file(), "landing/p0.html is missing")
        for table in ("epics", "matrix"):
            with self.subTest(table=table):
                self.assertGreaterEqual(len(page_table(PAGE, table)), 1)
        self.assertGreaterEqual(len(page_list(PAGE, "proof")), 1)


class TestParityWithTheRecords(unittest.TestCase):
    def test_epics_match_the_plan(self) -> None:
        self.assertEqual(plan_epics(), page_table(PAGE, "epics"), "the epic table disagrees with PLAN-001 section 4")

    def test_proof_matches_the_plan(self) -> None:
        self.assertEqual(plan_proof(), page_list(PAGE, "proof"), "the mandatory proof disagrees with PLAN-001 section 4")

    def test_matrix_matches_the_flows_record(self) -> None:
        self.assertEqual(flows_matrix(), page_table(PAGE, "matrix"), "the negative proof matrix disagrees with FLOWS.md section 3")


if __name__ == "__main__":
    unittest.main()
