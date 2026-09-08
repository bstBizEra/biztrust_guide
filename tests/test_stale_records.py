#!/usr/bin/env python3
"""A record that says work remains must not describe work that has landed.

Six findings on 2026-09-08 were one defect wearing three disguises (#343, #347, and two instances
added to #326): a governance record telling a reader that something still needs doing, when it was
done. Three documents, three detection methods, and no test read any of them, which is why each
drifted in silence. This module is that test (#349).

WHAT IT MAY NOT DO. The suite is offline - no `requests`, `urllib` or `socket` anywhere under
`tests/` - and #311 exists to keep it so. **So this guard may never ask GitHub whether an issue is
closed.** Both defects below are detectable without the network, which is the whole reason they were
chosen; the issue-state variant belongs to #311's advisory reconciliation and deliberately not here.

TWO CHECKS.

  A  A row that names a string in a file. `SOURCE_RECONCILIATION.md`'s table records which published
     summaries still repeat a superseded claim, and each row names the exact string it waits on -
     "`docs/NEXT_STEPS.md:89` - `ADR-001...012`". A row asserting that a file still contains a string
     is checkable by looking for the string. When the repair lands, the string goes, and the row
     becomes a lie that nothing catches. Two such rows are stale today.

  B  A ticket cited as both landed and outstanding. `BIZTRUST-PLAN-001` section 14 is titled "What
     this document does not yet carry". Its first bullet credits WP-051 and WP-055 as landed, naming
     #165 and #169. Its last lists #165 to #170 as manuals that have not moved. The same tickets,
     both ways, four bullets apart. The contradiction is internal: no network is needed to see that
     one section says a ticket is both done and not done.

WHY A STRING AND NOT AN ISSUE NUMBER. Check A was nearly written against the issue the row cites
(#35, #34, both closed). That version would have needed the network, and it would also have been
wrong in a subtler way: an issue can close for reasons that leave the published summary untouched -
wontfix, superseded, split. The string is the claim. The issue is only who was asked to change it.

THE ELLIPSIS IS LITERAL. `ADR-001...012` reads like notation for a range, and the first draft of this
module assumed it was and skipped the row. It is not: `docs/NEXT_STEPS.md` today literally contains
`ADR-001...020`, the same notation with the number repaired. So the row's string was a real string,
it is really gone, and a guard that had "helpfully" treated it as shorthand would have passed on the
defect it exists to catch. Checked against the commit that added the row before relying on it.

RATCHET, as `tests/test_btg1_matrix_reconciles.py` uses it. Every entry below fails TODAY. Each is
registered with what it is and why, and asserted to still fail at exactly its registered value, so a
repair forces it out of the registry rather than quietly satisfying a weaker test. Registry
membership is asserted too, so the guard cannot be quieted by filing a new defect into it.

NEGATIVE CONTROLS, re-run 2026-09-08, each failing for the reason it names:
  * a registered row's string restored to its file        -> test_registered_rows_still_fail FAILS
  * an unregistered row's string deleted from its file    -> test_no_unregistered_stale_rows FAILS
  * a ticket added to section 14 as both landed and open  -> test_no_unregistered_contradictions FAILS
  * an entry added to either registry                     -> test_registries_are_exactly_these FAILS
  * the anchor heading renamed                            -> test_anchors_exist FAILS

Stdlib only: no third-party import, no network, no subprocess.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RECONCILIATION = ROOT / "docs/architecture/SOURCE_RECONCILIATION.md"
PLAN = ROOT / "docs/architecture/BIZTRUST-PLAN-001.md"

# --- check A ---------------------------------------------------------------------------------
# A row of the reconciliation table marked Deferred: backticked file references, an em dash, then
# the backticked string the row says those files still contain.
DEFERRED_ROW = re.compile(r"^\|.*\*\*Deferred\*\*.*\|", re.M)
BACKTICKED = re.compile(r"`([^`]+)`")

# Rows that are stale TODAY. Key is the target string; value is (files, why).
STALE_ROWS: dict[str, tuple[tuple[str, ...], str]] = {
    "ADR-001…012": (
        ("docs/NEXT_STEPS.md",),
        "closed by #35 in b93c701; the file now reads ADR-001…020, the same notation repaired",
    ),
    "G0…G8": (
        ("index.html", "docs/AGENT_CONTINUITY.md"),
        "closed by #34 in 151ca05, which landed a regression guard for the ENG-G* namespace",
    ),
}

# --- check B ---------------------------------------------------------------------------------
SECTION_14 = "## 14. What this document does not yet carry"
LANDED = re.compile(r"\bsince (?:WP|BIZTRUST-GUIDE-WP)-\d+|\bis a pointer to\b|\bare a pointer to\b")
ISSUE = re.compile(r"issues/(\d{1,4})\b")

# Tickets section 14 cites as landed AND lists as outstanding. Value is why.
#
# Only #165. The bullet writes its range as "[#165](…) to [#170](…)", so #169 - which bullet 1 does
# credit to WP-055 - never appears literally in bullet 5 and is not an intersection. This module was
# first written registering #169 as well, and its own ratchet refused the entry, which is the whole
# point of asserting that a registered defect still fails. Ranges are read as the two endpoints they
# literally are; expanding "#165 to #170" into six tickets would find #169 and would also invent
# citations wherever "to" sits between two issue links for another reason. One literal contradiction
# is enough to catch the defect, and it is the one that is actually written down.
CONTRADICTED: dict[str, str] = {
    "165": "credited to WP-051 in bullet 1; listed among the manuals that have not moved in bullet 5",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def deferred_rows() -> list[tuple[tuple[str, ...], str]]:
    """Each Deferred row as (files it names, the string it says they contain)."""
    out = []
    for row in DEFERRED_ROW.findall(read(RECONCILIATION)):
        cells = [c.strip() for c in row.strip("|").split("|")]
        # The claim cell is the one carrying both a file reference and a target string.
        for cell in cells:
            ticks = BACKTICKED.findall(cell)
            if len(ticks) < 2:
                continue
            files = tuple(t.split(":")[0] for t in ticks[:-1] if "/" in t or t.endswith(".html"))
            target = ticks[-1]
            if files:
                out.append((files, target))
                break
    return out


def section_14() -> str:
    text = read(PLAN)
    start = text.index(SECTION_14)
    nxt = text.find("\n## ", start + 1)
    return text[start: nxt if nxt != -1 else len(text)]


def contradictions() -> dict[str, str]:
    """Tickets section 14 cites as landed and also lists as outstanding."""
    landed: set[str] = set()
    outstanding: set[str] = set()
    for bullet in section_14().split("\n- ")[1:]:
        nums = set(ISSUE.findall(bullet))
        (landed if LANDED.search(bullet) else outstanding).update(nums)
    return {n: "" for n in landed & outstanding}


class TestAnchorsExist(unittest.TestCase):
    """A reader scoped to nothing reads everything. Assert what this module is aimed at."""

    def test_anchors_exist(self) -> None:
        self.assertTrue(RECONCILIATION.is_file(), RECONCILIATION)
        self.assertTrue(PLAN.is_file(), PLAN)
        self.assertIn(SECTION_14, read(PLAN),
                      "BIZTRUST-PLAN-001 section 14's heading moved; check B is scoped to it by name")
        self.assertTrue(deferred_rows(),
                        "SOURCE_RECONCILIATION carries no Deferred row naming a file and a string; "
                        "check A now reads nothing and would pass on anything")


class TestStaleRows(unittest.TestCase):
    """Check A: a row saying a file contains a string, where it does not."""

    def test_registered_rows_still_fail(self) -> None:
        """Each registered row is STILL stale. A repair forces it out of the registry."""
        for target, (files, why) in STALE_ROWS.items():
            for rel in files:
                body = read(ROOT / rel)
                self.assertNotIn(
                    target, body,
                    f"{rel} now contains {target!r}, so the SOURCE_RECONCILIATION row naming it is no "
                    f"longer stale. Registered because: {why}. Remove this entry from STALE_ROWS "
                    f"rather than leaving a registry that no longer describes the repository.")

    def test_no_unregistered_stale_rows(self) -> None:
        """Every other Deferred row's string is really in the files it names."""
        for files, target in deferred_rows():
            if target in STALE_ROWS:
                continue
            for rel in files:
                path = ROOT / rel
                self.assertTrue(path.is_file(),
                                f"a Deferred row names {rel}, which does not exist")
                self.assertIn(
                    target, read(path),
                    f"SOURCE_RECONCILIATION says {rel} still contains {target!r}, and it does not. "
                    f"Either the repair landed and the row should say so, or the row's target is "
                    f"mistyped. This is the #347 defect, unregistered.")

    def test_registries_are_exactly_these(self) -> None:
        """Membership is asserted, so a new defect cannot be quieted by filing it in."""
        self.assertEqual(set(STALE_ROWS), {"ADR-001…012", "G0…G8"},
                         "STALE_ROWS changed. An entry may only LEAVE, when its row is repaired.")
        self.assertEqual(set(CONTRADICTED), {"165"},
                         "CONTRADICTED changed. An entry may only LEAVE, when section 14 is repaired.")


class TestSection14Contradictions(unittest.TestCase):
    """Check B: one section calling a ticket both landed and outstanding."""

    def test_registered_contradictions_still_fail(self) -> None:
        found = contradictions()
        for num, why in CONTRADICTED.items():
            self.assertIn(
                num, found,
                f"section 14 no longer cites #{num} as both landed and outstanding. Registered "
                f"because: {why}. Remove this entry from CONTRADICTED.")

    def test_no_unregistered_contradictions(self) -> None:
        extra = set(contradictions()) - set(CONTRADICTED)
        self.assertFalse(
            extra,
            f"section 14 cites {sorted('#' + n for n in extra)} as both landed and outstanding. "
            f"A section titled 'What this document does not yet carry' cannot also credit the same "
            f"ticket as carried. This is the #343 defect, unregistered.")


if __name__ == "__main__":
    unittest.main()
