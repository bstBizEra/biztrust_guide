#!/usr/bin/env python3
"""landing/p3.html projects BIZTRUST-PLAN-001 section 7 and the roadmap's section 7, and must keep projecting them.

Five things on the page are copied from records and held here: the ten-epic table (plan section 7,
cell for cell) and four lists from the roadmap's section 7, name for name and in order: the
environment ladder, the canonical pipeline, the incident loop and Gate E's evidence list. The
plain-words summaries, the local definitions restated and the gate paragraphs are the page's own
and are not held; their source lines say so.

Positive controls: the plan must yield ten epics; the roadmap six environments, eighteen pipeline
steps, eight incident steps and eighteen evidence items; the page at least one row and one item per
table and list.

Negative controls (run 2026-09-06 under WP-070, on in-memory copies):
  * Change P3G.1's capability on the page               -> test_epics_match_the_plan FAILS
  * Drop "Secret Scan" from the pipeline                 -> test_lists_match_the_roadmap[pipeline] FAILS
  * Swap "Runbooks" and "On-call/Escalation"             -> test_lists_match_the_roadmap[evidence] FAILS

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "landing" / "p3.html"
PLAN = ROOT / "docs" / "architecture" / "BIZTRUST-PLAN-001.md"
ROADMAP = ROOT / "docs" / "research" / "roadmap" / "BIZTRUST-ROADMAP-001-operator-draft.md"

try:
    from showcase_parity import section, md_rows, fenced_lines, page_table, page_list
except ModuleNotFoundError:  # invoked by module name from the repository root rather than by discovery
    from tests.showcase_parity import section, md_rows, fenced_lines, page_table, page_list


def plan_epics() -> dict[str, tuple[str, ...]]:
    return md_rows(section(PLAN, "\n## 7. P3", "\n## 8. "), r"P3[A-J]\.\d{1,2}")


def roadmap_lists() -> dict[str, list[str]]:
    return {
        "environments": fenced_lines(section(ROADMAP, "\n# P3A ", "\n# P3B ")),
        "pipeline": fenced_lines(section(ROADMAP, "\n# P3B ", "\n# P3C ")),
        "incident": fenced_lines(section(ROADMAP, "\n# P3J ", "\n# Gate E ")),
        "evidence": fenced_lines(section(ROADMAP, "\n# Gate E ", "\n# 8. ")),
    }


EXPECTED = {"environments": 6, "pipeline": 18, "incident": 8, "evidence": 18}


class TestCorpusIsPresent(unittest.TestCase):
    """Positive controls. Without these the comparisons below can pass over nothing."""

    def test_records_yield_their_tables(self) -> None:
        self.assertEqual(10, len(plan_epics()), "PLAN-001 section 7 no longer yields ten epics; re-derive this test")
        lists = roadmap_lists()
        for name, n in EXPECTED.items():
            with self.subTest(list=name):
                self.assertEqual(n, len(lists[name]), f"the roadmap's section 7 no longer yields {n} {name}; re-derive this test")

    def test_page_parses(self) -> None:
        self.assertTrue(PAGE.is_file(), "landing/p3.html is missing")
        self.assertGreaterEqual(len(page_table(PAGE, "epics")), 1)
        for name in EXPECTED:
            with self.subTest(list=name):
                self.assertGreaterEqual(len(page_list(PAGE, name)), 1)


class TestParityWithTheRecords(unittest.TestCase):
    def test_epics_match_the_plan(self) -> None:
        self.assertEqual(plan_epics(), page_table(PAGE, "epics"), "the epic table disagrees with PLAN-001 section 7")

    def test_lists_match_the_roadmap(self) -> None:
        lists = roadmap_lists()
        for name in EXPECTED:
            with self.subTest(list=name):
                self.assertEqual(lists[name], page_list(PAGE, name), f"the {name} list disagrees with the roadmap's section 7")


if __name__ == "__main__":
    unittest.main()
