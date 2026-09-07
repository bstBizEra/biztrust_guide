#!/usr/bin/env python3
"""Every ADR a document cites exists in the register, with the status it claims.

`docs/architecture/ADR_REGISTER.md` is the single place an ADR's status is decided: its own header says
`TRACKING REGISTER - NO ADR ACCEPTED BY THIS FILE`, and that an ADR moves from `DRAFT_REQUIRED` only
through the authority and review process of its Work Package. Until this test, nothing read it. Every
design in the P0 pack names ADRs and their status in prose, the pack's README makes "a technology with
no ADR row is a question, not a candidate" a rule that reviews enforced by hand, and a design could have
cited an ADR that does not exist, or called one `ACCEPTED`, with nothing to notice.

**The vocabulary is the register's, read from the register.** Its "Status vocabulary" block lists the
eight words an ADR's status may be, and this test reads that block rather than carrying a list of its
own. A hand-kept list was tried first and was wrong twice over: it omitted `IN_REVIEW` and `DEPRECATED`,
so a document claiming either would have been read as making no claim at all, and it included `DRAFT`,
which belongs to the design pack's vocabulary and is not a status an ADR may hold.

**How a claim is read.** The corpus writes an identifier, an optional gloss, then a backticked status:
"ADR-002 Logto as identity infrastructure, `DRAFT_REQUIRED`", and sometimes one status for two
identifiers, "ADR-002 and ADR-003, `DRAFT_REQUIRED`". So a claim is read **forward** from each
identifier to the first backticked status inside the same clause. Reading backward from the status was
tried first and silently missed four claims whose identifier sat further back than the window; forward
is the direction the grammar runs.

A clause ends at `;`, `|`, a newline, or a full stop **that ends a sentence** — a full stop followed by
whitespace or the end of the text. Any full stop was tried first and truncated real claims: the one in
"ADR-005 OpenAPI 3.2 for contract-first HTTP APIs, `DRAFT_REQUIRED`" ended the clause inside a version
number, and the corpus is full of version numbers and file names. Those claims were then never checked,
which is the quietest way for a guard like this to be useless.

Identifiers are matched as `ADR-` and exactly three digits with a word boundary, so a four-digit
identifier in someone else's example, such as the `ADR-0007` in `docs/agents/domain.md`, is not read as
`ADR-000`. That file is outside this corpus anyway: only Markdown under `docs/architecture/` is read,
which is where this repository's normative documents live.

A status this test finds disagreeing is a defect in the document, not a value to copy from it. The
register decides; a document repeats.

Positive controls: the register must yield its vocabulary and twenty rows, and the corpus must yield at
least eighteen distinct identifiers and a hundred claims against the hundred and sixteen it holds today.
Those floors are set close to the real figures on purpose: a floor low enough to survive one document
failing to parse is a floor that guards nothing.

Negative controls (run 2026-09-07 under WP-100, on the files and on copies):
  * a citation of an ADR with no register row  -> test_every_cited_adr_exists FAILS
  * a claim of ACCEPTED where the register says DRAFT_REQUIRED -> test_every_claimed_status_is_the_registers FAILS
  * a register identifier written twice        -> test_the_register_is_well_formed FAILS
  * a status in the register's vocabulary but not the test's   -> impossible; the vocabulary is the register's
  * a full stop inside a version number or a file name         -> must not end a clause, held below

The site's HTML pages are held to the same register by tests/test_html_adr_citations.py
(WP-107, #313). Their grammar is not this one's: the pages state statuses in aggregate, by
range and by count, rather than after each identifier, so the two readers are separate.

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "docs" / "architecture"
REGISTER = ARCH / "ADR_REGISTER.md"

IDENTIFIER = re.compile(r"\bADR-\d{3}\b")
REGISTER_ROW = re.compile(r"^\| (ADR-\d{3}) \|[^|]*\| `([A-Z_0-9]+)` \|", re.M)
VOCABULARY_WORD = re.compile(r"^([A-Z_0-9]+)$", re.M)
# A clause ends at a semicolon, a pipe, a newline, or a full stop that ends a sentence. Not at the
# full stop in `0.3` or in `P0.12-secrets-and-configuration.md`.
CLAUSE_END = re.compile(r"[;|\n]|\.(?=\s|$)")


def register_text() -> str:
    return REGISTER.read_text(encoding="utf-8")


def vocabulary(text: str) -> list[str]:
    """The status words the register's own 'Status vocabulary' block lists."""
    block = text.split("## Status vocabulary", 1)[1].split("```", 2)[1]
    return VOCABULARY_WORD.findall(block)


def register(text: str) -> dict[str, str]:
    """The register's rows: identifier -> the status it decides."""
    return {m.group(1): m.group(2) for m in REGISTER_ROW.finditer(text)}


def register_identifiers(text: str) -> list[str]:
    """The register's identifiers in file order, duplicates kept, so a repeat can be seen."""
    return [m.group(1) for m in REGISTER_ROW.finditer(text)]


def claims(text: str, statuses: list[str]) -> list[tuple[str, str, str]]:
    """Each (identifier, claimed status, the clause it was read from) in this document."""
    status_re = re.compile(rf"`({'|'.join(statuses)})`")
    found = []
    for m in IDENTIFIER.finditer(text):
        clause = CLAUSE_END.split(text[m.end():], maxsplit=1)[0]
        s = status_re.search(clause)
        if s:
            found.append((m.group(0), s.group(1), (m.group(0) + clause).strip()))
    return found


def citations(text: str) -> set[str]:
    return set(IDENTIFIER.findall(text))


def corpus() -> list[Path]:
    """Every normative Markdown document that may cite an ADR, the register itself excepted."""
    return sorted(p for p in ARCH.rglob("*.md") if p != REGISTER)


