#!/usr/bin/env python3
"""landing/p2.html projects BIZTRUST-PLAN-001 section 6 and the roadmap's section 6, and must keep projecting them.

Six things on the page are copied from records and held here: the nine-epic table (plan section 6,
cell for cell) and five lists from the roadmap's section 6, name for name and in order: the core
rule's ten concepts, Gate D's trace, the settlement chain, the reconciliation statuses and Gate D's
failure cases. The plain-words paragraphs, the transaction-flow paraphrase, the safety sequence and
the gate conditions are the page's own restatements and are not held; their source lines say so.

Positive controls: the plan must yield nine epics; the roadmap ten concepts, eleven trace steps,
seven settlement steps, eight statuses and ten failure cases; the page at least one row and one item
per table and list.

Negative controls (run 2026-09-06 under WP-069, on in-memory copies):
  * Change P2B.1's capability on the page               -> test_epics_match_the_plan FAILS
  * Drop "Payment Allocation" from the concepts         -> test_lists_match_the_roadmap[concepts] FAILS
  * Swap "ledger mismatch" and "reconciliation mismatch" -> test_lists_match_the_roadmap[failures] FAILS

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "landing" / "p2.html"
PLAN = ROOT / "docs" / "architecture" / "BIZTRUST-PLAN-001.md"
ROADMAP = ROOT / "docs" / "research" / "roadmap" / "BIZTRUST-ROADMAP-001-operator-draft.md"

try:
    from showcase_parity import section, md_rows, fenced_lines, bullets, page_table, page_list
except ModuleNotFoundError:  # invoked by module name from the repository root rather than by discovery
    from tests.showcase_parity import section, md_rows, fenced_lines, bullets, page_table, page_list


def plan_epics() -> dict[str, tuple[str, ...]]:
    return md_rows(section(PLAN, "\n## 6. P2", "\n## 7. "), r"P2[A-F]\.\d{1,2}")


def roadmap_lists() -> dict[str, list[str]]:
    gate_d = section(ROADMAP, "\n# Gate D ", "\n# 7. ")
    return {
        "concepts": fenced_lines(section(ROADMAP, "\n## Core rule", "\n## P2 transaction flow")),
        "trace": fenced_lines(gate_d),
        "settlement": fenced_lines(section(ROADMAP, "\n# P2D ", "\n# P2E ")),
        "statuses": fenced_lines(section(ROADMAP, "\n# P2E ", "\n# P2F ").split("Statuses:", 1)[1]),
        "failures": bullets(gate_d),
    }


EXPECTED = {"concepts": 10, "trace": 11, "settlement": 7, "statuses": 8, "failures": 10}


class TestCorpusIsPresent(unittest.TestCase):
    """Positive controls. Without these the comparisons below can pass over nothing."""

    def test_records_yield_their_tables(self) -> None:
        self.assertEqual(9, len(plan_epics()), "PLAN-001 section 6 no longer yields nine epics; re-derive this test")
        lists = roadmap_lists()
        for name, n in EXPECTED.items():
            with self.subTest(list=name):
                self.assertEqual(n, len(lists[name]), f"the roadmap's section 6 no longer yields {n} {name}; re-derive this test")

    def test_page_parses(self) -> None:
        self.assertTrue(PAGE.is_file(), "landing/p2.html is missing")
        self.assertGreaterEqual(len(page_table(PAGE, "epics")), 1)
        for name in EXPECTED:
            with self.subTest(list=name):
                self.assertGreaterEqual(len(page_list(PAGE, name)), 1)


class TestParityWithTheRecords(unittest.TestCase):
    def test_epics_match_the_plan(self) -> None:
        self.assertEqual(plan_epics(), page_table(PAGE, "epics"), "the epic table disagrees with PLAN-001 section 6")

    def test_lists_match_the_roadmap(self) -> None:
        lists = roadmap_lists()
        for name in EXPECTED:
            with self.subTest(list=name):
                self.assertEqual(lists[name], page_list(PAGE, name), f"the {name} list disagrees with the roadmap's section 6")


if __name__ == "__main__":
    unittest.main()
