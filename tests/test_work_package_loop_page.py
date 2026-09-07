#!/usr/bin/env python3
"""reference/work-package-loop.html is a rendering of PLAN-001 section 13.1, and must stay one.

The page carries one table: the roadmap's 24-step loop mapped onto the nine stages. It is read
row for row from PLAN-001 section 13.1 and compared with the page after the same normalisation
the phase-page test uses: tags and backticks stripped, whitespace collapsed, case folded. The
plan is the source; the page is a second rendering.

A second assertion holds the page's stage citations to the stage pages: `Build §03` must name a
section build.html displays under that number, read from `<div class="section-heading"><span>NN</span>`
as tests/test_catalogue_agrees_with_pages.py reads them. A citation that resolves may still be
the wrong section; the check is that the number exists.

Positive controls guard the parsers: the plan must yield exactly 24 rows numbered 01 to 24
whose stage column is one of the nine stage names or "Every stage", and the page must parse at
least one row. A row count of exactly 24 catches an extra or duplicated row.

Negative controls (run 2026-09-06 under WP-060, on in-memory copies):
  * Change step 12's stage on the page        -> test_rows_match_the_plan FAILS
  * Add a 25th row to the page                -> test_table_has_exactly_24_rows FAILS
  * Cite "Build §12" on the page              -> test_stage_citations_resolve FAILS

Text is normalised by showcase_parity.norm_markup (WP-110, #341), which four modules
carried a copy of. It is the STRICT sibling of norm(): it leaves Markdown emphasis and
links alone, because a record that emphasises or hyperlinks text the page does not is a
divergence this module exists to catch. Adopting norm() instead - the first attempt -
let eight such divergences through, and review measured every one.

Controls re-run 2026-09-07 under WP-110, because a refactor of a guard can leave every
test green while weakening what it catches:
  * step 12's stage changed on the page          -> test_rows_match_the_plan FAILS
  * the record's cell gains `**bold**` markers      -> caught
  * the record's cell becomes `[text](url)` where   -> caught
    the page says something else
The last two are review's, and they PASSED when this module briefly used norm() rather
than norm_markup(). That is why the strict sibling exists.

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import html as html_mod
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "reference" / "work-package-loop.html"
PLAN = ROOT / "docs" / "architecture" / "BIZTRUST-PLAN-001.md"
STAGES = ROOT / "stages"
STAGE_NAMES = ("Discover", "Define", "Architect", "Plan", "Build", "Assure", "Release", "Operate", "Learn")
SECTION_START, SECTION_END = "\n### 13.1 ", "\n## 14. "


try:
    from showcase_parity import norm_markup as _norm
except ModuleNotFoundError:  # invoked by module name from the repository root rather than by discovery
    from tests.showcase_parity import norm_markup as _norm


def plan_rows() -> dict[str, tuple[str, str, str]]:
    text = PLAN.read_text(encoding="utf-8").split(SECTION_START, 1)[1].split(SECTION_END, 1)[0]
    out: dict[str, tuple[str, str, str]] = {}
    for line in text.splitlines():
        m = re.match(r"^\|\s*(\d{2})\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$", line)
        if m:
            out[m.group(1)] = (_norm(m.group(2)), _norm(m.group(3)), _norm(m.group(4)))
    return out


def page_html() -> str:
    return PAGE.read_text(encoding="utf-8")


def page_table() -> str:
    m = re.search(r'<section id="mapping".*?<tbody>(.*?)</tbody>', page_html(), re.S)
    assert m, "the mapping table is missing from the page"
    return m.group(1)


def page_rows() -> dict[str, tuple[str, str, str]]:
    out: dict[str, tuple[str, str, str]] = {}
    for row in re.finditer(r"<tr><td><strong>(\d{2})</strong></td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>", page_table(), re.S):
        out[row.group(1)] = (_norm(row.group(2)), _norm(row.group(3)), _norm(row.group(4)))
    return out


def displayed_sections(stage: str) -> set[str]:
    html = (STAGES / f"{stage.lower()}.html").read_text(encoding="utf-8")
    return set(re.findall(r'<div class="section-heading"><span>(\d{2})</span>', html))


class TestCorpusIsPresent(unittest.TestCase):
    """Positive controls. Without these every assertion below can pass over nothing."""

    def test_plan_yields_24_rows_in_nine_stages(self) -> None:
        rows = plan_rows()
        self.assertEqual({f"{n:02d}" for n in range(1, 25)}, set(rows), "PLAN-001 section 13.1 no longer lists steps 01 to 24; re-derive this test")
        allowed = {s.lower() for s in STAGE_NAMES} | {"every stage"}
        for step, (_, stage, _) in rows.items():
            with self.subTest(step=step):
                self.assertIn(stage, allowed, f"step {step} names a stage that is not one of the nine")

    def test_page_parses(self) -> None:
        self.assertTrue(PAGE.is_file(), "reference/work-package-loop.html is missing")
        self.assertGreaterEqual(len(page_rows()), 1, "no rows parsed; the table shape changed or the parser is wrong")


class TestParityWithThePlan(unittest.TestCase):
    def test_rows_match_the_plan(self) -> None:
        self.assertEqual(plan_rows(), page_rows(), "the mapping table disagrees with PLAN-001 section 13.1")

    def test_table_has_exactly_24_rows(self) -> None:
        self.assertEqual(24, len(re.findall(r"<tr\b", page_table())), "the table does not have exactly 24 rows")


class TestStageCitationsResolve(unittest.TestCase):
    def test_stage_citations_resolve(self) -> None:
        text = html_mod.unescape(re.sub(r"<[^>]+>", " ", page_html()))
        problems = []
        for m in re.finditer(r"\b(" + "|".join(STAGE_NAMES) + r")\s+§(\d{2})((?:\s*(?:,|to)\s*§\d{2})*)", text):
            stage, first, rest = m.group(1), m.group(2), m.group(3)
            numbers = [first] + re.findall(r"§(\d{2})", rest)
            shown = displayed_sections(stage)
            for n in numbers:
                if n not in shown:
                    problems.append(f"{stage} §{n} names no displayed section on {stage.lower()}.html")
        self.assertEqual([], problems, "\n".join(problems))

    def test_every_stage_link_has_its_anchor(self) -> None:
        problems = []
        for href in re.findall(r'href="\.\./stages/([a-z]+)\.html#([a-z-]+)"', page_html()):
            stage, anchor = href
            html = (STAGES / f"{stage}.html").read_text(encoding="utf-8")
            if f'id="{anchor}"' not in html:
                problems.append(f"{stage}.html has no id {anchor}")
        self.assertEqual([], problems, "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
