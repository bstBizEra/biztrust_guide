#!/usr/bin/env python3
"""landing/architecture.html projects BIZTRUST-ARCH-001 sections 5, 6 and 17 and the roadmap's contract family, and must keep projecting them.

Four things on the page are copied from records and held here: the capability map (contract
section 6, cell for cell), the contract family (the roadmap's section 3 table, cell for cell),
the seventeen exit criteria (contract section 17, verbatim), and the invariant identifiers
(contract section 5: the same twenty-two ids, in the same order). The invariants' words are the
page's own plain restatement and are not held; the source line says so.

Positive controls: the contract must yield four groups, twenty-two invariants and seventeen
criteria, the roadmap twelve contracts, and the page at least one row per table.

Negative controls (run 2026-09-06 under WP-066, on in-memory copies):
  * Change the Financial group's modules on the page  -> test_capability_map_matches_the_contract FAILS
  * Drop BIZTRUST-WF-001 from the family table         -> test_family_matches_the_roadmap FAILS
  * Reword exit criterion 7 on the page                -> test_exit_criteria_match_the_contract FAILS
  * Swap INV-020 and INV-021 on the page               -> test_invariant_ids_match_the_contract FAILS

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
try:
    from showcase_parity import norm, section, md_rows, page_table, page_list
except ModuleNotFoundError:  # invoked by module name from the repository root rather than by discovery
    from tests.showcase_parity import norm, section, md_rows, page_table, page_list

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "landing" / "architecture.html"
CONTRACT = ROOT / "docs" / "architecture" / "BIZTRUST-ARCH-001.md"
ROADMAP = ROOT / "docs" / "research" / "roadmap" / "BIZTRUST-ROADMAP-001-operator-draft.md"


def contract_capability_map() -> dict[str, tuple[str, ...]]:
    return md_rows(section(CONTRACT, "\n## 6. Capability map", "\n## 7. "), r"Platform|Brokerage|Financial|Integration")


def contract_invariant_ids() -> list[str]:
    return re.findall(r"^\| (INV-\d{3}) \|", section(CONTRACT, "\n## 5. Architecture invariants", "\n## 6. "), re.M)


def contract_exit_criteria() -> list[str]:
    return [norm(line[2:]) for line in section(CONTRACT, "\n## 17. Contract-freeze exit criteria", "\n## 18. ").splitlines() if line.startswith("- ")]


def roadmap_family() -> dict[str, tuple[str, ...]]:
    return md_rows(section(ROADMAP, "\n## Architecture contract family", "\n## Architecture decisions to freeze"), r"`BIZTRUST-[A-Z]+-001`")


class TestCorpusIsPresent(unittest.TestCase):
    """Positive controls. Without these the comparisons below can pass over nothing."""

    def test_records_yield_their_tables(self) -> None:
        self.assertEqual(4, len(contract_capability_map()), "ARCH-001 section 6 no longer yields four groups; re-derive this test")
        self.assertEqual(22, len(contract_invariant_ids()), "ARCH-001 section 5 no longer yields twenty-two invariants; re-derive this test")
        self.assertEqual(17, len(contract_exit_criteria()), "ARCH-001 section 17 no longer yields seventeen criteria; re-derive this test")
        self.assertEqual(12, len(roadmap_family()), "the roadmap's contract family no longer yields twelve contracts; re-derive this test")

    def test_page_parses(self) -> None:
        self.assertTrue(PAGE.is_file(), "landing/architecture.html is missing")
        for table in ("capabilities", "family"):
            with self.subTest(table=table):
                self.assertGreaterEqual(len(page_table(PAGE, table)), 1)
        for lst in ("invariants", "criteria"):
            with self.subTest(list=lst):
                self.assertGreaterEqual(len(page_list(PAGE, lst)), 1)


class TestParityWithTheRecords(unittest.TestCase):
    def test_capability_map_matches_the_contract(self) -> None:
        self.assertEqual(contract_capability_map(), page_table(PAGE, "capabilities"), "the capability map disagrees with ARCH-001 section 6")

    def test_family_matches_the_roadmap(self) -> None:
        self.assertEqual(roadmap_family(), page_table(PAGE, "family"), "the contract family disagrees with the roadmap's section 3")

    def test_exit_criteria_match_the_contract(self) -> None:
        self.assertEqual(contract_exit_criteria(), page_list(PAGE, "criteria"), "the exit criteria disagree with ARCH-001 section 17")

    def test_invariant_ids_match_the_contract(self) -> None:
        page_ids = [item.split(" ", 1)[0].upper() for item in page_list(PAGE, "invariants")]
        self.assertEqual(contract_invariant_ids(), page_ids, "the invariants' identifiers or order disagree with ARCH-001 section 5")


if __name__ == "__main__":
    unittest.main()
