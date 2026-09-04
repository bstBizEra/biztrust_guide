#!/usr/bin/env python3
"""The artifact catalogue and the stage pages agree, mechanically.

reference/artifact-catalogue.html said of itself, in its method note: "Nothing is
checked mechanically. No test asserts that a stage page and this table still agree,
so a stage that gains an artifact will silently fall out of step." Measured cost of
that, September 2026: WP-033 and WP-037 each renumbered every `Operate §NN` / `Plan
§NN` citation by hand and verified by grep, because the link checker counts anchors
and not section numbers; WP-037's review found a catalogue row note the package
itself had made false; and the catalogue's own "two artifacts the lifecycle never
mentions" is a finding a test would have produced. Issue #77.

TWO ASSERTIONS
==============

1. Every section-number citation in the catalogue resolves. A citation is
   `<Stage> §NN` anywhere in the file, or a bare `§NN` inside a stage's block of
   rows (the italic notes say "Named in §09"). The stage page must carry a section
   whose displayed heading number is NN. Displayed numbers live in
   `<div class="section-heading"><span>NN</span>`; the page intro's stage number
   (`<span>04</span>` on plan.html) is excluded because its heading is the stage
   name, not a numbered section.

2. Every stage's outputs section names the same artifacts as the catalogue's block
   for that stage, as sets. Names are read by shape, because the nine pages use
   three: a table (`<tr><td><strong>NAME`), a definition list (`<div><span>NAME`),
   or - Assure only - a single artifact whose FIELDS are the definition list, so
   the artifact is the section's own heading. The shape per page is declared in
   SHAPE, not inferred, so a page that changes shape fails loudly here rather than
   reporting an empty set that agrees with nothing.

WHAT IS NOT CHECKED
===================

Semantics. A citation that resolves to a section with the right number may still
point at the wrong section if the page renumbers and the catalogue follows by
accident; the check is that the number exists, not that it means what the row
means. Row notes, formats, owners and accepters are prose and stay unchecked.

Negative controls mutate in-memory copies; nothing here writes to the tree.

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import html
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "reference" / "artifact-catalogue.html"
STAGES = ROOT / "stages"

# Page -> how its outputs section names artifacts.
SHAPE = {
    "discover": "table", "define": "table", "architect": "table", "plan": "table",
    "build": "table", "assure": "heading", "release": "deflist", "operate": "table", "learn": "table",
}
OUTPUTS_EYEBROWS = ("outputs", "what is produced")

_SECTION = re.compile(r"<section\b([^>]*)>(.*?)</section>", re.S)
_HEADING = re.compile(r'<div class="section-heading">\s*<span>(\d\d)</span>\s*<div>\s*<p>(.*?)</p>\s*<h2>(.*?)</h2>', re.S)
_STAGE_BREAK = re.compile(r'<tr class="stage-break"><td colspan="7">([A-Z][a-z]+)')


def text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def page_sections(page_html: str) -> list[dict]:
    out = []
    for attrs, body in _SECTION.findall(page_html):
        m = _HEADING.search(body)
        if not m:
            continue
        out.append({"number": m.group(1), "eyebrow": text(m.group(2)).lower(), "h2": text(m.group(3)), "body": body})
    return out


def page_numbers(page_html: str) -> set[str]:
    return {s["number"] for s in page_sections(page_html)}


def page_artifacts(stage: str, page_html: str) -> set[str]:
    shape = SHAPE[stage]
    outputs = [s for s in page_sections(page_html) if s["eyebrow"] in OUTPUTS_EYEBROWS]
    if len(outputs) != 1:
        raise AssertionError(f"{stage}.html: expected one outputs section, found {len(outputs)}")
    sec = outputs[0]
    if shape == "table":
        names = re.findall(r"<tr><td><strong>(.*?)</strong>", sec["body"])
    elif shape == "deflist":
        names = re.findall(r"<div><span>(.*?)</span>", sec["body"])
    elif shape == "heading":
        names = [sec["h2"]]
    else:
        raise AssertionError(shape)
    if not names:
        raise AssertionError(f"{stage}.html: outputs section yielded no names under shape {shape!r}")
    return {text(n) for n in names}


def catalogue_blocks(cat_html: str) -> dict[str, str]:
    """Stage name -> the HTML of its block of rows."""
    parts = _STAGE_BREAK.split(cat_html)
    # parts = [preamble, Stage1, body1, Stage2, body2, ...]
    blocks = {}
    for i in range(1, len(parts) - 1, 2):
        stage, body = parts[i], parts[i + 1]
        end = body.find("</tbody>")
        blocks[stage] = body if end < 0 else body[:end]
    return blocks


def catalogue_artifacts(cat_html: str) -> dict[str, set[str]]:
    out = {}
    for stage, body in catalogue_blocks(cat_html).items():
        rows = re.findall(r"<tr><td><small>%s</small></td><td><strong>(.*?)</strong>" % stage, body)
        out[stage] = {text(r) for r in rows}
    return out


def citations(cat_html: str) -> set[tuple[str, str]]:
    """(Stage, NN) pairs: explicit `Stage §NN` anywhere, and bare `§NN` inside a stage's block."""
    found = set(re.findall(r"([A-Z][a-z]+) §(\d\d)", cat_html))
    for stage, body in catalogue_blocks(cat_html).items():
        for n in re.findall(r"(?<![A-Za-z] )§(\d\d)", body):
            found.add((stage, n))
    return found


