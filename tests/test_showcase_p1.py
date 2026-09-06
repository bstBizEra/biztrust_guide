#!/usr/bin/env python3
"""landing/p1.html projects BIZTRUST-PLAN-001 section 5 and the roadmap's section 5, and must keep projecting them.

Five things on the page are copied from records and held here: the three epic tables (plan
sections 5.1 to 5.3, cell for cell), the twelve-step vertical slice (plan section 5.5, node for
node from its flowchart), and the two operating-model chains (the roadmap's section 5, step for
step). The boundaries' glosses, the plain-words rules, the surfaces and the gate conditions are the
page's own restatements and are not held; their source lines say so.

Positive controls: the plan must yield fourteen, ten and eight epics and twelve slice steps, the
roadmap five and nine chain steps, and the page at least one row per table and one item per list.

Negative controls (run 2026-09-06 under WP-068, on in-memory copies):
  * Change P1A.6's capability on the page               -> test_epics_match_the_plan FAILS
  * Swap "Request bind" and "Record client acceptance"  -> test_slice_matches_the_plan FAILS
  * Drop "Broker Advice" from the professional chain    -> test_models_match_the_roadmap FAILS

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
try:
    from showcase_parity import norm, section, md_rows, fenced_lines, page_table, page_list
except ModuleNotFoundError:  # invoked by module name from the repository root rather than by discovery
    from tests.showcase_parity import norm, section, md_rows, fenced_lines, page_table, page_list

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "landing" / "p1.html"
PLAN = ROOT / "docs" / "architecture" / "BIZTRUST-PLAN-001.md"
ROADMAP = ROOT / "docs" / "research" / "roadmap" / "BIZTRUST-ROADMAP-001-operator-draft.md"

SUBPHASES = {"p1a": ("\n### 5.1 ", "\n### 5.2 ", r"P1A\.\d{1,2}"),
             "p1b": ("\n### 5.2 ", "\n### 5.3 ", r"P1B\.\d{1,2}"),
             "p1c": ("\n### 5.3 ", "\n### 5.4 ", r"P1C\.\d{1,2}")}


def plan_epics(sub: str) -> dict[str, tuple[str, ...]]:
    start, end, pattern = SUBPHASES[sub]
    return md_rows(section(PLAN, start, end), pattern)


def plan_slice() -> list[str]:
    flow = section(PLAN, "\n### 5.5 ", "\n## 6. ").split("```mermaid", 1)[1].split("```", 1)[0]
    return [norm(node) for node in re.findall(r"\[([^\]]+)\]", flow)]


def roadmap_models() -> dict[str, list[str]]:
    p1c = section(ROADMAP, "\n# P1C ", "\n# P1 package recommendation engine")
    return {"professional": fenced_lines(p1c.split("### Professional brokerage", 1)[1]),
            "straight": fenced_lines(p1c.split("### Straight-through digital insurance", 1)[1])}


class TestCorpusIsPresent(unittest.TestCase):
    """Positive controls. Without these the comparisons below can pass over nothing."""

    def test_records_yield_their_tables(self) -> None:
        for sub, n in (("p1a", 14), ("p1b", 10), ("p1c", 8)):
            with self.subTest(sub=sub):
                self.assertEqual(n, len(plan_epics(sub)), f"PLAN-001 section 5 no longer yields {n} {sub.upper()} epics; re-derive this test")
        self.assertEqual(12, len(plan_slice()), "PLAN-001 section 5.5 no longer yields twelve slice steps; re-derive this test")
        models = roadmap_models()
        self.assertEqual(5, len(models["professional"]), "the roadmap's professional chain no longer yields five steps; re-derive this test")
        self.assertEqual(9, len(models["straight"]), "the roadmap's straight-through chain no longer yields nine steps; re-derive this test")

    def test_page_parses(self) -> None:
        self.assertTrue(PAGE.is_file(), "landing/p1.html is missing")
        for table in SUBPHASES:
            with self.subTest(table=table):
                self.assertGreaterEqual(len(page_table(PAGE, table)), 1)
        for lst in ("slice", "professional", "straight"):
            with self.subTest(list=lst):
                self.assertGreaterEqual(len(page_list(PAGE, lst)), 1)


class TestParityWithTheRecords(unittest.TestCase):
    def test_epics_match_the_plan(self) -> None:
        for sub in SUBPHASES:
            with self.subTest(sub=sub):
                self.assertEqual(plan_epics(sub), page_table(PAGE, sub), f"the {sub.upper()} table disagrees with PLAN-001 section 5")

    def test_slice_matches_the_plan(self) -> None:
        self.assertEqual(plan_slice(), page_list(PAGE, "slice"), "the vertical slice disagrees with PLAN-001 section 5.5")

    def test_models_match_the_roadmap(self) -> None:
        models = roadmap_models()
        for name in ("professional", "straight"):
            with self.subTest(model=name):
                self.assertEqual(models[name], page_list(PAGE, name), f"the {name} chain disagrees with the roadmap's section 5")


if __name__ == "__main__":
    unittest.main()
