#!/usr/bin/env python3
"""The site's pages are held to the ADR register, as the Markdown corpus already is.

`tests/test_adr_citations.py` (WP-100) holds every ADR citation in Markdown under
`docs/architecture/` to `docs/architecture/ADR_REGISTER.md`. It reads no HTML, and said so as
declared non-coverage. This is that gap closed (#313).

It is the more public half of the corpus: thirteen pages carry a hundred and ninety citations,
nine of which sit only inside an href and are read from the raw source rather than the prose. A
design read by five people may misstate an ADR's status; a landing page misstates it to a review
seat, a broker or a prospective tenant.

THE GRAMMAR IS NOT MARKDOWN'S, and the ticket asked for it to be read rather than assumed. The
Markdown corpus writes a backticked status straight after the identifier. The pages almost never
do: across a hundred and ninety citations there are FIVE status claims, and every one is an
aggregate rather than a per-identifier statement. So this module reads what the pages actually
say:

  Citation   `ADR-NNN` anywhere on a page. Every one must have a register row.
  Set claim  "ADR-001 to ADR-012, ADR-015, ADR-020, marked DRAFT_REQUIRED" - a set of
             identifiers and ranges, then the word "marked", then a status. Every ADR in the set
             must hold that status. Two of these, both on landing/architecture.html.
  Count      "fourteen read DRAFT_REQUIRED", "six of them are BLOCKED_BY_S01" - a number word and
             a status. The register's count at that status must be the number. Three of these.

A STATUS WORD NEAR AN ADR PLAYS THREE ROLES, and only one of them is a claim. Reading the pages
first is what surfaced the other two, and a reader that missed the distinction would have
reported two defects that are not there:

 1. A CLAIM about the register's current state - the five above, and what this module checks.
 2. AN ENTRY CRITERION, a required future state. `phases/p0.html` carries, under a heading
    "Entry criteria", an article headed "The ADRs P0 builds on are accepted", whose body reads
    "ADR-001 ... and ADR-005 (contract-first) - accepted per the register, not `DRAFT_REQUIRED`".
    That is a condition for starting P0, and it names the CURRENT status as the thing that must
    change. It is the most careful phrasing on the site and it is not a claim; a reader treating
    it as one would report that the page says five ADRs are accepted when it says the opposite.
 3. A DESIGN'S status, not an ADR's. `phases/p0.html` writes "(design, IN_REVIEW)" thirteen
    times, since WP-104. Different subject entirely.

Roles 2 and 3 are excluded by construction: the count reader requires a status in the register's
own SCREAMING_CASE and skips a window containing "design," or an identifier, which also keeps it
away from ordinary English. "Twenty decisions registered, none accepted" is prose about the
register and not a claim that twenty ADRs are ACCEPTED; the lowercase is what says so.

WHAT THIS DOES NOT DO. It does not read a count written in DIGITS. Review evaded the reader with
"3 read DRAFT_REQUIRED"; admitting digits then manufactured three claims out of stray numbers -
an issue reference read as "15 ADRs are BLOCKED_BY_S01", a section number as "9 are
DRAFT_REQUIRED" - so the evasion is declared instead. Every count on these pages is spelt out.
It does not read prose paraphrases of a count - "Fourteen require a
draft", "Six wait on the first slice of the freeze" - both of which sit beside the numeric claims
it does read, on the same page, and both of which are true. It strips tags before reading, so it
does not know which element a claim sits in, and it cannot tell a heading from a caption. It
checks what a page says against the register; it does not check that the register is right.

Positive controls, by name and not by count: the pages carrying citations, and the pages carrying
each kind of claim, are asserted as sets. WP-105 learned that a threshold sitting on the tree's
own value is not a control at all.

No page's content is changed by this package. The ticket's instruction was that a disagreement
found is reported on #313 first, because the page may be wrong or the register may have moved
under it - and none was found: all five claims agree with the register, and all hundred and
ninety citations have a row.

(An earlier version of this docstring claimed the same of a hundred and ninety while its reader
examined a hundred and eighty-one, because it read citations from the tag-stripped prose. Nine
were never looked at. Corrected, and the reader now takes them from the source.)

Negative controls (run 2026-09-07 under WP-107, each on a copied tree, run as
`unittest discover -s tests -p test_html_adr_citations.py` from that tree's root):
  * A page cites ADR-021, which has no register row  -> test_every_cited_adr_has_a_register_row
  * A set claim gains an ADR at another status       -> test_every_set_claim_matches_the_register
  * A set claim's status is changed                  -> test_every_set_claim_matches_the_register
  * A count claim's number is changed                -> test_every_count_claim_matches_the_register
  * A page stops citing any ADR                      -> test_the_same_pages_cite_adrs
  * A status appears near an identifier anywhere new -> test_every_status_reading_is_one_of_the_known_ones
  * A set claim written "flagged" rather than "marked" -> test_every_set_claim_matches_the_register
  * An ADR cited only inside an href                 -> test_every_cited_adr_has_a_register_row
  * The register's status column is emptied          -> not isolated: the register is the corpus

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import html as html_mod
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs" / "architecture" / "ADR_REGISTER.md"
SKIP = {".git", "_site", "node_modules"}

ADR = re.compile(r"ADR-\d{3}")

# The register's own vocabulary, read from the register rather than listed here, so the two
# cannot drift. tests/test_adr_citations.py reads it the same way.
VOCABULARY_HEADING = "## Status vocabulary"

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}

# Pages that cite at least one ADR, and pages carrying each kind of claim. Asserted by name.
CITING_PAGES = (
    "index.html", "landing/architecture.html", "landing/index.html", "landing/operations.html",
    "landing/p0.html", "landing/p1.html", "landing/p2.html", "landing/team.html",
    "phases/overview.html", "phases/p0.html", "phases/p1.html", "phases/p2.html",
    "reference/continuous-operations.html",
)
SET_CLAIM_PAGES = ("landing/architecture.html",)

# Every place a status sits within forty characters of an identifier, and what kind of statement
# it is. Only a person can tell an assertion from a condition, so the kind is recorded here and
# never inferred. A reading that is not on this list fails until someone classifies it.
KNOWN_STATUS_READINGS = (
    ("landing/architecture.html", "ADR-001", "DRAFT_REQUIRED", "set claim"),
    ("landing/architecture.html", "ADR-013", "BLOCKED_BY_S01", "set claim"),
    # A halt condition, and a disjunction over two ADRs and two statuses: it asserts nothing.
    ("phases/p1.html", "ADR-013", "BLOCKED_BY_S01", "condition"),
)
KIND_OF = {(page, adr, status): kind for page, adr, status, kind in KNOWN_STATUS_READINGS}
COUNT_CLAIM_PAGES = ("index.html", "landing/architecture.html")


# A vocabulary line, by the same rule tests/test_adr_citations.py uses. Taking any non-empty line
# instead read the fence's own language tag - ```text - as a status word, which is how a page
# with a "5" near the word "text" became a claim that five ADRs are "text". The sibling never had
# this bug; matching its idiom is both the fix and the answer to having duplicated its parser badly.
VOCABULARY_WORD = re.compile(r"^([A-Z_0-9]+)$", re.M)


def vocabulary() -> tuple[str, ...]:
    text = REGISTER.read_text(encoding="utf-8")
    block = text.split(VOCABULARY_HEADING, 1)[1].split("```", 2)[1]
    return tuple(VOCABULARY_WORD.findall(block))


def register() -> dict[str, str]:
    """Every ADR row's status, by identifier."""
    words = set(vocabulary())
    found: dict[str, str] = {}
    for line in REGISTER.read_text(encoding="utf-8").splitlines():
        named = re.match(r"^\|\s*`?(ADR-\d{3})`?\s*\|", line)
        if not named:
            continue
        stated = [c.strip().strip("`") for c in line.split("|")]
        holds = [c for c in stated if c in words]
        if holds:
            found[named.group(1)] = holds[0]
    return found


