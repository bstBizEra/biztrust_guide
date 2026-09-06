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

import html as html_mod
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "landing" / "p0.html"
PLAN = ROOT / "docs" / "architecture" / "BIZTRUST-PLAN-001.md"
FLOWS = ROOT / "docs" / "architecture" / "FLOWS.md"


def _norm(fragment: str) -> str:
    s = re.sub(r"<[^>]+>", "", fragment)
    s = html_mod.unescape(s).replace("`", "").replace("**", "")
    return re.sub(r"\s+", " ", s).strip().lower()


def _section(path: Path, start: str, end: str) -> str:
    return path.read_text(encoding="utf-8").split(start, 1)[1].split(end, 1)[0]


def _md_rows(section: str, first_cell_pattern: str) -> dict[str, tuple[str, ...]]:
    out: dict[str, tuple[str, ...]] = {}
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and re.fullmatch(first_cell_pattern, cells[0]) and not re.fullmatch(r"-+", cells[1]):
            out[_norm(cells[0])] = tuple(_norm(c) for c in cells[1:])
    return out


def _page_table(table_class: str) -> dict[str, tuple[str, ...]]:
    m = re.search(rf'<table class="{table_class}">.*?<tbody>(.*?)</tbody>', PAGE.read_text(encoding="utf-8"), re.S)
    assert m, f"no table of class {table_class} on the page"
    out: dict[str, tuple[str, ...]] = {}
    for row in re.finditer(r"<tr>(.*?)</tr>", m.group(1), re.S):
        cells = [_norm(c) for c in re.findall(r"<td>(.*?)</td>", row.group(1), re.S)]
        assert cells, f"a row of the {table_class} table has no cells"
        out[cells[0]] = tuple(cells[1:])
    return out


def _page_list(list_class: str) -> list[str]:
    m = re.search(rf'<ol class="copied {list_class}">(.*?)</ol>', PAGE.read_text(encoding="utf-8"), re.S)
    assert m, f"no list of class {list_class} on the page"
    return [_norm(item) for item in re.findall(r"<li>(.*?)</li>", m.group(1), re.S)]


def plan_section_4() -> str:
    return _section(PLAN, "\n## 4. P0", "\n## 5. ")


def plan_epics() -> dict[str, tuple[str, ...]]:
    return _md_rows(plan_section_4(), r"P0\.\d{1,2}")


def plan_proof() -> list[str]:
    return [_norm(line[2:]) for line in plan_section_4().splitlines() if line.startswith("- ")]


def flows_matrix() -> dict[str, tuple[str, ...]]:
    # every row but the header row, whose first cell is "Attempt"; the separator row is skipped by _md_rows
    return _md_rows(_section(FLOWS, "\n### Minimum negative proof matrix", "\n## 4. "), r"(?!Attempt$).+")


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
                self.assertGreaterEqual(len(_page_table(table)), 1)
        self.assertGreaterEqual(len(_page_list("proof")), 1)


class TestParityWithTheRecords(unittest.TestCase):
    def test_epics_match_the_plan(self) -> None:
        self.assertEqual(plan_epics(), _page_table("epics"), "the epic table disagrees with PLAN-001 section 4")

    def test_proof_matches_the_plan(self) -> None:
        self.assertEqual(plan_proof(), _page_list("proof"), "the mandatory proof disagrees with PLAN-001 section 4")

    def test_matrix_matches_the_flows_record(self) -> None:
        self.assertEqual(flows_matrix(), _page_table("matrix"), "the negative proof matrix disagrees with FLOWS.md section 3")


if __name__ == "__main__":
    unittest.main()
