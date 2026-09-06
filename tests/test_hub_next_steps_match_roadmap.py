#!/usr/bin/env python3
"""The hub's next-steps cards carry docs/NEXT_STEPS.md's frozen labels, and must keep carrying them.

docs/NEXT_STEPS.md (ROADMAP-002) numbers twelve items NS-001 to NS-012 as frozen roadmap labels.
The hub's next-steps section shows seven of them as cards. Until WP-062 the hub numbered its three
platform cards NS-005 to NS-007, which in NEXT_STEPS are documentation ownership, schema validation
and the issue-branch-PR binding; a state file's "NS-007 unticketed" was then read as the hub's card
(#203, #208). This module holds every hub card to the NEXT_STEPS heading with the same id: same id,
same title after normalisation (backticks stripped, whitespace collapsed, case folded).

The live action ledger is badf/next-actions.json, which numbers its own actions; nothing here reads
it, and NEXT_STEPS's own header says why its ids and the ledger's must never be resolved against
each other.

Positive controls: NEXT_STEPS must yield at least twelve headings and the hub at least one card.

Negative controls (run 2026-09-06 under WP-062, on in-memory copies):
  * Renumber the hub's Freeze card back to NS-005   -> test_hub_cards_match_roadmap_headings FAILS
  * Retitle the hub's NS-004 card "Guard main"       -> test_hub_cards_match_roadmap_headings FAILS
  * Add a hub card NS-013                            -> test_hub_cards_match_roadmap_headings and test_hub_shows_exactly_seven_cards FAIL
  * Delete the hub's NS-002 card                     -> test_hub_shows_exactly_seven_cards FAILS (review pass)

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import html as html_mod
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "index.html"
ROADMAP = ROOT / "docs" / "NEXT_STEPS.md"
CARD_COUNT = 7  # the hub shows seven of the file's twelve; a lost or added card fails here before the comparison


def _norm(fragment: str) -> str:
    s = re.sub(r"<[^>]+>", "", fragment)
    s = html_mod.unescape(s).replace("`", "")
    return re.sub(r"\s+", " ", s).strip().lower()


def roadmap_headings() -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"^### (NS-\d{3}): (.+?)\s*$", ROADMAP.read_text(encoding="utf-8"), re.M):
        out[m.group(1)] = _norm(m.group(2))
    return out


def hub_cards() -> dict[str, str]:
    html = HUB.read_text(encoding="utf-8")
    m = re.search(r'<section id="next-steps".*?</section>', html, re.S)
    assert m, "the hub has no next-steps section"
    out: dict[str, str] = {}
    for card in re.finditer(r"<span>(NS-\d{3}) · [^<]*</span>(?:<div>)?<h3>(.*?)</h3>", m.group(0), re.S):
        out[card.group(1)] = _norm(card.group(2))
    return out


class TestCorpusIsPresent(unittest.TestCase):
    """Positive controls. Without these the comparison below can pass over nothing."""

    def test_roadmap_yields_its_twelve_headings(self) -> None:
        self.assertGreaterEqual(len(roadmap_headings()), 12, "docs/NEXT_STEPS.md no longer yields twelve NS headings; re-derive this test")

    def test_hub_yields_cards(self) -> None:
        self.assertGreaterEqual(len(hub_cards()), 1, "no next-steps cards parsed on the hub; the shape changed or the parser is wrong")

    def test_hub_shows_exactly_seven_cards(self) -> None:
        self.assertEqual(CARD_COUNT, len(hub_cards()), "the hub does not show exactly seven next-steps cards; the hub's intro and NEXT_STEPS's note both say seven")


class TestHubCarriesTheFrozenLabels(unittest.TestCase):
    def test_hub_cards_match_roadmap_headings(self) -> None:
        headings, cards = roadmap_headings(), hub_cards()
        problems = []
        for ns_id, title in sorted(cards.items()):
            if ns_id not in headings:
                problems.append(f"{ns_id} is on the hub but docs/NEXT_STEPS.md has no such heading")
            elif headings[ns_id] != title:
                problems.append(f"{ns_id}: hub says {title!r}, NEXT_STEPS says {headings[ns_id]!r}")
        self.assertEqual([], problems, "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
