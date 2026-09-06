#!/usr/bin/env python3
"""landing/roadmap.html projects PLAN-001 sections 2, 8 and 10.1, and must keep projecting them.

The page carries three tables copied cell for cell from the plan: the five phases (section 2),
the labels (section 10.1) and the expansion streams (section 8). Each is read from the plan and
compared with the page after the normalisation the plan-rendering tests share: tags and
backticks stripped, whitespace collapsed, case folded. The plan is the source; the page is a
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

import html as html_mod
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "landing" / "roadmap.html"
PLAN = ROOT / "docs" / "architecture" / "BIZTRUST-PLAN-001.md"


def _norm(fragment: str) -> str:
    s = re.sub(r"<[^>]+>", "", fragment)
    s = html_mod.unescape(s).replace("`", "").replace("**", "")
    return re.sub(r"\s+", " ", s).strip().lower()


def _plan_section(start: str, end: str) -> str:
    return PLAN.read_text(encoding="utf-8").split(start, 1)[1].split(end, 1)[0]


def _plan_rows(section: str, first_cell: str) -> dict[str, tuple[str, ...]]:
    """Rows of the section's table whose first cell matches -> {first: (rest...)}."""
    out: dict[str, tuple[str, ...]] = {}
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.strip().startswith("|") else []
        if len(cells) >= 2 and re.fullmatch(first_cell, cells[0]) and not re.fullmatch(r"-+", cells[1]):
            out[_norm(cells[0])] = tuple(_norm(c) for c in cells[1:])
    return out


def _page_rows(table_class: str) -> dict[str, tuple[str, ...]]:
    html = PAGE.read_text(encoding="utf-8")
    m = re.search(rf'<table class="{table_class}">.*?<tbody>(.*?)</tbody>', html, re.S)
    assert m, f"no table of class {table_class} on the page"
    out: dict[str, tuple[str, ...]] = {}
    for row in re.finditer(r"<tr>(.*?)</tr>", m.group(1), re.S):
        cells = [_norm(c) for c in re.findall(r"<td>(.*?)</td>", row.group(1), re.S)]
        out[cells[0]] = tuple(cells[1:])
    return out


def plan_phases() -> dict[str, tuple[str, ...]]:
    return _plan_rows(_plan_section("\n## 2. The five phases", "\n## 3. "), r"Architecture|P[0-3]")


def plan_labels() -> dict[str, tuple[str, ...]]:
    return _plan_rows(_plan_section("\n### 10.1 ", "\n### 10.2 "), r"[A-E]")


def plan_streams() -> dict[str, tuple[str, ...]]:
    rows = _plan_rows(_plan_section("\n## 8. Continuous Operations", "\n## 9. "), r"E[1-8] .+")
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
                self.assertGreaterEqual(len(_page_rows(table)), 1, f"no rows parsed from the {table} table")


class TestParityWithThePlan(unittest.TestCase):
    def test_phases_match_the_plan(self) -> None:
        self.assertEqual(plan_phases(), _page_rows("phases"), "the phases table disagrees with PLAN-001 section 2")

    def test_labels_match_the_plan(self) -> None:
        self.assertEqual(plan_labels(), _page_rows("labels"), "the labels table disagrees with PLAN-001 section 10.1")

    def test_streams_match_the_plan(self) -> None:
        self.assertEqual(plan_streams(), _page_rows("streams"), "the streams table disagrees with PLAN-001 section 8")


if __name__ == "__main__":
    unittest.main()
