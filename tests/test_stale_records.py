#!/usr/bin/env python3
"""A record that says work remains must not describe work that has landed.

Six findings on 2026-09-08 were one defect wearing three disguises (#343, #347, and two instances
added to #326): a governance record telling a reader that something still needs doing, when it was
done. Three documents, three detection methods, and no test read any of them, which is why each
drifted in silence. This module is that test (#349).

WHAT IT MAY NOT DO. The suite is offline - no `requests`, `urllib` or `socket` anywhere under
`tests/` - and #311 exists to keep it so. **This guard may never ask GitHub whether an issue is
closed.** Both defects below are detectable without the network, which is why they were chosen; the
issue-state variant belongs to #311's advisory reconciliation and deliberately not here.

TWO CHECKS.

  A  A row that names a string in a file. `SOURCE_RECONCILIATION.md`'s table records which published
     summaries still repeat a superseded claim, and each row names the exact string it waits on -
     "`docs/NEXT_STEPS.md:89` - `ADR-001...012`". A row that says a file still contains a string is
     checkable by looking for the string. Two rows are stale today.

  B  A ticket cited as both landed and outstanding inside one section. `BIZTRUST-PLAN-001` section 14
     is titled "What this document does not yet carry". Its first bullet credits WP-051 as landed for
     #165; its last lists #165 among manuals that have not moved. No network is needed to see that
     one section says a ticket is both done and not done.

WHAT THE FIRST VERSION GOT WRONG, because it is the whole reason this module is shaped as it is.

  The ratchet did not ratchet. `test_registered_rows_still_fail` asserted `target not in file` - a
  property of the FILE. But #347's repair is to fix the ROW. Rewriting a row's status from
  `**Deferred**` to `**Closed**` left the suite green with the entry still registered; deleting the
  row entirely did too. The registry could outlive the row it described, which is the drift this
  module exists to stop. Every one of the five negative controls passed because every one exercised
  the file and none exercised the row.

  So a registration now names WHAT THE ROW SAYS, and the assertion is two-sided: the row must still
  be present AND still carry its registered status AND its string must still be absent. Repairing the
  row in any of those ways forces the entry out.

  Check B classified by a three-phrase whitelist and defaulted everything unmatched to "outstanding".
  That made an ownership sentence in bullet 4 look like a deferral and kept #165 satisfied even when
  bullet 5 - the bullet #343 actually names - was repaired. Classification is now positive on both
  sides: a bullet joins "landed" only on completion language and "outstanding" only on deferral
  language, and a bullet matching neither is UNCLASSIFIED, counted, and its count registered, so new
  wording surfaces instead of being silently bucketed.

  Both were found by a fresh-context review of PR #350, not by the author.

RATCHET, as `tests/test_btg1_matrix_reconciles.py` uses it. Every entry below fails TODAY, is
registered with a reason, and is asserted to still fail at exactly its registered value. Registry
membership is asserted too, so a new defect cannot be filed in to quiet the guard.

CORPUS FLOOR. `test_anchors_exist` asserts a floor near the true corpus size rather than merely
non-empty, as `test_adr_citations.py` and `test_btg1_matrix_reconciles.py` do. Non-empty was the
first version's mistake here as well: both Deferred rows are registered, so the unregistered arm
iterated two rows, skipped both, and asserted nothing while looking alive.

NEGATIVE CONTROLS, re-run 2026-09-08, each failing for the reason it names. Each exercises the ROW or
the CLASSIFIER, not only the file:
  * a registered row's status changes Deferred -> Closed  -> test_registered_rows_still_fail FAILS
  * a registered row is deleted outright                  -> test_registered_rows_still_fail FAILS
  * a registered row's string returns to its file          -> test_registered_rows_still_fail FAILS
  * an unregistered row's string vanishes                  -> test_no_unregistered_stale_rows FAILS
  * bullet 5 is repaired, #165 no longer outstanding       -> test_registered_contradictions_still_fail FAILS
  * a ticket added to section 14 as both landed and open   -> test_no_unregistered_contradictions FAILS
  * a bullet is written in wording neither regex knows     -> test_every_bullet_is_classified FAILS
  * an entry is added to either registry                   -> test_registries_are_exactly_these FAILS
  * the section 14 anchor is renamed                       -> test_anchors_exist FAILS

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
# SCOPED TO ONE TABLE, by its header. SOURCE_RECONCILIATION.md holds five tables and the first
# version of this reader was scoped to none of them: it matched 38 rows across the whole file, of
# which 36 are source inventories and finding lists that assert nothing about a published summary.
# The corpus floor is what exposed that, which is the argument for having one. The sibling guard
# tests/test_btg1_matrix_reconciles.py learned the same lesson the same way and says so in its own
# docstring: a reader scoped to nothing reads everything.
TABLE_HEADER = "| Reconciled claim | Published summary | Status | Owner |"
TABLE_ROW = re.compile(r"^\|(?!\s*[-: ]+\|).*\|\s*$", re.M)
STATUS = re.compile(r"\*\*([^*]+)\*\*")
BACKTICKED = re.compile(r"`([^`]+)`")

# The reconciliation table's data rows. Exactly 3 today: one `Updated in this change` naming
# index.html in prose, and the two `Deferred` rows registered below. Asserted as an equality rather
# than a floor, so a row ADDED to the table is noticed as loudly as one removed - a new reconciled
# claim is exactly the thing this module should be made to read.
RECONCILIATION_ROWS = 3

# Rows stale TODAY. Key is the target string the row says its files still contain.
# `status` is what the row's status cell says - registering it is what makes this a ratchet:
# repair the row and the registration stops describing it.
STALE_ROWS: dict[str, dict] = {
    "ADR-001…012": {
        "files": ("docs/NEXT_STEPS.md",),
        "status": "Deferred",
        "why": ("closed by #35 in b93c701; docs/NEXT_STEPS.md now reads ADR-001…020, the same "
                "ellipsis notation with the number repaired, so the row's target is really gone"),
    },
    "G0…G8": {
        "files": ("index.html", "docs/AGENT_CONTINUITY.md"),
        "status": "Deferred",
        "why": ("closed by #34 in 151ca05, which landed a regression guard for the ENG-G* gate "
                "namespace, so this row describes work that is not merely done but tested"),
    },
}

# --- check B ---------------------------------------------------------------------------------
SECTION_14 = "## 14. What this document does not yet carry"
COMPLETION = re.compile(
    r"\bsince (?:BIZTRUST-GUIDE-)?WP-\d+|\bis a pointer to\b|\bare a pointer to\b"
    r"|\bcarrie[sd] (?:it|them)\b|\blanded (?:in|as|under)\b|\bcredited to\b|\bresolved by\b", re.I)
DEFERRAL = re.compile(
    r"\buntil (?:they|it|the|that)\b|\bnot yet\b|\bdoes not yet\b|\bstill (?:stand|name|read|list)"
    r"|\bwaits on\b|\bremain(?:s)? (?:open|outstanding)\b|\bhas not\b", re.I)
ISSUE = re.compile(r"(?:issues/|#)(\d{1,4})\b")

# Tickets section 14 cites as landed AND as outstanding.
#
# Only #165. Bullet 5 writes its range as "[#165](…) to [#170](…)", so #169 - which bullet 1 does
# credit to WP-055 - never appears literally there and is not an intersection. The first version of
# this module registered #169 as well and its own ratchet refused the entry, which is what asserting
# that a registered defect still fails is for. Ranges are read as the two endpoints they literally
# are; expanding them would find #169 and would also invent citations wherever "to" sits between two
# issue links for another reason.
CONTRADICTED: dict[str, str] = {
    "165": ("credited to WP-051 in bullet 1 as a landed pointer, and listed in bullet 5 among the "
            "manuals that have not moved; the two bullets are four apart in one section"),
}

# Bullets in section 14 matching neither vocabulary. Registered so that new wording surfaces here
# rather than being silently bucketed as outstanding, which is how the first version let bullet 4's
# ownership sentence keep entry 165 satisfied.
UNCLASSIFIED_BULLETS = 2


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def reconciliation_table() -> list[str]:
    """The data rows of the reconciliation table, and no other table's."""
    text = read(RECONCILIATION)
    start = text.index(TABLE_HEADER) + len(TABLE_HEADER)
    rest = text[start:]
    end = rest.find("\n\n")
    body = rest[: end if end != -1 else len(rest)]
    return [r for r in TABLE_ROW.findall(body)]


