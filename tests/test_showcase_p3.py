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

import html as html_mod
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "landing" / "p3.html"
PLAN = ROOT / "docs" / "architecture" / "BIZTRUST-PLAN-001.md"
ROADMAP = ROOT / "docs" / "research" / "roadmap" / "BIZTRUST-ROADMAP-001-operator-draft.md"


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


def _fenced_lines(section: str) -> list[str]:
    """The lines of the first ```text fence in the section: arrows stripped, arrow-only lines dropped."""
    fence = section.split("```text", 1)[1].split("```", 1)[0]
    lines = [line.strip().lstrip("→ ").strip() for line in fence.splitlines()]
    return [_norm(line) for line in lines if line and line not in ("↓", "↕", "│", "▼")]


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


def plan_epics() -> dict[str, tuple[str, ...]]:
    return _md_rows(_section(PLAN, "\n## 7. P3", "\n## 8. "), r"P3[A-J]\.\d{1,2}")


def roadmap_lists() -> dict[str, list[str]]:
    return {
        "environments": _fenced_lines(_section(ROADMAP, "\n# P3A ", "\n# P3B ")),
        "pipeline": _fenced_lines(_section(ROADMAP, "\n# P3B ", "\n# P3C ")),
        "incident": _fenced_lines(_section(ROADMAP, "\n# P3J ", "\n# Gate E ")),
        "evidence": _fenced_lines(_section(ROADMAP, "\n# Gate E ", "\n# 8. ")),
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
        self.assertGreaterEqual(len(_page_table("epics")), 1)
        for name in EXPECTED:
            with self.subTest(list=name):
                self.assertGreaterEqual(len(_page_list(name)), 1)


class TestParityWithTheRecords(unittest.TestCase):
    def test_epics_match_the_plan(self) -> None:
        self.assertEqual(plan_epics(), _page_table("epics"), "the epic table disagrees with PLAN-001 section 7")

    def test_lists_match_the_roadmap(self) -> None:
        lists = roadmap_lists()
        for name in EXPECTED:
            with self.subTest(list=name):
                self.assertEqual(lists[name], _page_list(name), f"the {name} list disagrees with the roadmap's section 7")


if __name__ == "__main__":
    unittest.main()
