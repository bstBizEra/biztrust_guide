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

THE RATCHET IS A DIGEST, and this is the third mechanism this module has had. The first two were
holed by independent review, both times in the same direction: the ratchet compared a SUMMARY of the
record - the first word of its first bold run, and a separately registered file tuple - so a repair
that changed the record without changing that summary left the entry registered and the suite green.
Measured, on fresh copies, all of these were green while the defect they name was repaired:

  * `**Deferred (closed by b93c701)**`                    - annotation inside the bold run
  * `**Deferred** - resolved 2026-09-05 by b93c701`       - annotation after it
  * `index.html` dropped from the `G0...G8` row's files   - the row's files were never read
  * the ADR row repointed at a file that DOES hold it     - likewise

A ratchet does not need to understand a record; it needs to notice that the record CHANGED. So each
registration now carries the SHA-256 of the exact registered text, normalised for line ending and
trailing whitespace and nothing else. Any repair, in any wording, in any of the four shapes above or
in one nobody has thought of, changes the digest and forces the entry out. The registered `files`
tuple and the registered status are gone with it: a matched digest fixes the row's whole text, so the
row supplies its own files and its own target, and the "the defect is still really present" half
reads THE FILES THE ROW NAMES. The registration says which record is being ratcheted; it is never
also the source of truth for what to check.

The digests were computed by running `digest()` over the tree at commit 57ed4d8, not written by hand.