def reconciliation_rows() -> list[dict]:
    """Those rows that name files and a target string, with the status each carries."""
    out = []
    for row in reconciliation_table():
        status = STATUS.search(row)
        for cell in (c.strip() for c in row.strip().strip("|").split("|")):
            ticks = BACKTICKED.findall(cell)
            if len(ticks) < 2:
                continue
            files = tuple(t.split(":")[0] for t in ticks[:-1] if "/" in t or t.endswith(".html"))
            if files:
                out.append({"files": files, "target": ticks[-1],
                            "status": status.group(1).split()[0] if status else "",
                            "row": row})
                break
    return out


def section_14() -> str:
    text = read(PLAN)
    start = text.index(SECTION_14)
    nxt = text.find("\n## ", start + 1)
    return text[start: nxt if nxt != -1 else len(text)]


def bullets() -> list[str]:
    return [b for b in section_14().split("\n- ")[1:]]


def classify() -> tuple[set[str], set[str], list[str]]:
    """(landed, outstanding, unclassified). A bullet joins a set only on positive evidence."""
    landed: set[str] = set()
    outstanding: set[str] = set()
    unclassified: list[str] = []
    for bullet in bullets():
        nums = set(ISSUE.findall(bullet))
        if COMPLETION.search(bullet):
            landed |= nums
        elif DEFERRAL.search(bullet):
            outstanding |= nums
        else:
            unclassified.append(bullet.strip()[:80])
    return landed, outstanding, unclassified


def contradictions() -> set[str]:
    landed, outstanding, _ = classify()
    return landed & outstanding