def resolve(cat_html: str, pages: dict[str, str]) -> list[str]:
    """Every citation that names a section number the page does not display."""
    problems = []
    for stage, n in sorted(citations(cat_html)):
        page = pages.get(stage.lower())
        if page is None:
            problems.append(f"{stage} §{n}: no page stages/{stage.lower()}.html")
        elif n not in page_numbers(page):
            problems.append(f"{stage} §{n}: {stage.lower()}.html displays sections {sorted(page_numbers(page))}")
    return problems


def disagreements(cat_html: str, pages: dict[str, str]) -> list[str]:
    problems = []
    cat = catalogue_artifacts(cat_html)
    for stage in sorted(SHAPE):
        page_names = page_artifacts(stage, pages[stage])
        cat_names = cat.get(stage.capitalize(), set())
        only_cat = sorted(cat_names - page_names)
        only_page = sorted(page_names - cat_names)
        if only_cat or only_page:
            problems.append(f"{stage}: only in catalogue {only_cat}; only on page {only_page}")
    return problems


class Corpus:
    """Mixin, not a TestCase: a base class with tests runs them once per subclass."""

    def setUp(self) -> None:
        self.cat = CATALOGUE.read_text(encoding="utf-8")
        self.pages = {p.stem: p.read_text(encoding="utf-8") for p in sorted(STAGES.glob("*.html"))}


class TestCorpusIsPresent(Corpus, unittest.TestCase):
    def test_corpus_is_present(self) -> None:
        """Without this, an emptied catalogue or a renamed stages/ passes everything below."""
        self.assertEqual(sorted(SHAPE), sorted(self.pages), "SHAPE must name every stage page and nothing else")
        # Distinct (stage, number) pairs; the catalogue cites ten or more distinct sections.
        self.assertGreaterEqual(len(citations(self.cat)), 10, "fewer distinct citations than the catalogue is known to carry; the parser broke")
        self.assertEqual(sorted(catalogue_blocks(self.cat)), sorted(s.capitalize() for s in SHAPE))


class TestCitationsResolve(Corpus, unittest.TestCase):
    def test_every_citation_names_a_displayed_section(self) -> None:
        problems = resolve(self.cat, self.pages)
        self.assertEqual([], problems, "catalogue citations that no section number backs:\n  " + "\n  ".join(problems))

    def test_check_can_fail(self) -> None:
        """Renumber one Operate section in a copy; the Operate §11 citations must break."""
        mutated = dict(self.pages)
        heading = '<div class="section-heading"><span>11</span>'
        self.assertIn(heading, mutated["operate"], "the control needs Operate's section 11 heading to exist")
        mutated["operate"] = mutated["operate"].replace(heading, '<div class="section-heading"><span>99</span>', 1)
        self.assertTrue(any(p.startswith("Operate §11") for p in resolve(self.cat, mutated)))
        # And a citation the catalogue invents must break too.
        self.assertTrue(any("Plan §42" in p for p in resolve(self.cat + " Plan §42", self.pages)))


class TestOutputsAgree(Corpus, unittest.TestCase):
    def test_every_outputs_section_matches_its_catalogue_block(self) -> None:
        problems = disagreements(self.cat, self.pages)
        self.assertEqual([], problems, "a stage page and the catalogue name different artifacts:\n  " + "\n  ".join(problems))

    def test_check_can_fail(self) -> None:
        """Add a row to a page copy, then remove one from a catalogue copy; both must be reported."""
        mutated = dict(self.pages)
        mutated["build"] = mutated["build"].replace("<tr><td><strong>Tests</strong>", "<tr><td><strong>Wishes</strong>", 1)
        found = disagreements(self.cat, mutated)
        self.assertTrue(any("build:" in p and "Wishes" in p and "Tests" in p for p in found), found)
        cat = self.cat.replace("<tr><td><small>Learn</small></td><td><strong>Control change set</strong>",
                               "<tr><td><small>Learn</small></td><td><strong>Control change list</strong>", 1)
        found = disagreements(cat, self.pages)
        self.assertTrue(any("learn:" in p and "Control change set" in p for p in found), found)

    def test_shape_declaration_is_load_bearing(self) -> None:
        """Reading Assure or Release by the table shape yields nothing; the declaration is what makes
        the check see them, and an empty set here must raise rather than agree vacuously."""
        for stage in ("assure", "release"):
            with self.subTest(stage=stage):
                saved = SHAPE[stage]
                SHAPE[stage] = "table"
                try:
                    with self.assertRaises(AssertionError):
                        page_artifacts(stage, self.pages[stage])
                finally:
                    SHAPE[stage] = saved


if __name__ == "__main__":
    unittest.main(verbosity=2)