CLASSIFICATION IS INDEPENDENT, NOT FIRST-MATCH. Check B's second hole was `if COMPLETION / elif
DEFERRAL`: a bullet carrying both vocabularies joined only the first set and so could never intersect
with itself, which is exactly how a reviewer wrote a single bullet calling one ticket both landed and
outstanding and watched the guard stay green. A bullet now contributes its tickets to `landed` if
COMPLETION matches AND to `outstanding` if DEFERRAL matches. A bullet matching neither is
UNCLASSIFIED, counted, and its count registered, so new wording surfaces instead of being bucketed.

WHAT THIS DOES NOT DO. Every item is a real limit, not a caveat.

 1. The ratchet on REGISTERED defects is exact. The DETECTION OF NEW, UNREGISTERED ones is
    heuristic: COMPLETION and DEFERRAL are regex vocabularies over English prose, and a
    contradiction written in wording neither knows is not caught. It lands in the unclassified
    bucket, whose SIZE is guarded and whose contents are not.
 2. Issue states are not read. Whether #35 is closed on GitHub is #311's business and needs the
    network this suite refuses.
 3. Ranges are read as their two literal endpoints. "#165 to #170" contributes #165 and #170, so
    #169 - which bullet 1 does credit - is not an intersection. Expanding ranges would also invent
    citations wherever "to" sits between two issue links for another reason.
 4. Only the reconciliation table and PLAN-001 section 14 are read. The sweep that found these
    examined 65 lines across all tracked `.md` and `.html`; other records may carry the class.
 5. Check A's unregistered arm has no live subject today. The table's three rows are one
    "Updated in this change" row, which names no backticked target, and the two registered rows,
    which the digest skip removes. It is exercised by the controls and by the row-count equality,
    not by current content.
 6. A row is read as making a live claim unless its status names it as `Updated`. A row given some
    third status - `**Closed**`, say - is still required to hold its string, and would fail loudly.
    That is deliberate: the table's vocabulary today is exactly `Updated in this change` and
    `Deferred`, the row count is asserted as an equality, so a third status is a deliberate edit
    that should re-derive this module rather than pass through it.

CORPUS FLOOR. `test_anchors_exist` asserts a floor near the true corpus size rather than merely
non-empty, as `test_adr_citations.py` and `test_btg1_matrix_reconciles.py` do. Non-empty was an
earlier mistake here as well: both Deferred rows are registered, so the unregistered arm iterated two
rows, skipped both, and asserted nothing while looking alive.

ANCHORS ARE ASSERTED, NOT ASSUMED. `section_14()` and `reconciliation_table()` return empty when
their anchor is missing rather than raising, as `test_btg1_matrix_reconciles.matrix_rows()` does, so
`test_anchors_exist` owns the diagnosis and a renamed heading reports the heading rather than a
`ValueError` from the middle of a reader.

NEGATIVE CONTROLS, eleven of them, run 2026-09-08 by `wp111_controls.py`: each on a fresh copy of
the worktree, one mutation apiece, `unittest discover -s tests -p test_stale_records.py` from that
copy's root, with the unmutated copy run first and green. Every mutation asserts that the text it
replaces was found, so a control cannot quietly become a no-op. The first four are the shapes two
independent reviews measured as GREEN under the previous mechanism.

ISOLATED - exactly one test fails:
  * the ADR row repointed at a file that DOES hold the string -> test_registered_rows_still_fail
  * the string restored to `docs/NEXT_STEPS.md`               -> test_registered_rows_still_fail
  * one bullet citing #199 as landed AND outstanding          -> test_no_unregistered_contradictions
  * a bullet in wording neither vocabulary knows              -> test_every_bullet_is_classified

NOT ISOLATED, and declared rather than trimmed, as `tests/test_stale_asks.py` and
`tests/test_btg1_matrix_reconciles.py` declare of their own. What each breaks really does break more
than one rule, and saying otherwise would be false precision:
  * `**Deferred (closed by b93c701)**` on the ADR row        -> test_registered_rows_still_fail and
  * `**Deferred** - resolved ... by b93c701` after the run   |  test_no_unregistered_stale_rows
  * `index.html` dropped from the `G0...G8` row              |
    Each changes the row's digest, so the row stops being skipped as registered, and it still reads
    `Deferred` over a string its files do not hold. Both failures are true: the registration no
    longer describes the row, and the row still misinforms a reader. A repair that instead marked
    the row `Updated` would fire only the first.
  * a registered row deleted outright     -> test_registered_rows_still_fail and test_anchors_exist,
                                             whose row count is an equality
  * an entry added to CONTRADICTED        -> test_registries_are_exactly_these and
                                             test_registered_contradictions_still_fail, because a
                                             filed-in entry names no contradiction that exists
  * the section 14 anchor renamed         -> test_anchors_exist,
                                             test_registered_contradictions_still_fail and
                                             test_every_bullet_is_classified
  * the reconciliation table header renamed -> test_anchors_exist and
                                               test_registered_rows_still_fail

Stdlib only: no third-party import, no network, no subprocess.
"""
from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RECONCILIATION = ROOT / "docs/architecture/SOURCE_RECONCILIATION.md"
PLAN = ROOT / "docs/architecture/BIZTRUST-PLAN-001.md"

# --- the ratchet's primitive -------------------------------------------------------------------


def digest(record: str) -> str:
    """The SHA-256 of a record's exact text.

    Normalised for line ending and trailing whitespace ONLY. Nothing else is touched: not case, not
    Markdown, not whitespace inside the record. Every earlier version of this module compared a
    summary of a record - a status word, a file tuple - and every earlier version was holed by a
    repair that left the summary alone. A digest cannot be repaired around.
    """
    return hashlib.sha256(
        record.replace("\r\n", "\n").replace("\r", "\n").rstrip().encode("utf-8")
    ).hexdigest()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# --- check A ---------------------------------------------------------------------------------
# SCOPED TO ONE TABLE, by its header. SOURCE_RECONCILIATION.md holds five tables and the first
# version of this reader was scoped to none of them: it matched 38 rows across the whole file, of
# which 36 are source inventories and finding lists that assert nothing about a published summary.
# The corpus floor is what exposed that, which is the argument for having one. The sibling guard
# tests/test_btg1_matrix_reconciles.py learned the same lesson the same way and says so in its own
# docstring: a reader scoped to nothing reads everything.
TABLE_HEADER = "| Reconciled claim | Published summary | Status | Owner |"
TABLE_ROW = re.compile(r"^\|(?!\s*[-: ]+\|).*\|\s*$", re.M)
BACKTICKED = re.compile(r"`([^`]+)`")

# A row whose status names it as `Updated` has already been reconciled and makes no live claim that
# a file still holds a string. Matched on the whole bold run, not on its first word: the first-word
# comparison is what `**Deferred (closed by b93c701)**` walked through twice.
UPDATED_STATUS = re.compile(r"\*\*[^*]*\bUpdated\b[^*]*\*\*")

# The reconciliation table's data rows. Exactly 3 today: one `Updated in this change` naming
# index.html in prose, and the two `Deferred` rows registered below. Asserted as an equality rather
# than a floor, so a row ADDED to the table is noticed as loudly as one removed - a new reconciled
# claim is exactly the thing this module should be made to read.
RECONCILIATION_ROWS = 3

# Rows stale TODAY, keyed by the target string each says its files still contain - a label for the
# reader, since the assertion is the digest. `digest` is the SHA-256 of the row's exact text, so a
# repair in ANY wording forces the entry out; the row itself then supplies the files to check.
# Computed by running digest(), not written by hand. An entry may only LEAVE.
STALE_ROWS: dict[str, dict] = {
    "ADR-001…012": {
        "digest": "32fae731249eb043000f9116aaa7ae09f4ccfa84f7e8962c327842eeb1217b04",
        "why": ("closed by #35 in b93c701; docs/NEXT_STEPS.md now reads ADR-001…020, the same "
                "ellipsis notation with the number repaired, so the row's target is really gone"),
    },
    "G0…G8": {
        "digest": "afec2dc8bb35052eca71d6fc9a001685cd872ca88139235740d35c76e3dd24fb",
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

# Tickets section 14 cites as landed AND as outstanding, with the digests of the bullets that put
# them on each side. Registering the bullets by digest is what makes this a ratchet: repairing
# either bullet, in any wording, changes its digest and forces the entry out - and so does a THIRD
# bullet joining the argument, because the registered tuple is asserted as the exact set.
#
# Only #165. Bullet 5 writes its range as "[#165](…) to [#170](…)", so #169 - which bullet 1 does
# credit to WP-055 - never appears literally there and is not an intersection.
CONTRADICTED: dict[str, dict] = {
    "165": {
        "digests": (
            "a1e5ab6b5cb30cb40c4aea6407788ca3ec1a3b442ef58a8bf09feb4f0b3052a6",
            "d0998aaa07b2611e1651cc0991ab63c828c23cb848013de5f8109a53366d43af",
        ),
        "why": ("credited to WP-051 in bullet 1 as a landed pointer, and listed in bullet 5 among "
                "the manuals that have not moved; the two bullets are four apart in one section"),
    },
}

# Bullets in section 14 matching neither vocabulary. Registered so that new wording surfaces here
# rather than being silently bucketed, which is how an earlier version let bullet 4's ownership
# sentence keep entry 165 satisfied.
UNCLASSIFIED_BULLETS = 2


def reconciliation_table() -> list[str]:
    """The data rows of the reconciliation table, and no other table's.

    Empty when the file or the header is missing, rather than raising, so that test_anchors_exist
    owns the diagnosis. tests/test_btg1_matrix_reconciles.matrix_rows() is the house pattern.
    """
    if not RECONCILIATION.is_file():
        return []
    text = read(RECONCILIATION)
    if TABLE_HEADER not in text:
        return []
    rest = text.split(TABLE_HEADER, 1)[1]
    end = rest.find("\n\n")
    body = rest[: end if end != -1 else len(rest)]
    return TABLE_ROW.findall(body)


def reconciliation_rows() -> list[dict]:
    """Those rows naming files and a target string, each carrying the digest of its own text.

    `live` is False for a row whose status says the summary was already updated; such a row makes
    no claim that a file still holds anything.
    """
    out = []
    for row in reconciliation_table():
        for cell in (c.strip() for c in row.strip().strip("|").split("|")):
            ticks = BACKTICKED.findall(cell)
            if len(ticks) < 2:
                continue
            files = tuple(t.split(":")[0] for t in ticks[:-1] if "/" in t or t.endswith(".html"))
            if files:
                out.append({
                    "files": files,
                    "target": ticks[-1],
                    "digest": digest(row),
                    "live": not UPDATED_STATUS.search(row),
                })
                break
    return out


def section_14() -> str:
    """Section 14's text, or "" when its heading is missing. See reconciliation_table()."""
    if not PLAN.is_file():
        return ""
    text = read(PLAN)
    if SECTION_14 not in text:
        return ""
    start = text.index(SECTION_14)
    nxt = text.find("\n## ", start + 1)
    return text[start: nxt if nxt != -1 else len(text)]


def bullets() -> list[str]:
    return section_14().split("\n- ")[1:]


def classify() -> tuple[set[str], set[str], list[str]]:
    """(landed, outstanding, unclassified). Membership in the two sets is INDEPENDENT.

    Not `if COMPLETION / elif DEFERRAL`. First-match-wins meant a bullet carrying both vocabularies
    joined one set only and could never intersect with itself, so a single bullet calling one ticket
    both landed and outstanding - which is a reviewer's control, and a shape a real editor would
    write - was invisible.
    """
    landed: set[str] = set()
    outstanding: set[str] = set()
    unclassified: list[str] = []
    for bullet in bullets():
        nums = set(ISSUE.findall(bullet))
        matched = False
        if COMPLETION.search(bullet):
            landed |= nums
            matched = True
        if DEFERRAL.search(bullet):
            outstanding |= nums
            matched = True
        if not matched:
            unclassified.append(bullet.strip()[:80])
    return landed, outstanding, unclassified


def contradictions() -> set[str]:
    landed, outstanding, _ = classify()
    return landed & outstanding


def bullet_digests(number: str) -> tuple[str, ...]:
    """The digests of the classified bullets citing a ticket - the record of the contradiction."""
    return tuple(sorted(
        digest(bullet) for bullet in bullets()
        if number in set(ISSUE.findall(bullet))
        and (COMPLETION.search(bullet) or DEFERRAL.search(bullet))
    ))


class TestAnchorsExist(unittest.TestCase):
    """A reader scoped to nothing reads everything, and a floor is not the same as non-empty."""

    def test_anchors_exist(self) -> None:
        self.assertTrue(RECONCILIATION.is_file(), RECONCILIATION)
        self.assertTrue(PLAN.is_file(), PLAN)
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
        """The registered ROW is still present byte for byte, and its defect is still real.

        Two-sided. The digest is the ratchet: a row repaired in any wording - a status annotated
        inside or outside its bold run, a file dropped, the row repointed, the row deleted - no
        longer hashes to its registration and the entry is forced out. The second half then reads
        THE FILES THE ROW NAMES, never the registration, and asserts the string is still absent.
        """
        rows = {r["digest"]: r for r in reconciliation_rows()}
        for target, reg in STALE_ROWS.items():
            with self.subTest(target=target):
                self.assertIn(
                    reg["digest"], rows,
                    f"no reconciliation row now hashes to the text registered for {target!r}. The "
                    f"row was reworded, repointed, restatused or removed, so this registration no "
                    f"longer describes the repository. Registered because: {reg['why']}. Remove the "
                    f"entry from STALE_ROWS - do not re-hash it, which would ratchet nothing.")
                row = rows[reg["digest"]]
                self.assertEqual(
                    target, row["target"],
                    f"the row registered for {target!r} names {row['target']!r}; the label and the "
                    f"digest have come apart, so STALE_ROWS is mislabelled")
                self.assertTrue(row["files"], f"the row naming {target!r} names no file to check")
                for rel in row["files"]:
                    self.assertNotIn(
                        target, read(ROOT / rel),
                        f"{rel} now contains {target!r}, so the row naming it is no longer stale. "
                        f"Remove the entry from STALE_ROWS.")

    def test_no_unregistered_stale_rows(self) -> None:
        """Every other live row's target string is really in the files it names.

        Registered rows are skipped by DIGEST, so a registered row that is edited at all stops being
        skipped and is read here too. That is not double-counting: a row edited to annotate its
        `Deferred` status still tells a reader the string is there, and it is not.
        """
        registered = {reg["digest"] for reg in STALE_ROWS.values()}
        for row in reconciliation_rows():
            if row["digest"] in registered or not row["live"]:
                continue
            for rel in row["files"]:
                with self.subTest(file=rel, target=row["target"]):
                    path = ROOT / rel
                    self.assertTrue(path.is_file(), f"a live row names {rel}, which does not exist")
                    self.assertIn(
                        row["target"], read(path),
                        f"SOURCE_RECONCILIATION says {rel} still contains {row['target']!r}, and it "
                        f"does not. Either the repair landed and the row should say so, or the "
                        f"target is mistyped. This is the #347 defect, unregistered.")


class TestSection14Contradictions(unittest.TestCase):
    """Check B: one section calling a ticket both landed and outstanding."""

    def test_registered_contradictions_still_fail(self) -> None:
        """The ticket is still contradicted, and by exactly the bullets registered, byte for byte."""
        found = contradictions()
        for num, reg in CONTRADICTED.items():
            with self.subTest(ticket=num):
                self.assertIn(
                    num, found,
                    f"section 14 no longer cites #{num} as both landed and outstanding. Registered "
                    f"because: {reg['why']}. Remove this entry from CONTRADICTED.")
                self.assertEqual(
                    tuple(sorted(reg["digests"])), bullet_digests(num),
                    f"the bullets citing #{num} are no longer the bullets registered for it. One was "
                    f"reworded or removed, or a third has joined; either way the registration no "
                    f"longer describes the record. Registered because: {reg['why']}. Remove the "
                    f"entry from CONTRADICTED - do not re-hash it.")

    def test_no_unregistered_contradictions(self) -> None:
        extra = contradictions() - set(CONTRADICTED)
        self.assertFalse(
            extra,
            f"section 14 cites {sorted('#' + n for n in extra)} as both landed and outstanding. A "
            f"section titled 'What this document does not yet carry' cannot also credit the same "
            f"ticket as carried. This is the #343 defect, unregistered.")

    def test_every_bullet_is_classified(self) -> None:
        """A bullet neither vocabulary recognises joins no set, and its count is registered.

        An earlier version had no third bucket: anything unmatched became 'outstanding', so an
        ownership sentence propped up a contradiction that had actually been repaired. The count is
        this module's own honesty check - detection of NEW contradictions is heuristic, and this is
        the number that says how much prose the heuristic cannot read.
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
            with self.subTest(target=target):
                self.assertGreater(len(reg["why"].split()), 12,
                                   f"STALE_ROWS[{target!r}] has no real reason; a registry entry "
                                   f"without one is a suppression")
                self.assertRegex(reg["digest"], r"^[0-9a-f]{64}$",
                                 f"STALE_ROWS[{target!r}] registers no SHA-256")
        for num, reg in CONTRADICTED.items():
            with self.subTest(ticket=num):
                self.assertGreater(len(reg["why"].split()), 12,
                                   f"CONTRADICTED[{num!r}] has no real reason")
                self.assertTrue(reg["digests"], f"CONTRADICTED[{num!r}] registers no bullet")
                for one in reg["digests"]:
                    self.assertRegex(one, r"^[0-9a-f]{64}$",
                                     f"CONTRADICTED[{num!r}] registers a malformed SHA-256")


if __name__ == "__main__":
    unittest.main()
