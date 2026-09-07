#!/usr/bin/env python3
"""Every design under docs/architecture/p0/ obeys the pack's template, docs/architecture/p0/README.md.

The pack's README (WP-046) fixes the file naming, the status vocabulary and nine mandatory sections
in a fixed order. This test reads those rules from the README itself, then holds every P0.NN-*.md
and P0.SECURITY-PROOF.md to them: the nine headings present and in order, a status block with the
contents README 4.1 names, a status from the vocabulary that no agent may set to ACCEPTED, no sentence of the
form "we use X" (a design names candidates, never choices), a link from the P0 manual's epic row
to every design that has reached PROPOSED, as the README's section 6 requires, and the manual's
stated status agreeing with the design's own.

Positive controls: the README must yield nine mandatory headings and six status words; at least one
design must exist once the first has landed (before that the design tests skip, not pass).

Negative controls (run 2026-09-06 under WP-073, on in-memory copies of P0.12):
  * Remove the "Evidence contract" heading             -> test_mandatory_sections_in_order FAILS
  * Set the status to ACCEPTED                          -> test_status_is_proposable FAILS
  * Write "we use OpenBao" in the candidates section    -> test_no_technology_is_chosen FAILS
  * Drop the manual's link to the design                -> test_manual_links_each_landed_design FAILS

Negative controls added 2026-09-07 under WP-104, on in-memory copies:
  * Set one design to DRAFT, so the link rule skips it   -> test_manual_links_each_landed_design FAILS
  * Leave one manual row at PROPOSED after the move      -> test_the_manual_states_each_design_status FAILS

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "docs" / "architecture" / "p0"

# Every status a design on main may hold. README section 3: "A `DRAFT` lives on its
# branch; a design lands on `main` only at `PROPOSED`."
LANDED_STATUSES = ("PROPOSED", "IN_REVIEW", "ACCEPTED", "REJECTED", "SUPERSEDED")
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
                block = text.split("## Status block", 1)[1].split("\n## ", 1)[0].lower()
                for keyword in ("version", "epic", "ticket", "work package", "adr", "research"):
                    self.assertIn(keyword, block, f"{p.name}: the status block does not mention {keyword!r} (README 4.1)")

    def test_no_technology_is_chosen(self) -> None:
        for p in designs():
            with self.subTest(design=p.name):
                text = p.read_text(encoding="utf-8")
                self.assertIsNone(re.search(r"\bwe (use|chose|choose|will use|are using)\b", text, re.I), f"{p.name}: a design names candidates, never choices")
                controls = text.split("## Negative controls", 1)[1].split("\n## ", 1)[0]
                self.assertGreaterEqual(len([l for l in controls.splitlines() if l.startswith("| ") and not l.startswith("| #") and not l.startswith("|---")]), 1, f"{p.name}: no negative control row (README 4.5)")

    def test_manual_links_each_landed_design(self) -> None:
        """The manual links every design that has reached PROPOSED, whatever it has reached since.

        This was written as "each design at PROPOSED, skip the rest", which is only safe while
        no design has moved on. WP-104 moved all thirteen to IN_REVIEW at once, and the old
        form would have iterated over nothing and passed. The README's section 6 rule is that
        the link appears when a design REACHES PROPOSED; reaching it and moving on does not
        withdraw the link, so the statuses at or past it are the ones that must be linked.
        """
        manual = MANUAL.read_text(encoding="utf-8")
        linked = 0
        for p in designs():
            status = status_field(p.read_text(encoding="utf-8"), "Status").strip("`")
            if status not in LANDED_STATUSES:
                continue
            with self.subTest(design=p.name):
                self.assertIn(DESIGN_URL + p.name, manual, f"the P0 manual does not link {p.name}")
                linked += 1
        self.assertEqual(len(designs()), linked, "a design in the pack is at a status the manual need not link")

    def test_the_manual_states_each_design_status(self) -> None:
        """The manual copies each design's status, so the two must agree.

        Numbers and names on a page are the record's, never the page's own. Twelve epic rows
        carried "(design, PROPOSED)" while the designs said PROPOSED; nothing made them move
        together, and nothing would have said so.
        """
        manual = MANUAL.read_text(encoding="utf-8")
        stated = set(re.findall(r"\(design, ([A-Z_]+)\)", manual))
        self.assertNotEqual(set(), stated, "the manual states no design status; this check reads nothing")
        actual = {
            status_field(p.read_text(encoding="utf-8"), "Status").strip("`")
            for p in designs()
        }
        self.assertEqual(actual, stated, "the manual's stated status is not the designs' own")


if __name__ == "__main__":
    unittest.main()
