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
  * Add a tenth seat to the hub                -> test_seats_match_the_plan FAILS

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
CONTRACT_SEATS = ("business authority", "insurance practitioner", "legal and compliance reviewer", "finance and accounting reviewer", "accountable architecture owner")


def _norm(fragment: str) -> str:
    s = re.sub(r"<[^>]+>", "", fragment)
    s = html_mod.unescape(s).replace("`", "")
    return re.sub(r"\s+", " ", s).strip().lower()


def plan_seats() -> dict[str, str]:
    """The seats table: `| Seat | Source | Records or accepts |` -> {seat: records}."""
    text = PLAN.read_text(encoding="utf-8").split(SECTION_START, 1)[1].split(SECTION_END, 1)[0]
    block = text.split("**The seats**", 1)[1].split("**The roadmap", 1)[0]
    out: dict[str, str] = {}
    for line in block.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$", line)
        if m and m.group(1) not in ("Seat", "---"):
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

    def test_hub_parses(self) -> None:
        self.assertGreaterEqual(len(hub_seats()), 1, "no seat rows parsed on the hub; the table shape changed or the parser is wrong")


class TestParityWithThePlan(unittest.TestCase):
    def test_seats_match_the_plan(self) -> None:
        self.assertEqual(plan_seats(), hub_seats(), "the hub's seats table disagrees with PLAN-001 section 12.1")


if __name__ == "__main__":
    unittest.main()
