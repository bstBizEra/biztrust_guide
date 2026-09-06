#!/usr/bin/env python3
"""Every ADR a document cites exists in the register, with the status it claims.

`docs/architecture/ADR_REGISTER.md` is the single place an ADR's status is decided: its own header says
`TRACKING REGISTER - NO ADR ACCEPTED BY THIS FILE`, and that an ADR moves from `DRAFT_REQUIRED` only
through the authority and review process of its Work Package. Until this test, nothing read it. Every
design in the P0 pack names ADRs and their status in prose, the pack's README makes "a technology with
no ADR row is a question, not a candidate" a rule that reviews enforced by hand, and a design could have
cited an ADR that does not exist, or called one `ACCEPTED`, with nothing to notice.

What a citation looks like, and how it is read. The corpus writes an identifier, an optional gloss, then
a backticked status: "ADR-002 Logto as identity infrastructure, `DRAFT_REQUIRED`", and sometimes one
status for two identifiers, "ADR-002 and ADR-003, `DRAFT_REQUIRED`". So a claim is read **forward** from
each identifier to the first backticked status inside the same clause, a clause ending at `;`, `|`, `.`
or a newline. Reading backward from the status was tried first and silently missed four claims whose
identifier sat further back than the window; forward is the direction the grammar runs.

Identifiers are matched as `ADR-` and exactly three digits with a word boundary, so a four-digit
identifier in someone else's example, such as the `ADR-0007` in `docs/agents/domain.md`, is not read as
`ADR-000`. That file is outside this corpus anyway: only Markdown under `docs/architecture/` is read,
which is where this repository's normative documents live.

A status this test finds disagreeing is a defect in the document, not a value to copy from it. The
register decides; a document repeats.

Positive controls: the register must yield twenty rows and every one of its statuses; the corpus must
yield a substantial number of citations and claims. Without these the comparisons pass over nothing,
which is what a parse that quietly stops working looks like.

Negative controls (run 2026-09-07 under WP-100, on in-memory copies):
  * a citation of an ADR with no register row  -> test_every_cited_adr_exists FAILS
  * a claim of ACCEPTED where the register says DRAFT_REQUIRED -> test_every_claimed_status_is_the_registers FAILS
  * a register identifier written twice        -> test_the_register_is_well_formed FAILS
  * a claim whose status is not in the register's vocabulary   -> read as no claim, held below

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "docs" / "architecture"
REGISTER = ARCH / "ADR_REGISTER.md"

STATUSES = ("DRAFT_REQUIRED", "BLOCKED_BY_S01", "ACCEPTED", "PROPOSED", "DRAFT", "REJECTED", "SUPERSEDED")
IDENTIFIER = re.compile(r"\bADR-\d{3}\b")
STATUS = re.compile(rf"`({'|'.join(STATUSES)})`")
REGISTER_ROW = re.compile(r"^\| (ADR-\d{3}) \|[^|]*\| `([A-Z_0-9]+)` \|", re.M)
CLAUSE_END = re.compile(r"[;|.\n]")


def register(text: str) -> dict[str, str]:
    """The register's rows: identifier -> the status it decides."""
    return {m.group(1): m.group(2) for m in REGISTER_ROW.finditer(text)}


def register_identifiers(text: str) -> list[str]:
    """The register's identifiers in file order, duplicates kept, so a repeat can be seen."""
    return [m.group(1) for m in REGISTER_ROW.finditer(text)]


def claims(text: str) -> list[tuple[str, str, str]]:
    """Each (identifier, claimed status, the clause it was read from) in this document."""
    found = []
    for m in IDENTIFIER.finditer(text):
        clause = CLAUSE_END.split(text[m.end():], maxsplit=1)[0]
        s = STATUS.search(clause)
        if s:
            found.append((m.group(0), s.group(1), (m.group(0) + clause).strip()))
    return found


def citations(text: str) -> set[str]:
    return set(IDENTIFIER.findall(text))


def corpus() -> list[Path]:
    """Every normative Markdown document that may cite an ADR, the register itself excepted."""
    return sorted(p for p in ARCH.rglob("*.md") if p != REGISTER)


def register_text() -> str:
    return REGISTER.read_text(encoding="utf-8")


class TestTheReadersFindSomething(unittest.TestCase):
    """Positive controls. A parse that quietly stops working looks exactly like a passing test."""

    def test_the_register_yields_its_rows(self) -> None:
        reg = register(register_text())
        self.assertEqual(20, len(reg), "the register no longer yields twenty rows; re-derive this test")
        self.assertTrue(set(reg.values()) <= set(STATUSES),
                        f"the register carries a status this test does not know: {sorted(set(reg.values()))}")

    def test_the_corpus_cites_adrs(self) -> None:
        cited = set().union(*(citations(p.read_text(encoding="utf-8")) for p in corpus()))
        self.assertGreaterEqual(len(cited), 10, "almost no ADR is cited under docs/architecture; the reader has broken")

    def test_the_corpus_claims_statuses(self) -> None:
        n = sum(len(claims(p.read_text(encoding="utf-8"))) for p in corpus())
        self.assertGreaterEqual(n, 50, f"only {n} status claims read; the clause reader has broken")


class TestTheReaderCanFail(unittest.TestCase):
    """Negative controls, on copies. A guard that cannot fail guards nothing."""

    def test_an_unregistered_citation_is_seen(self) -> None:
        self.assertNotIn("ADR-021", register(register_text()))
        self.assertIn("ADR-021", citations("this design depends on ADR-021 for its shape"))

    def test_a_wrong_status_claim_is_seen(self) -> None:
        reg = register(register_text())
        read = claims("The design rests on ADR-001 modular monolith, `ACCEPTED`, and proceeds.")
        self.assertEqual([("ADR-001", "ACCEPTED")], [(a, s) for a, s, _ in read])
        self.assertNotEqual("ACCEPTED", reg["ADR-001"], "ADR-001 is accepted in the register; re-derive this control")

    def test_a_duplicated_register_identifier_is_seen(self) -> None:
        doubled = register_text() + "\n| ADR-001 | A second row | `ACCEPTED` | Nothing |\n"
        ids = register_identifiers(doubled)
        self.assertNotEqual(len(ids), len(set(ids)), "a repeated register row was not seen")

    def test_a_status_from_another_clause_is_not_claimed(self) -> None:
        text = "ADR-009's adapter boundary is elsewhere; ADR-019 retention, `BLOCKED_BY_S01`."
        self.assertEqual([("ADR-019", "BLOCKED_BY_S01")], [(a, s) for a, s, _ in claims(text)],
                         "a status was attributed across a clause boundary")

    def test_two_identifiers_may_share_one_status(self) -> None:
        text = "The design names ADR-002 and ADR-003, `DRAFT_REQUIRED`, as dependencies."
        self.assertEqual([("ADR-002", "DRAFT_REQUIRED"), ("ADR-003", "DRAFT_REQUIRED")],
                         [(a, s) for a, s, _ in claims(text)])


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
        reg = register(register_text())
        for p in corpus():
            with self.subTest(document=p.name):
                for adr, claimed, clause in claims(p.read_text(encoding="utf-8")):
                    self.assertIn(adr, reg, f"{p.name} claims a status for {adr}, which has no register row")
                    self.assertEqual(reg[adr], claimed,
                                     f"{p.name} says {adr} is `{claimed}`; the register says `{reg[adr]}`. "
                                     f"The register decides, so the document is what changes. Read: {clause[:120]!r}")


if __name__ == "__main__":
    unittest.main()