class TestAnchorsExist(unittest.TestCase):
    """A reader scoped to nothing reads everything, and a floor is not the same as non-empty."""

    def test_anchors_exist(self) -> None:
        self.assertTrue(RECONCILIATION.is_file(), RECONCILIATION)
        self.assertIn(SECTION_14, read(PLAN),
                      "BIZTRUST-PLAN-001 section 14's heading moved; check B is scoped to it by name")
        self.assertIn(TABLE_HEADER, read(RECONCILIATION),
                      "the reconciliation table's header moved; check A is scoped to it by name")
        rows = reconciliation_table()
        self.assertEqual(
            RECONCILIATION_ROWS, len(rows),
            f"the reconciliation table has {len(rows)} data rows, against {RECONCILIATION_ROWS} "
            f"registered. A row added is a new reconciled claim this module should be made to read; a "
            f"row removed means the reader is seeing less than it should, which is how a guard passes "
            f"while reading nothing.")
        self.assertGreaterEqual(
            len(bullets()), 4,
            f"section 14 has {len(bullets())} bullets; check B reads too few to be meaningful")


class TestStaleRows(unittest.TestCase):
    """Check A: a row saying a file contains a string, where it does not."""

    def test_registered_rows_still_fail(self) -> None:
        """Registered rows STILL say what they were registered as saying, and are STILL wrong.

        Two-sided on purpose. The first version asserted only the file half, so repairing the ROW -
        changing its status, or deleting it - left the entry registered and the guard silent.
        """
        rows = {r["target"]: r for r in reconciliation_rows()}
        for target, reg in STALE_ROWS.items():
            self.assertIn(
                target, rows,
                f"no reconciliation row now names {target!r}. The row was repaired or removed, so this "
                f"registration no longer describes the repository. Registered because: {reg['why']}. "
                f"Remove the entry from STALE_ROWS.")
            self.assertEqual(
                reg["status"], rows[target]["status"],
                f"the row naming {target!r} now reads {rows[target]['status']!r}, not "
                f"{reg['status']!r}. It has been repaired; remove the entry from STALE_ROWS.")
            for rel in reg["files"]:
                self.assertNotIn(
                    target, read(ROOT / rel),
                    f"{rel} now contains {target!r}, so the row naming it is no longer stale. "
                    f"Remove the entry from STALE_ROWS.")

    def test_no_unregistered_stale_rows(self) -> None:
        """Every other row's target string is really in the files it names."""
        for row in reconciliation_rows():
            if row["target"] in STALE_ROWS or row["status"].lower() != "deferred":
                continue
            for rel in row["files"]:
                path = ROOT / rel
                self.assertTrue(path.is_file(), f"a Deferred row names {rel}, which does not exist")
                self.assertIn(
                    row["target"], read(path),
                    f"SOURCE_RECONCILIATION says {rel} still contains {row['target']!r}, and it does "
                    f"not. Either the repair landed and the row should say so, or the target is "
                    f"mistyped. This is the #347 defect, unregistered.")


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
        extra = contradictions() - set(CONTRADICTED)
        self.assertFalse(
            extra,
            f"section 14 cites {sorted('#' + n for n in extra)} as both landed and outstanding. A "
            f"section titled 'What this document does not yet carry' cannot also credit the same "
            f"ticket as carried. This is the #343 defect, unregistered.")

    def test_every_bullet_is_classified(self) -> None:
        """A bullet neither vocabulary recognises joins no set, and its count is registered.

        The first version had no third bucket: anything unmatched became 'outstanding', so an
        ownership sentence propped up a contradiction that had actually been repaired.
        """
        _, _, unclassified = classify()
        self.assertEqual(
            UNCLASSIFIED_BULLETS, len(unclassified),
            f"section 14 has {len(unclassified)} bullets that neither COMPLETION nor DEFERRAL "
            f"recognises, against {UNCLASSIFIED_BULLETS} registered. New wording has appeared and is "
            f"being read as neither landed nor outstanding, so a contradiction written that way would "
            f"be invisible. Widen the vocabulary or move the count: {unclassified}")


class TestTheRegistriesAreRatchets(unittest.TestCase):
    """Membership is asserted, so a new defect cannot be quieted by filing it in."""

    def test_registries_are_exactly_these(self) -> None:
        self.assertEqual(set(STALE_ROWS), {"ADR-001…012", "G0…G8"},
                         "STALE_ROWS changed. An entry may only LEAVE, when its row is repaired.")
        self.assertEqual(set(CONTRADICTED), {"165"},
                         "CONTRADICTED changed. An entry may only LEAVE, when section 14 is repaired.")

    def test_every_registration_gives_a_reason(self) -> None:
        """As tests/test_btg1_matrix_reconciles.py requires of its own registry."""
        for target, reg in STALE_ROWS.items():
            self.assertGreater(len(reg["why"].split()), 12,
                               f"STALE_ROWS[{target!r}] has no real reason; a registry entry without "
                               f"one is a suppression")
        for num, why in CONTRADICTED.items():
            self.assertGreater(len(why.split()), 12,
                               f"CONTRADICTED[{num!r}] has no real reason")


if __name__ == "__main__":
    unittest.main()
