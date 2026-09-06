#!/usr/bin/env python3
"""Every page under landing/ carries the shell landing/README.md prescribes, and must keep carrying it.

landing/README.md (SHOWCASE-001) is the record for the showcase: nine pages in a fixed order, a
shared shell (strip, mast with the wordmark, navigation, record line, sourced sections, footer),
and a shared stylesheet. This module holds the structural rules:

1. The navigation on every showcase page lists exactly the README's nine labels, in its order,
   each as a link to a file that exists under landing/ or as an unlinked label; a link to a page
   that has not landed is a broken promise the validator would also catch, but a label out of
   order or missing would not be.
2. Every page carries the strip, the wordmark and the shared stylesheet, and no tenant mark.
3. Every section of class "block" ends in a source line; every page but the overview carries a
   record line in the README's form.

Positive controls: the README must yield nine rows, and landing/ must hold at least the overview.

Negative controls (run 2026-09-06 under WP-064, on in-memory copies):
  * Reorder two labels in the overview's navigation  -> test_navigation_matches_the_record FAILS
  * Drop a section's source line on the overview     -> test_every_block_has_a_source_line FAILS
  * Add a UniTrust asset to the overview             -> test_no_tenant_mark FAILS

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import html as html_mod
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "landing"
RECORD = LANDING / "README.md"
RECORD_LINE = re.compile(r'<p class="record">Projects .+?, sections? .+?; read at [0-9a-f]{7}, \d{4}-\d{2}-\d{2}\.</p>')


def _norm(fragment: str) -> str:
    return re.sub(r"\s+", " ", html_mod.unescape(re.sub(r"<[^>]+>", "", fragment))).strip()


def record_pages() -> list[tuple[str, str]]:
    """The README's section 1 table -> [(label, file)], in order."""
    text = RECORD.read_text(encoding="utf-8").split("\n## 1. ", 1)[1].split("\n## 2. ", 1)[0]
    rows = []
    for line in text.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|", line)
        if m and m.group(1) != "Navigation label":
            rows.append((m.group(1), m.group(2)))
    return rows


def showcase_pages() -> list[Path]:
    return sorted(LANDING.glob("*.html"))


def navigation(html: str) -> list[tuple[str, str | None]]:
    """[(label, href or None)] in document order, from the nav the README prescribes."""
    m = re.search(r'<nav class="showcase-nav"[^>]*>(.*?)</nav>', html, re.S)
    assert m, "no showcase navigation on the page"
    out = []
    for item in re.finditer(r"<(a|span)\b([^>]*)>(.*?)</\1>", m.group(1), re.S):
        href = re.search(r'href="([^"]+)"', item.group(2))
        out.append((_norm(item.group(3)), href.group(1) if href else None))
    return out


class TestCorpusIsPresent(unittest.TestCase):
    """Positive controls. Without these the rules below can pass over nothing."""

    def test_record_yields_nine_pages(self) -> None:
        self.assertEqual(9, len(record_pages()), "landing/README.md section 1 no longer lists nine pages; re-derive this test with the record")

    def test_landing_holds_the_overview(self) -> None:
        self.assertIn(LANDING / "index.html", showcase_pages())


class TestTheShell(unittest.TestCase):
    def test_navigation_matches_the_record(self) -> None:
        expected = record_pages()
        for page in showcase_pages():
            with self.subTest(page=page.name):
                nav = navigation(page.read_text(encoding="utf-8"))
                self.assertEqual([label for label, _ in expected], [label for label, _ in nav], f"{page.name}: navigation labels differ from the record's order")
                for (label, file), (_, href) in zip(expected, nav):
                    if href is not None:
                        self.assertEqual(file, href, f"{page.name}: {label} links {href}, the record says {file}")
                        self.assertTrue((LANDING / href).is_file(), f"{page.name}: {label} links {href}, which does not exist")

    def test_strip_wordmark_and_stylesheet(self) -> None:
        for page in showcase_pages():
            with self.subTest(page=page.name):
                html = page.read_text(encoding="utf-8")
                self.assertIn('class="strip"', html, "no status strip")
                self.assertIn('class="wordmark"', html, "no wordmark")
                self.assertIn('href="showcase.css"', html, "the shared stylesheet is not linked")
                self.assertNotIn("<style>", html, "an inline style block; the tokens live in showcase.css")

    def test_no_tenant_mark(self) -> None:
        for page in showcase_pages():
            with self.subTest(page=page.name):
                self.assertNotRegex(page.read_text(encoding="utf-8"), r"(?i)unitrust\.(png|svg|jpg)|assets/unitrust", "a tenant mark on a showcase page")

    def test_every_block_has_a_source_line(self) -> None:
        for page in showcase_pages():
            with self.subTest(page=page.name):
                html = page.read_text(encoding="utf-8")
                problems = []
                for m in re.finditer(r'<section\b([^>]*)>(.*?)</section>', html, re.S):
                    attrs, body = m.group(1), m.group(2)
                    if 'class="block"' in attrs and 'class="source"' not in body:
                        ident = re.search(r'id="([^"]+)"', attrs)
                        problems.append(ident.group(1) if ident else "(a block with no id)")
                self.assertEqual([], problems, f"{page.name}: sections without a source line: {problems}")

    def test_record_line_on_every_projection(self) -> None:
        for page in showcase_pages():
            if page.name == "index.html":
                continue
            with self.subTest(page=page.name):
                self.assertRegex(page.read_text(encoding="utf-8"), RECORD_LINE, "no record line in the README's form")


if __name__ == "__main__":
    unittest.main()
