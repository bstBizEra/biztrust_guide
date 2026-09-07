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

Negative controls added 2026-09-07 under WP-104, on in-memory copies. The first three were
found by review, after a first version of the status check passed all of them:
  * Drop one row's status, leaving its link             -> ..._and_states_its_status FAILS
  * Mark one design REJECTED and write REJECTED on a    -> ..._and_states_its_status FAILS
    DIFFERENT design's row, so both sets stay equal
  * Swap two epic rows' design links                    -> test_the_epic_row_holds_its_own_design_link FAILS
  * Leave one manual row at the old status              -> ..._and_states_its_status FAILS
Two controls are deliberately not isolated, because what they break really does break more
than one rule, and claiming otherwise would be false precision:
  * Drop the manual's link to a design                  -> ..._and_states_its_status AND
                                                           test_the_epic_row_holds_its_own_design_link
  * Set one design to DRAFT                             -> test_every_landed_design_is_linked
                                                           and one more

WHAT THESE DO NOT DO. They read the manual's anchors, not its prose: a sentence elsewhere on
the page asserting a design's status is not seen. They do not check that an epic row's OTHER
cells describe the design it links. And the status the manual states is compared to the status
the design's block declares, not to anything that would show the declaration is true - the
review recorded on the design's map ticket is what section 3 rests IN_REVIEW on, and no test
reads a ticket.

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


def design_status(path: Path) -> str:
    """A design's status, from its status block, without the backticks the table writes."""
    return status_field(path.read_text(encoding="utf-8"), "Status").strip("`")


# Every status a design on main may hold: the README's own vocabulary less DRAFT, which
# section 3 keeps on a branch - "A `DRAFT` lives on its branch; a design lands on `main` only
# at `PROPOSED`." Derived rather than listed, so it cannot drift from the record it cites.
LANDED_STATUSES = tuple(s for s in readme_statuses() if s != "DRAFT")


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

    def test_the_manual_links_each_design_and_states_its_status(self) -> None:
        """Each design is linked, and the status beside THAT link is that design's own.

        Paired, not compared set-wise. A set comparison is vacuous while every design holds
        the same status - the state this was written in - and review found three mutations
        that survived one: dropping a row's status, swapping two rows' links, and marking one
        design REJECTED while writing REJECTED on a different design's row, which misstates
        both and leaves the two sets equal.

        The pairing seam is in the markup: the manual states a status as the TEXT of the
        anchor whose HREF names the design, so the link and the claim about it are one string
        and cannot drift apart.
        """
        manual = MANUAL.read_text(encoding="utf-8")
        for p in designs():
            status = design_status(p)
            with self.subTest(design=p.name):
                anchors = re.findall(
                    rf'<a href="{re.escape(DESIGN_URL + p.name)}"[^>]*>([^<]*)</a>', manual
                )
                if status not in LANDED_STATUSES:
                    continue
                self.assertNotEqual([], anchors, f"the P0 manual does not link {p.name}")
                for text in anchors:
                    stated = re.search(r"\b([A-Z][A-Z_]{2,})\b", text)
                    self.assertIsNotNone(stated, f"the manual links {p.name} and states no status: {text!r}")
                    self.assertEqual(
                        status, stated.group(1),
                        f"the manual says {p.name} is {stated.group(1)}; the design says {status}",
                    )

    def test_every_landed_design_is_linked(self) -> None:
        """Positive control for the rule above: it must have had every design to check.

        Written separately because the rule above returns early for a status the manual need
        not link, and a rule that can skip its whole corpus has to say how many it saw.
        """
        landed = [p for p in designs() if design_status(p) in LANDED_STATUSES]
        self.assertEqual(len(designs()), len(landed), "a design in the pack is at a status the manual need not link")
        self.assertGreaterEqual(len(landed), 13, "fewer designs than the pack holds")

    def test_the_epic_row_holds_its_own_design_link(self) -> None:
        """A numbered design's link is in the row of the epic it belongs to, not merely somewhere.

        Review swapped two rows' links and the substring check did not notice, because it asked
        whether the file contained a link and not which row held it. The security proof has no
        epic row of its own and is checked by the rule above alone.
        """
        manual = MANUAL.read_text(encoding="utf-8")
        rows = re.findall(r"<tr>.*?</tr>", manual, re.S)
        self.assertNotEqual([], rows, "the manual has no table rows; this check reads nothing")
        checked = 0
        for p in designs():
            epic = re.match(r"P0\.(\d{2})-", p.name)
            if not epic:
                continue
            wanted = f"<strong>P0.{int(epic.group(1))}</strong>"
            with self.subTest(design=p.name):
                owning = [r for r in rows if wanted in r]
                self.assertEqual(1, len(owning), f"expected exactly one epic row for {wanted}")
                self.assertIn(
                    DESIGN_URL + p.name, owning[0],
                    f"the row for {wanted} does not link {p.name}; another row may hold it",
                )
                checked += 1
        self.assertEqual(12, checked, "expected twelve numbered designs to check")


if __name__ == "__main__":
    unittest.main()
