#!/usr/bin/env python3
"""The hub summarises the delivery plan; it may not speak a partition the plan does not have.

Two phrases went stale on index.html when PLAN-001 re-partitioned the phases, and both were
found by review rather than by a test: "Authorize P2 based on evidence" (#190, WP-057) and
"Authorize P1" (#203, WP-059). Each authorised a whole phase, which the plan forbids: a phase
is a queue of Work Packages, never an approval state (PLAN-001 section 10; the overview's
invariant). This module makes the two shapes fail.

1. No "Authorize P<n>" on the hub. Authority is granted per Work Package after a gate is
   recorded; a card that authorises a phase by number is the previous plan's voice.
2. No letterless previous-plan epic identifier (P1.n, P2.n, P3.n) on the hub. Since WP-053
   to WP-055 those identifiers live only in PLAN-001's mapping columns; P0.n stays letterless
   by the plan's id rule and is allowed.

Negative controls (run 2026-09-06 under WP-059, on in-memory copies):
  * Put "Authorize P1" back on the hub     -> test_hub_authorises_no_phase FAILS
  * Put "P3.10" on the hub                 -> test_hub_names_no_previous_plan_epic FAILS
  * Put "P0.11" on the hub                 -> both PASS (allowed by the id rule)

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "index.html"

AUTHORISE_A_PHASE = re.compile(r"\bAuthori[sz]e\s+P[0-3]\b")
PREVIOUS_PLAN_EPIC = re.compile(r"\bP[1-3]\.\d{1,2}\b")


def hub_text(html: str) -> str:
    body = re.search(r"<main\b.*?>(.*)</main>", html, re.S)
    text = body.group(1) if body else html
    text = re.sub(r"<(script|style).*?</\1>", " ", text, flags=re.S)
    return re.sub(r"<[^>]+>", " ", text)


class TestHubSpeaksThePlan(unittest.TestCase):
    def setUp(self) -> None:
        self.text = hub_text(HUB.read_text(encoding="utf-8"))
        self.assertGreater(len(self.text), 1000, "index.html parsed to almost nothing; the shape changed")

    def test_hub_authorises_no_phase(self) -> None:
        found = sorted(set(AUTHORISE_A_PHASE.findall(self.text)))
        self.assertEqual([], found, f"the hub authorises a phase by number: {found}; authority is per Work Package after a gate")

    def test_hub_names_no_previous_plan_epic(self) -> None:
        found = sorted(set(PREVIOUS_PLAN_EPIC.findall(self.text)))
        self.assertEqual([], found, f"the hub names previous-plan epic identifiers: {found}; PLAN-001's P1 to P3 epics carry a sub-phase letter")


if __name__ == "__main__":
    unittest.main()
