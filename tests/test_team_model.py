#!/usr/bin/env python3
"""The hub's seats table is a rendering of PLAN-001 section 12.1, and must stay one.

PLAN-001 section 12.1 records the team model: seats (humans who hold authority), roles (a
responsibility within one stage) and personas (agent identities). Only the seats are rendered
on the hub, as a table in its team-topology section, because seats are what a reader must not
confuse with an agent. The table is read row for row from the plan and compared with the hub
after the same normalisation the plan-rendering tests use.

Positive controls guard the parsers: the plan must yield at least the five review seats the
contract map requires (#27), and the hub must parse at least one seat row.

Negative controls (run 2026-09-06 under WP-061, on in-memory copies):
  * Rename a seat on the hub                   -> test_seats_match_the_plan FAILS
  * Drop the practitioner row from the hub     -> test_seats_match_the_plan FAILS
  * Add a tenth seat to the hub                -> test_seats_match_the_plan and test_plan_and_hub_each_hold_nine_seats FAIL
  * Reword the seats table's header in the plan -> plan_seats raises with the header it expects (review pass)

Text is normalised by showcase_parity.norm, shared with the showcase tests (WP-110, #341).
This module carried its own copy; four modules carried the same one.

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import html as html_mod
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "index.html"
PLAN = ROOT / "docs" / "architecture" / "BIZTRUST-PLAN-001.md"
SECTION_START, SECTION_END = "\n### 12.1 ", "\n## 13. "
CONTRACT_SEATS = ("business authority", "insurance-domain practitioner", "legal/compliance reviewer", "finance/accounting reviewer", "accountable architecture owner")
SEAT_COUNT = 9  # the record's number; a tenth seat or a lost one fails here before the comparison


try:
    from showcase_parity import norm as _norm
except ModuleNotFoundError:  # invoked by module name from the repository root rather than by discovery
    from tests.showcase_parity import norm as _norm


SEATS_HEADER = "| Seat | Source | Records or accepts |"


def plan_seats() -> dict[str, str]:
    """The seats table, located by its header row and read to the next blank line -> {seat: records}."""
    text = PLAN.read_text(encoding="utf-8").split(SECTION_START, 1)[1].split(SECTION_END, 1)[0]
    assert SEATS_HEADER in text, f"PLAN-001 section 12.1 has no table headed {SEATS_HEADER!r}"
    body = text.split(SEATS_HEADER, 1)[1].split("\n\n", 1)[0]
    out: dict[str, str] = {}
    for line in body.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$", line)
        if m and not re.fullmatch(r"-+", m.group(1)):  # skip the |---| separator row
            out[_norm(m.group(1))] = _norm(m.group(3))
    return out


def hub_seats() -> dict[str, str]:
    html = HUB.read_text(encoding="utf-8")
    m = re.search(r'<section id="team".*?<tbody>(.*?)</tbody>', html, re.S)
    assert m, "the hub's team section has no seats table"
    out: dict[str, str] = {}
    for row in re.finditer(r"<tr><td><strong>(.*?)</strong></td><td>(.*?)</td></tr>", m.group(1), re.S):
        out[_norm(row.group(1))] = _norm(row.group(2))
    return out


class TestCorpusIsPresent(unittest.TestCase):
    """Positive controls. Without these the comparison below can pass over nothing."""

    def test_plan_yields_the_contract_seats(self) -> None:
        seats = plan_seats()
        for seat in CONTRACT_SEATS:
            with self.subTest(seat=seat):
                self.assertTrue(any(seat in s for s in seats), f"PLAN-001 section 12.1 lists no seat named like '{seat}'; #27 requires it")

    def test_plan_and_hub_each_hold_nine_seats(self) -> None:
        self.assertEqual(SEAT_COUNT, len(plan_seats()), "PLAN-001 section 12.1 does not list exactly nine seats; re-derive this test with the record")
        self.assertEqual(SEAT_COUNT, len(hub_seats()), "the hub does not render exactly nine seat rows")

    def test_hub_parses(self) -> None:
        self.assertGreaterEqual(len(hub_seats()), 1, "no seat rows parsed on the hub; the table shape changed or the parser is wrong")


class TestParityWithThePlan(unittest.TestCase):
    def test_seats_match_the_plan(self) -> None:
        self.assertEqual(plan_seats(), hub_seats(), "the hub's seats table disagrees with PLAN-001 section 12.1")


if __name__ == "__main__":
    unittest.main()