def pages() -> list[Path]:
    return sorted(
        p for p in ROOT.rglob("*.html")
        if p.is_file() and not SKIP.intersection(p.relative_to(ROOT).parts)
    )


def readable(page: Path) -> str:
    """A page's PROSE: tags removed, entities resolved, whitespace flattened.

    Claims are read from this, because a claim is a sentence. Citations are not: see cited().
    """
    text = re.sub(r"<[^>]*>", " ", page.read_text(encoding="utf-8"))
    return re.sub(r"\s+", " ", html_mod.unescape(text))


def cited(page: Path) -> set[str]:
    """Every ADR a page names, including inside an attribute.

    Read from the raw source rather than the prose. Nine of the hundred and ninety citations live
    only inside an href - four on phases/p1.html and five on phases/p2.html - and an earlier
    version read the prose for both jobs, so it examined a hundred and eighty-one and its
    docstring said it had examined all of them.
    """
    return set(ADR.findall(page.read_text(encoding="utf-8")))


def spread(phrase: str) -> set[str]:
    """The identifiers a phrase names: 'ADR-001 to ADR-003, ADR-009' is three plus one."""
    found: set[str] = set()
    ranges = re.compile(r"ADR-(\d{3})\s*(?:to|through|-|–)\s*ADR-(\d{3})")
    for run in ranges.finditer(phrase):
        found |= {f"ADR-{n:03d}" for n in range(int(run.group(1)), int(run.group(2)) + 1)}
    found |= set(ADR.findall(ranges.sub("", phrase)))
    return found


