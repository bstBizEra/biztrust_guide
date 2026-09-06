#!/usr/bin/env python3
"""landing/team.html projects BIZTRUST-PLAN-001 sections 12.1, 13 and 13.1 and the roadmap's sections 8H and 9, and must keep projecting them.

Five things on the page are copied from records and held here: the seats table, the councils
mapping and the Definition of Done reconciliation (plan sections 12.1 and 13, cell for cell, each
table located by its header row), the eight agent bindings (roadmap section 8H, name for name) and
the twenty-four-step loop (roadmap section 9, step for step). The three kinds in plain words, the
reading of the seats table, the four steps' paragraph and the doctrine restatement are the page's
own and are not held; their source lines say so.

Positive controls: the plan must yield nine seats, six council rows and eight Definition of Done
rows; the roadmap eight bindings and twenty-four steps; the page at least one row and one item per
table and list.

Negative controls (run 2026-09-06 under WP-072, on in-memory copies):
  * Rename the release authority's record on the page   -> test_tables_match_the_plan[seats] FAILS
  * Drop "Independent Review" from the bindings          -> test_lists_match_the_roadmap[bindings] FAILS
  * Swap steps 12 and 13 of the loop                     -> test_lists_match_the_roadmap[loop] FAILS

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest
from pathlib import Path
try:
    from showcase_parity import section, headed_table, fenced_lines, page_table, page_list
except ModuleNotFoundError:  # invoked by module name from the repository root rather than by discovery
    from tests.showcase_parity import section, headed_table, fenced_lines, page_table, page_list

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "landing" / "team.html"
PLAN = ROOT / "docs" / "architecture" / "BIZTRUST-PLAN-001.md"
ROADMAP = ROOT / "docs" / "research" / "roadmap" / "BIZTRUST-ROADMAP-001-operator-draft.md"

TABLES = {
    "seats": ("\n### 12.1 ", "\n## 13. ", "| Seat | Source | Records or accepts |"),
    "councils": ("\n### 12.1 ", "\n## 13. ", "| Roadmap (section 10) | Hub group | Kind |"),
    "done": ("\n## 13. Definition of Done", "\n### 13.1 ", "| Guide item | Roadmap items it carries |"),
}
EXPECTED_ROWS = {"seats": 9, "councils": 6, "done": 8}


def plan_table(name: str) -> dict[str, tuple[str, ...]]:
    start, end, header = TABLES[name]
    return headed_table(section(PLAN, start, end), header)


def roadmap_lists() -> dict[str, list[str]]:
    return {
        "bindings": fenced_lines(section(ROADMAP, "\n## H. Agentic Engineering Governance", "\n# 9. ")),
        "loop": fenced_lines(section(ROADMAP, "\n# 9. Canonical Agentic Engineering Loop", "\n# 10. ")),
    }


EXPECTED_ITEMS = {"bindings": 8, "loop": 24}


class TestCorpusIsPresent(unittest.TestCase):
    """Positive controls. Without these the comparisons below can pass over nothing."""

    def test_records_yield_their_tables(self) -> None:
        for name, n in EXPECTED_ROWS.items():
            with self.subTest(table=name):
                self.assertEqual(n, len(plan_table(name)), f"PLAN-001 no longer yields {n} {name} rows; re-derive this test")
        lists = roadmap_lists()
        for name, n in EXPECTED_ITEMS.items():
            with self.subTest(list=name):
                self.assertEqual(n, len(lists[name]), f"the roadmap no longer yields {n} {name}; re-derive this test")

    def test_page_parses(self) -> None:
        self.assertTrue(PAGE.is_file(), "landing/team.html is missing")
        for name in EXPECTED_ROWS:
            with self.subTest(table=name):
                self.assertGreaterEqual(len(page_table(PAGE, name)), 1)
        for name in EXPECTED_ITEMS:
            with self.subTest(list=name):
                self.assertGreaterEqual(len(page_list(PAGE, name)), 1)


class TestParityWithTheRecords(unittest.TestCase):
    def test_tables_match_the_plan(self) -> None:
        for name in EXPECTED_ROWS:
            with self.subTest(table=name):
                self.assertEqual(plan_table(name), page_table(PAGE, name), f"the {name} table disagrees with PLAN-001")

    def test_lists_match_the_roadmap(self) -> None:
        lists = roadmap_lists()
        for name in EXPECTED_ITEMS:
            with self.subTest(list=name):
                self.assertEqual(lists[name], page_list(PAGE, name), f"the {name} list disagrees with the roadmap")


if __name__ == "__main__":
    unittest.main()
