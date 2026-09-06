#!/usr/bin/env python3
"""Every design under docs/architecture/p0/ obeys the pack's template, docs/architecture/p0/README.md.

The pack's README (WP-046) fixes the file naming, the status vocabulary and nine mandatory sections
in a fixed order. This test reads those rules from the README itself, then holds every P0.NN-*.md
and P0.SECURITY-PROOF.md to them: the nine headings present and in order, a status block with the
required fields, a status from the vocabulary that no agent may set to ACCEPTED, no sentence of the
form "we use X" (a design names candidates, never choices), and, for a design at PROPOSED, a link
from the P0 manual's epic row to the design on GitHub, as the README's section 6 requires.

Positive controls: the README must yield nine mandatory headings and six status words; at least one
design must exist once the first has landed (before that the design tests skip, not pass).

Negative controls (run 2026-09-06 under WP-073, on in-memory copies of P0.12):
  * Remove the "Evidence contract" heading             -> test_mandatory_sections_in_order FAILS
  * Set the status to ACCEPTED                          -> test_status_is_proposable FAILS
  * Write "we use OpenBao" in the candidates section    -> test_no_technology_is_chosen FAILS
  * Drop the manual's link to the design                -> test_manual_links_each_proposed_design FAILS

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "docs" / "architecture" / "p0"
README = PACK / "README.md"
MANUAL = ROOT / "phases" / "p0.html"
DESIGN_URL = "https://github.com/bstBizEra/biztrust_guide/blob/main/docs/architecture/p0/"


def readme_headings() -> list[str]:
    """The nine mandatory section titles, read from the README's '### 4.n Title' headings."""
    return re.findall(r"^### 4\.\d+ (.+)$", README.read_text(encoding="utf-8"), re.M)


def readme_statuses() -> list[str]:
    block = README.read_text(encoding="utf-8").split("## 3. Status vocabulary", 1)[1].split("```", 2)[1]
    return re.findall(r"^([A-Z_]+)\s", block, re.M)


def designs() -> list[Path]:
    return sorted(p for p in PACK.glob("P0.*.md"))


def design_headings(text: str) -> list[str]:
    return re.findall(r"^## (.+)$", text, re.M)


def status_field(text: str, field: str) -> str:
    m = re.search(rf"^\| {re.escape(field)} \| (.+?) \|$", text, re.M)
    assert m, f"no status-block row for {field!r}"
    return m.group(1).strip()


class TestTemplateIsPresent(unittest.TestCase):
    def test_readme_yields_the_rules(self) -> None:
        self.assertEqual(9, len(readme_headings()), "the pack README no longer lists nine mandatory sections; re-derive this test")
        self.assertEqual(["DRAFT", "PROPOSED", "IN_REVIEW", "ACCEPTED", "REJECTED", "SUPERSEDED"], readme_statuses())

    def test_a_design_exists(self) -> None:
        self.assertGreaterEqual(len(designs()), 1, "no design has landed under docs/architecture/p0/")


class TestEveryDesignObeysTheTemplate(unittest.TestCase):
    def test_file_names(self) -> None:
        for p in designs():
            with self.subTest(design=p.name):
                self.assertRegex(p.name, r"^P0\.(\d{2}-[a-z0-9]+(-[a-z0-9]+){0,3}|SECURITY-PROOF)\.md$")

    def test_mandatory_sections_in_order(self) -> None:
        required = readme_headings()
        for p in designs():
            with self.subTest(design=p.name):
                found = [h for h in design_headings(p.read_text(encoding="utf-8")) if h in required]
                self.assertEqual(required, found, f"{p.name}: mandatory sections missing or out of order")

    def test_status_is_proposable(self) -> None:
        for p in designs():
            with self.subTest(design=p.name):
                text = p.read_text(encoding="utf-8")
                status = status_field(text, "Status").strip("`")
                self.assertIn(status, readme_statuses())
                self.assertNotEqual("ACCEPTED", status, f"{p.name}: no agent marks a design ACCEPTED")
                self.assertNotEqual("DRAFT", status, f"{p.name}: a DRAFT lives on its branch, not on main")
                for field in ("Version", "Epic", "Map ticket", "Landed by", "ADRs this design depends on", "Research cited"):
                    status_field(text, field)

    def test_no_technology_is_chosen(self) -> None:
        for p in designs():
            with self.subTest(design=p.name):
                text = p.read_text(encoding="utf-8")
                self.assertIsNone(re.search(r"\bwe (use|chose|choose|will use|are using)\b", text, re.I), f"{p.name}: a design names candidates, never choices")
                self.assertRegex(text, r"\bnegative control", f"{p.name}: no negative control")

    def test_manual_links_each_proposed_design(self) -> None:
        manual = MANUAL.read_text(encoding="utf-8")
        for p in designs():
            if status_field(p.read_text(encoding="utf-8"), "Status").strip("`") != "PROPOSED":
                continue
            with self.subTest(design=p.name):
                self.assertIn(DESIGN_URL + p.name, manual, f"the P0 manual does not link {p.name}")


if __name__ == "__main__":
    unittest.main()