def set_claims() -> list[tuple[Path, set[str], str]]:
    """(page, the identifiers named, the status claimed) for every "... marked STATUS" claim."""
    words = "|".join(vocabulary())
    # "marked" was the only verb read, and the identifier run was capped at twelve chunks, so an
    # author writing "flagged" - or enumerating fourteen identifiers rather than using a range -
    # made a claim this module could not see. Both were found by review.
    pattern = re.compile(
        rf"((?:ADR-\d{{3}}[^.]{{0,10}}){{1,}}?)\s*,?\s*(?:marked|flagged|listed as|recorded as)\s+({words})\b"
    )
    return [
        (page, spread(m.group(1)), m.group(2))
        for page in pages()
        for m in pattern.finditer(readable(page))
    ]


def count_claims() -> list[tuple[Path, int, str]]:
    """(page, the number claimed, the status) for every "<number> ... STATUS" claim.

    The status must be in the register's own case, which is what keeps ordinary English out: the
    same page writes "Twenty decisions registered, none accepted", which is prose about the
    register and not a claim that twenty ADRs are ACCEPTED. The window may not contain "design,"
    - a design's status is not an ADR's - nor an identifier, which would make it a set claim.
    """
    words = "|".join(vocabulary())
    numbers = "|".join(f"[{w[0].upper()}{w[0]}]{w[1:]}" for w in NUMBER_WORDS)
    # Number WORDS only. Review evaded this with "3 read DRAFT_REQUIRED", so digits were tried -
    # and they manufactured three claims out of stray numbers: an issue reference on index.html
    # read as "15 ADRs are BLOCKED_BY_S01", a section number on landing/architecture.html as
    # "9 are DRAFT_REQUIRED". The evasion is real and is DECLARED rather than closed, for the
    # reason WP-105 declined to widen its trigger: a reader that invents claims is worse than one
    # that reads fewer, and every count on these pages is spelt out in words.
    pattern = re.compile(rf"\b({numbers})\b(?![’']s)(?:(?!ADR-|design,)[^.]){{0,70}}?\b({words})\b")
    return [
        (page, NUMBER_WORDS[m.group(1).lower()], m.group(2))
        for page in pages()
        for m in pattern.finditer(readable(page))
    ]


def relative(page: Path) -> str:
    return page.relative_to(ROOT).as_posix()


def status_readings() -> list[tuple[Path, str, str, str]]:
    """(page, identifier, status, kind) for every status sitting near an identifier.

    Forty characters, not crossing a sentence end or a table-cell boundary. The kind is decided
    by the classification below, never by the reader: telling an assertion from a condition is
    not something proximity can do.
    """
    words = "|".join(vocabulary())
    pattern = re.compile(rf"(ADR-\d{{3}})((?:(?![.|])[^\n]){{0,40}}?)\b({words})\b")
    found = []
    for page in pages():
        for m in pattern.finditer(readable(page)):
            kind = KIND_OF.get((relative(page), m.group(1), m.group(3)), "unclassified")
            found.append((page, m.group(1), m.group(3), kind))
    return found


class TestTheReaderReadsSomething(unittest.TestCase):
    """Positive controls, asserted as named sets."""

    def test_the_register_is_readable(self) -> None:
        rows = register()
        self.assertEqual(20, len(rows), "the register no longer holds twenty ADR rows")
        self.assertGreaterEqual(len(vocabulary()), 6, "the register's status vocabulary is unreadable")

    def test_the_same_pages_cite_adrs(self) -> None:
        citing = tuple(relative(p) for p in pages() if cited(p))
        self.assertEqual(
            tuple(sorted(CITING_PAGES)), tuple(sorted(citing)),
            "the set of pages citing an ADR has changed. One that has gone may have lost its "
            "citations rather than its subject; one that has appeared needs adding to "
            "CITING_PAGES deliberately.",
        )

    def test_the_same_pages_make_claims(self) -> None:
        self.assertEqual(
            tuple(sorted(SET_CLAIM_PAGES)), tuple(sorted({relative(p) for p, _, _ in set_claims()})),
            "the set of pages making a 'marked STATUS' claim has changed",
        )
        self.assertEqual(
            tuple(sorted(COUNT_CLAIM_PAGES)), tuple(sorted({relative(p) for p, _, _ in count_claims()})),
            "the set of pages making a counted status claim has changed",
        )