class TestTheReadersFindSomething(unittest.TestCase):
    """Positive controls. A parse that quietly stops working looks exactly like a passing test."""

    def test_the_register_yields_its_vocabulary(self) -> None:
        words = vocabulary(register_text())
        self.assertIn("DRAFT_REQUIRED", words)
        self.assertIn("ACCEPTED", words)
        self.assertGreaterEqual(len(words), 5, "the register's status vocabulary block no longer yields its words")

    def test_the_register_yields_its_rows(self) -> None:
        text = register_text()
        reg = register(text)
        self.assertEqual(20, len(reg), "the register no longer yields twenty rows; re-derive this test")
        unknown = set(reg.values()) - set(vocabulary(text))
        self.assertFalse(unknown, f"the register uses a status its own vocabulary block does not list: {sorted(unknown)}")

    def test_the_corpus_cites_adrs(self) -> None:
        cited = set().union(*(citations(p.read_text(encoding="utf-8")) for p in corpus()))
        self.assertGreaterEqual(len(cited), 18, f"only {len(cited)} distinct ADRs cited; the reader has broken")

    def test_the_corpus_claims_statuses(self) -> None:
        words = vocabulary(register_text())
        n = sum(len(claims(p.read_text(encoding="utf-8"), words)) for p in corpus())
        self.assertGreaterEqual(n, 100, f"only {n} status claims read, against 116 in the corpus; the reader has broken")


class TestTheReaderCanFail(unittest.TestCase):
    """Negative controls, on copies and on real corpus sentences. A guard that cannot fail guards nothing."""

    def setUp(self) -> None:
        self.words = vocabulary(register_text())

    def test_an_unregistered_citation_is_seen(self) -> None:
        self.assertNotIn("ADR-021", register(register_text()))
        self.assertIn("ADR-021", citations("this design depends on ADR-021 for its shape"))

    def test_a_wrong_status_claim_is_seen(self) -> None:
        read = claims("The design rests on ADR-001 modular monolith, `ACCEPTED`, and proceeds.", self.words)
        self.assertEqual([("ADR-001", "ACCEPTED")], [(a, s) for a, s, _ in read])
        self.assertNotEqual("ACCEPTED", register(register_text())["ADR-001"],
                            "ADR-001 is accepted in the register; re-derive this control")

    def test_a_duplicated_register_identifier_is_seen(self) -> None:
        doubled = register_text() + "\n| ADR-001 | A second row | `ACCEPTED` | Nothing |\n"
        ids = register_identifiers(doubled)
        self.assertNotEqual(len(ids), len(set(ids)), "a repeated register row was not seen")

    def test_a_status_from_another_sentence_is_not_claimed(self) -> None:
        text = "The adapter boundary is ADR-009. A different design is `PROPOSED`."
        self.assertEqual([], claims(text, self.words), "a status was attributed across a sentence boundary")

    def test_a_full_stop_inside_a_version_does_not_end_the_clause(self) -> None:
        text = "ADR-005 OpenAPI 3.2 for contract-first HTTP APIs, `DRAFT_REQUIRED`, which decides the shape."
        self.assertEqual([("ADR-005", "DRAFT_REQUIRED")], [(a, s) for a, s, _ in claims(text, self.words)],
                         "a full stop inside a version number ended the clause, so the claim went unchecked")

    def test_a_full_stop_inside_a_file_name_does_not_end_the_clause(self) -> None:
        text = "See P0.12-secrets-and-configuration.md for ADR-004 shared PostgreSQL with RLS, `DRAFT_REQUIRED`."
        self.assertEqual([("ADR-004", "DRAFT_REQUIRED")], [(a, s) for a, s, _ in claims(text, self.words)],
                         "a full stop inside a file name ended the clause")

    def test_two_identifiers_may_share_one_status(self) -> None:
        text = "The design names ADR-002 and ADR-003, `DRAFT_REQUIRED`, as dependencies."
        self.assertEqual([("ADR-002", "DRAFT_REQUIRED"), ("ADR-003", "DRAFT_REQUIRED")],
                         [(a, s) for a, s, _ in claims(text, self.words)])


class TestTheCorpusAgreesWithTheRegister(unittest.TestCase):
    def test_the_register_is_well_formed(self) -> None:
        ids = register_identifiers(register_text())
        self.assertEqual(len(ids), len(set(ids)), f"the register lists an identifier twice: {sorted(ids)}")
        numbers = sorted(int(i.removeprefix("ADR-")) for i in ids)
        self.assertEqual(list(range(1, len(numbers) + 1)), numbers,
                         "the register's identifiers are not ADR-001 upwards without a gap; a citation could "
                         "resolve to a row that was renumbered")

    def test_every_cited_adr_exists(self) -> None:
        reg = register(register_text())
        for p in corpus():
            with self.subTest(document=p.name):
                for adr in sorted(citations(p.read_text(encoding="utf-8"))):
                    self.assertIn(adr, reg, f"{p.name} cites {adr}, which has no row in the ADR register. "
                                            f"A decision with no row is not a decision.")

    def test_every_claimed_status_is_the_registers(self) -> None:
        text = register_text()
        reg, words = register(text), vocabulary(text)
        for p in corpus():
            with self.subTest(document=p.name):
                for adr, claimed, clause in claims(p.read_text(encoding="utf-8"), words):
                    self.assertIn(adr, reg, f"{p.name} claims a status for {adr}, which has no register row")
                    self.assertEqual(reg[adr], claimed,
                                     f"{p.name} says {adr} is `{claimed}`; the register says `{reg[adr]}`. "
                                     f"The register decides, so the document is what changes. Read: {clause[:120]!r}")


if __name__ == "__main__":
    unittest.main()
