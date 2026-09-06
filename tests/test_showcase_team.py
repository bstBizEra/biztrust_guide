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

import html as html_mod
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "landing" / "team.html"
PLAN = ROOT / "docs" / "architecture" / "BIZTRUST-PLAN-001.md"
ROADMAP = ROOT / "docs" / "research" / "roadmap" / "BIZTRUST-ROADMAP-001-operator-draft.md"


def _norm(fragment: str) -> str:
    s = re.sub(r"<[^>]+>", "", fragment)
    s = html_mod.unescape(s).replace("`", "").replace("**", "")
    return re.sub(r"\s+", " ", s).strip().lower()


def _section(path: Path, start: str, end: str) -> str:
    return path.read_text(encoding="utf-8").split(start, 1)[1].split(end, 1)[0]


def _headed_table(section: str, header: str) -> dict[str, tuple[str, ...]]:
    """The rows of the table headed exactly `header`, read to the next blank line -> {first cell: rest}."""
    assert header in section, f"no table headed {header!r} in the section"
    body = section.split(header, 1)[1].split("\n\n", 1)[0]
    out: dict[str, tuple[str, ...]] = {}
    for line in body.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and not re.fullmatch(r"-+", cells[0]):
            out[_norm(cells[0])] = tuple(_norm(c) for c in cells[1:])
    return out


def _fenced_lines(section: str) -> list[str]:
    """The lines of the first ```text fence in the section: arrows stripped, joiner-only lines dropped."""
    fence = section.split("```text", 1)[1].split("```", 1)[0]
    lines = [line.strip().lstrip("→ ").strip() for line in fence.splitlines()]
    return [_norm(line) for line in lines if line and line not in ("↓", "+", "=")]


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
    assert m, f"no list of class copied {list_class} on the page"
    return [_norm(item) for item in re.findall(r"<li>(.*?)</li>", m.group(1), re.S)]


TABLES = {
    "seats": ("\n### 12.1 ", "\n## 13. ", "| Seat | Source | Records or accepts |"),
    "councils": ("\n### 12.1 ", "\n## 13. ", "| Roadmap (section 10) | Hub group | Kind |"),
    "done": ("\n## 13. Definition of Done", "\n### 13.1 ", "| Guide item | Roadmap items it carries |"),
}
EXPECTED_ROWS = {"seats": 9, "councils": 6, "done": 8}


def plan_table(name: str) -> dict[str, tuple[str, ...]]:
    start, end, header = TABLES[name]
    return _headed_table(_section(PLAN, start, end), header)


def roadmap_lists() -> dict[str, list[str]]:
    return {
        "bindings": _fenced_lines(_section(ROADMAP, "\n## H. Agentic Engineering Governance", "\n# 9. ")),
        "loop": _fenced_lines(_section(ROADMAP, "\n# 9. Canonical Agentic Engineering Loop", "\n# 10. ")),
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
                self.assertGreaterEqual(len(_page_table(name)), 1)
        for name in EXPECTED_ITEMS:
            with self.subTest(list=name):
                self.assertGreaterEqual(len(_page_list(name)), 1)


class TestParityWithTheRecords(unittest.TestCase):
    def test_tables_match_the_plan(self) -> None:
        for name in EXPECTED_ROWS:
            with self.subTest(table=name):
                self.assertEqual(plan_table(name), _page_table(name), f"the {name} table disagrees with PLAN-001")

    def test_lists_match_the_roadmap(self) -> None:
        lists = roadmap_lists()
        for name in EXPECTED_ITEMS:
            with self.subTest(list=name):
                self.assertEqual(lists[name], _page_list(name), f"the {name} list disagrees with the roadmap")


if __name__ == "__main__":
    unittest.main()