class TestEveryStatusReadingIsClassified(unittest.TestCase):
    """Every place a status word sits near an identifier is known, and says which kind it is.

    Review's bottom line was that the status rule is near-vacuous: it reads two sentences, on one
    page, gated on one English word, and cannot detect the day a per-identifier status appears.
    That is true, and a proximity reader is NOT the answer - reading the pages is what showed why.
    Of the three places an identifier sits within forty characters of a status in the register's
    own case, two are the set claims and the third is this:

        phases/p1.html, under "Halt / Stop conditions":
        "ADR-013 or ADR-017 is still BLOCKED_BY_S01 or DRAFT_REQUIRED"

    A halt condition, and a disjunction: it asserts neither status of either ADR. Together with
    the entry criterion on phases/p0.html, the pattern is that this site states statuses mostly in
    CONDITIONALS - what must be true to start, what must not be true to continue - and only the
    "marked" form asserts anything. A reader that took proximity for assertion would manufacture
    claims out of both.

    So the rule is a ratchet instead: every reading is enumerated and classified, and a FOURTH one
    fails until a human says which kind it is. That turns "cannot detect the day one appears" into
    "fails the day one appears", without inventing a claim from a condition.
    """

    def test_every_status_reading_is_one_of_the_known_ones(self) -> None:
        readings = {(relative(p), a, st, kind) for p, a, st, kind in status_readings()}
        self.assertEqual(
            set(KNOWN_STATUS_READINGS), readings,
            "a status now sits near an ADR identifier somewhere this module has not classified. "
            "It is an assertion, a condition or a set claim, and only a person can say which; "
            "add it to KNOWN_STATUS_READINGS with its kind, or correct the page. See #313.",
        )

    def test_every_asserted_reading_matches_the_register(self) -> None:
        """A reading classified as an assertion is checked; a condition is not, and must not be."""
        rows = register()
        asserted = [r for r in KNOWN_STATUS_READINGS if r[3] == "assertion"]
        for page, adr, status, _kind in asserted:
            with self.subTest(page=page, adr=adr):
                self.assertEqual(status, rows.get(adr), f"{page} asserts {adr} is {status}")
        self.assertNotEqual(
            [], [r for r in KNOWN_STATUS_READINGS if r[3] == "condition"],
            "no reading is classified as a condition; the classification has stopped distinguishing",
        )


class TestThePagesAgreeWithTheRegister(unittest.TestCase):
    def test_every_cited_adr_has_a_register_row(self) -> None:
        rows = register()
        for page in pages():
            names = sorted(cited(page))
            if not names:
                continue
            with self.subTest(page=relative(page)):
                missing = [a for a in names if a not in rows]
                self.assertEqual([], missing, f"{relative(page)} cites {missing}, which the register has no row for")

    def test_every_set_claim_matches_the_register(self) -> None:
        rows = register()
        claims = set_claims()
        self.assertNotEqual([], claims, "no set claim was read; this rule checks nothing")
        for page, identifiers, status in claims:
            with self.subTest(page=relative(page), status=status):
                self.assertNotEqual(set(), identifiers, "a set claim naming no ADR")
                disagreeing = {
                    a: rows.get(a, "no register row") for a in sorted(identifiers) if rows.get(a) != status
                }
                self.assertEqual(
                    {}, disagreeing,
                    f"{relative(page)} says {sorted(identifiers)} are {status}; the register says "
                    f"{disagreeing}. The page may be wrong or the register may have moved under "
                    f"it - report it on #313 before changing either.",
                )

    def test_every_count_claim_matches_the_register(self) -> None:
        rows = register()
        claims = count_claims()
        self.assertNotEqual([], claims, "no count claim was read; this rule checks nothing")
        for page, number, status in claims:
            with self.subTest(page=relative(page), status=status):
                holding = sum(1 for s in rows.values() if s == status)
                self.assertEqual(
                    holding, number,
                    f"{relative(page)} says {number} ADRs are {status}; the register holds "
                    f"{holding}. Report it on #313 before changing either.",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
