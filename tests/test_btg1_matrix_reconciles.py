#!/usr/bin/env python3
"""The BT-G1 matrix reconciles: a design's claim on it, and the proof's rows, say the same thing.

`BT-G1` is recorded against one artefact: the eleven rows under "### The rows" in
`docs/architecture/p0/P0.SECURITY-PROOF.md`, each naming sibling controls by design and number.
Designs also state, in their own words, which of their controls feed that matrix. Nothing
compared the two, and five designs disagree with the proof (#323, found by the thirteen design
reviews under #322). A design believing it is covered, when the proof does not carry it, is a
hole nobody sees at the gate.

TWO DIRECTIONS.

  Forward   Every control a design claims feeds the matrix is named on a matrix row. Five
            designs fail this today; each is REGISTERED below, with its numbers and a reason.
  Backward  Every control the matrix names exists in the design it names. Nothing fails this,
            so it is live from the start: it catches a control renumbered or deleted out from
            under a row that still cites it.

WHICH TABLE IS THE MATRIX. The proof holds two numbered tables - its eleven matrix rows and its
own ten negative controls - so the reader is scoped to the section "### The rows". An earlier
version was not, and read both. That was not a cosmetic bug: editing the proof's OWN control
table to mention "P0.3 control 10" made this module report that P0.3 "no longer mismatches" and
instruct the author to retire a live #323 defect. A guard that tells you to delete a real finding
is worse than no guard, which is why the section anchor is asserted rather than assumed.

HOW A CLAIM IS READ. Clause-bounded, as `tests/test_adr_citations.py` reads an ADR's status: a
paragraph is split on `;` and `|`, and only a clause naming `BT-G1` is read. This matters. P0.5's
claim shares a paragraph with "Controls 1 to 3 and 5 are the manual's acceptance", which is true
and has nothing to do with the matrix, so a paragraph-level reader would invent three claims the
design never made. P0.12's claim sits inside a table cell, so a cell boundary is a clause
boundary too. Wrapped prose is joined into a paragraph first, because a claim written over two
lines is one claim.

A clause saying "every control feeds the ..." claims the design's whole control set. A clause
saying "the verifier for any control that feeds the matrix is not the implementer" claims
nothing: it is a conditional about the verifier, and requiring the verb `feed` right after
`every control` keeps the two apart. Without that, P0.6 and P0.12 would both read as claiming
everything.

WHAT THIS DOES NOT DO, and every item was demonstrated by an adversarial review that ran it.

 1. It keys on the literal `BT-G1`. A claim phrased "rows of the security proof's minimum
    negative proof matrix" - a wording the pack itself uses at P0.10's line 42 - is not read.
    The trigger is NOT widened to the bare word "matrix", because in this pack that word also
    means the baseline's matrix, P0.7's matrix, the matrix file and the matrix's scope; widening
    it would manufacture claims no design made, which is the failure mode this reader was built
    to avoid.
 2. It does not check that a control is on the RIGHT row. P0.7 puts its control 6 on the
    tampering row and the proof puts it on row 2; knowing that is wrong needs to know what a row
    means, and this module only counts.
 3. It does not read a design's evidence contract, so P0.6 naming controls 2, 3, 5, 6 and 8 in
    its text and only 2, 3, 5 and 6 in its evidence table passes here.
 4. It does not notice a design carrying the matrix's verifier language with no matrix row at
    all (P0.9), nor a control on a row that the design never claims (P0.10's control 6, #323's
    eighth item). The forward rule reads a design's claims; a design that claims nothing is
    silent, not clean.
 5. SIX OF THE THIRTEEN DESIGNS FILE NO READABLE CLAIM: P0.2, P0.8, P0.9, P0.10, P0.11 and P0.13.
    CLAIMING is asserted below so that the set cannot quietly change, but the forward rule
    genuinely reads under half the pack, and this module must not be read as covering the rest.

Items 2, 3 and 4 are recorded in #323's prose. A guard that caught them would have to understand
the rows rather than count them.

POSITIVE CONTROLS are structural, not thresholds. The matrix must be found, must hold exactly
eleven rows, and every row must name a design; the one row that rests on a mechanism rather
than a numbered control - row 11 - is registered, so a second cannot appear unnoticed. The set of designs filing
a claim is asserted by name. An earlier version counted instead - "at least six designs, at
least thirty controls" - and review showed both numbers sat exactly on the tree's own values,
so de-prefixing five mentions in the proof shrank the matrix to the threshold and passed.

WHAT THE REGISTRY IS ABSORBING. Emptying REGISTERED and running against the tree this was
written on reports exactly five designs at exactly the registered numbers: P0.3 (10), P0.4 (9),
P0.5 (4), P0.7 (7, 8, 9, 10) and P0.12 (6). That is the real-tree control #330 asks for - not a
synthetic mutation but the repository's own state - and it is the same five that a hand census
and three independent reviewers found separately.

Negative controls (run 2026-09-07 under WP-105, each on a copied tree, run as
`unittest discover -s tests -p test_btg1_matrix_reconciles.py` from that tree's root):
  * A design claims a control no matrix row names       -> test_every_claim_is_carried
  * The same, written over two wrapped lines            -> test_every_claim_is_carried
  * The same, written as a hyphen range, "3-5"          -> test_every_claim_is_carried
  * A registered mismatch repaired, entry left behind   -> test_registered_mismatches_still_mismatch
  * A registered design's claim made worse              -> test_registered_mismatches_still_mismatch
  * The proof's OWN control table mentions a registered -> nothing: it is not the matrix
    design's control (the false-repair bug, now fixed)     (asserted by test_the_matrix_is_the_right_table)
  * The matrix names a control no design has            -> test_every_carried_control_exists
  * A matrix row loses its design prefix                -> test_only_the_known_row_rests_on_no_numbered_control
    (caught by the row rule, not the name-set rule: the design is still named on another row,
    but the row it left has lost its only numbered control)
  * A design's claim is traded for another design's     -> test_the_same_designs_file_claims
  * The matrix section renamed away                     -> five rules, not isolated and not claimed to be

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "docs" / "architecture" / "p0"
PROOF = PACK / "P0.SECURITY-PROOF.md"
TICKET = "#323"

# The matrix is the table under this heading, and NOT the proof's own negative-control table,
# which is numbered identically. The header line is asserted too, so that a renamed section or a
# reordered table is a failure rather than a silent empty read.
MATRIX_HEADING = "### The rows"
MATRIX_HEADER = "| # | Row, as the ticket and the plan state it | Negative controls |"
MATRIX_ROWS = 11

# The designs that file a claim this reader can see. Asserted by name, not counted: review traded
# one design's claim for another's and a headcount passed. The other six - P0.2, P0.8, P0.9,
# P0.10, P0.11, P0.13 - file none, which the docstring records as a real limit of the forward rule.
CLAIMING = ("P0.12", "P0.3", "P0.4", "P0.5", "P0.6", "P0.7")

# The designs the matrix names controls for. Asserted by name because a mention that loses its
# "P0.N " prefix is simply dropped by the reader, and review showed five such edits shrinking the
# matrix silently while count-based positive controls still passed.
CARRIED_DESIGNS = ("P0.10", "P0.11", "P0.12", "P0.3", "P0.4", "P0.6", "P0.7", "P0.8")

# Designs whose claim the matrix does not carry, with the exact controls and why each is
# registered rather than repaired. A ratchet, in the shape of
# test_checkpoints_match_schema.LEGACY: an entry must STILL disagree at exactly these numbers, so
# a repaired design is forced out of the list, and the registry may only shrink.
#
# None is repaired here because repairing one edits a design, and whether that moves a design's
# version is unsettled (#316). WP-104 recorded the findings and fixed none, by the operator's
# instruction. Registering is not accepting: #323 stays open.
REGISTERED: dict[str, tuple[tuple[int, ...], str]] = {
    "P0.3": (
        (10,),
        "says 'Controls 1 to 7 and 10 are the BT-G1 matrix's ... rows' and separately that every "
        "control feeds it; the matrix names controls 1 to 9, and control 10 is on no row",
    ),
    "P0.4": (
        (9,),
        "claims 'every control feeds the BT-G1 matrix' over nine controls, but its own control 9 "
        "is 'A measurement, not a protection' and the matrix names 1 to 8",
    ),
    "P0.5": (
        (4,),
        "says 'control 4 is the tampering row of the BT-G1 (label B) matrix seen from the "
        "provisioning side'; no matrix row names any P0.5 control, and P0.5 appears in the proof "
        "only as environment and acceptance",
    ),
    "P0.7": (
        (7, 8, 9, 10),
        "claims 'every control feeds the BT-G1 matrix' over ten controls while its own next "
        "sentence scopes that to controls 1 to 5; the matrix names 1 to 6",
    ),
    "P0.12": (
        (6,),
        "says 'controls 2 and 6, which feed the BT-G1 matrix'; the matrix names control 2, and "
        "row 9 names 'the P0.12 design's log scan', which is not a numbered control",
    ),
}

# The matrix rows that name no numbered control, and so rest on a mechanism this module cannot
# reach. Row 11's cell is "P0.10's read-back asserting every field of the evidence contract
# present" - not one of P0.10's ten controls. One row is a finding for #323; a second appearing
# unnoticed would be a hole.
ROWS_ON_A_MECHANISM = (11,)

# One number-phrase grammar, used by both readers. "1 to 5", "3-5", "2, 3 and 8" and any mixture.
# The hyphen form is here because review wrote "Controls 3-5" and an earlier version read it as
# {3, 5}, losing the interior claim on control 4 silently.
PHRASE = r"(?:\d+(?:\s*(?:to|-|–)\s*\d+)?[,\s]*(?:and\s+)?)+"
CONTROLS_NAMED = re.compile(rf"\bcontrols?\s+({PHRASE})", re.I)
ROW_CONTROLS = re.compile(rf"(?:(P0\.\d+)\s+)?controls?\s+({PHRASE})")
BLANKET = re.compile(r"\bevery control\b[^;|]*\bfeed", re.I)


def control_numbers(phrase: str) -> set[int]:
    """The numbers a phrase names: '1 to 3, 5 and 8' and '1-3, 5, 8' are both {1,2,3,5,8}."""
    numbers: set[int] = set()
    ranges = re.compile(r"(\d+)\s*(?:to|-|–)\s*(\d+)")
    for run in ranges.finditer(phrase):
        numbers |= set(range(int(run.group(1)), int(run.group(2)) + 1))
    numbers |= {int(n) for n in re.findall(r"\d+", ranges.sub("", phrase))}
    return numbers


def designs() -> list[Path]:
    return sorted(p for p in PACK.glob("P0.*.md") if p.name != PROOF.name)


def epic(path: Path) -> str:
    """The name the matrix calls a design by: P0.06-... is P0.6."""
    return "P0." + str(int(re.match(r"P0\.(\d+)-", path.name).group(1)))


def own_controls(text: str) -> set[int]:
    """The numbers of a design's own negative-control rows."""
    body = text.split("## Negative controls", 1)[1].split("\n## ", 1)[0]
    return {int(m.group(1)) for m in re.finditer(r"^\| (\d+) \|", body, re.M)}


def matrix_rows() -> list[str]:
    """The eleven rows of the BT-G1 matrix, and nothing else that happens to be numbered."""
    text = PROOF.read_text(encoding="utf-8")
    if MATRIX_HEADING not in text:
        return []
    section = text.split(MATRIX_HEADING, 1)[1].split("\n## ", 1)[0]
    if MATRIX_HEADER not in section:
        return []
    return [l for l in section.splitlines() if re.match(r"^\| \d+ \|", l)]


def carried() -> dict[str, set[int]]:
    """Every control the matrix rows name, by design.

    A row names several designs in one cell and continues without repeating the last one -
    "P0.7 controls 1 to 5, through the bypass path, and control 6" - so the design most recently
    named carries forward within the row, and never across rows.
    """
    found: dict[str, set[int]] = {}
    for line in matrix_rows():
        current = None
        for m in ROW_CONTROLS.finditer(line):
            if m.group(1):
                current = m.group(1)
            if current:
                found.setdefault(current, set()).update(control_numbers(m.group(2)))
    return found


def clauses(text: str) -> list[str]:
    """Clause-sized pieces of a document: table cells stay per row, prose is joined per paragraph.

    Wrapped prose is joined first, because a claim written over two lines is one claim and an
    earlier line-at-a-time reader let exactly that through.
    """
    pieces: list[str] = []
    paragraph: list[str] = []
    for line in text.splitlines():
        if line.startswith("|") or not line.strip():
            if paragraph:
                pieces.append(" ".join(paragraph))
                paragraph = []
            if line.startswith("|"):
                pieces.append(line)
        else:
            paragraph.append(line.strip())
    if paragraph:
        pieces.append(" ".join(paragraph))
    return [c for piece in pieces for c in re.split(r"[;|]", piece)]


def claimed(text: str) -> tuple[set[int], bool]:
    """The controls a design says feed the matrix, and whether it said so as a blanket."""
    numbers: set[int] = set()
    blanket = False
    for clause in clauses(text):
        if "BT-G1" not in clause:
            continue
        if BLANKET.search(clause):
            blanket = True
        for m in CONTROLS_NAMED.finditer(clause):
            numbers |= control_numbers(m.group(1))
    return numbers, blanket


def mismatch(path: Path, rows: dict[str, set[int]]) -> tuple[int, ...]:
    """The controls this design claims on the matrix that no matrix row names."""
    text = path.read_text(encoding="utf-8")
    numbers, blanket = claimed(text)
    if blanket:
        numbers |= own_controls(text)
    return tuple(sorted(numbers - rows.get(epic(path), set())))


class TestTheReaderReadsTheRightThing(unittest.TestCase):
    """Positive controls, structural rather than counted. Every rule below rests on these."""

    def test_the_matrix_is_the_right_table(self) -> None:
        """The proof holds two numbered tables; only one of them is the matrix.

        Reading the other made an earlier version report a registered defect as repaired.
        """
        text = PROOF.read_text(encoding="utf-8")
        self.assertIn(MATRIX_HEADING, text, "the matrix section has been renamed; re-derive this module")
        self.assertIn(MATRIX_HEADER, text, "the matrix table's header has changed; re-derive this module")
        self.assertEqual(MATRIX_ROWS, len(matrix_rows()), "the matrix no longer holds eleven rows")
        numbered = len(re.findall(r"^\| \d+ \|", text, re.M))
        self.assertGreater(numbered, MATRIX_ROWS, "the proof's own control table has gone; the scoping may be stale")

    def test_every_row_names_a_design(self) -> None:
        """A row naming no design at all is a row this module cannot read.

        Weaker than "names a numbered control", and deliberately: see the next test.
        """
        for row in matrix_rows():
            with self.subTest(row=row.split("|")[1].strip()):
                self.assertRegex(row, r"P0\.\d+", "this matrix row names no design")

    def test_only_the_known_row_rests_on_no_numbered_control(self) -> None:
        """Row 11 rests on a mechanism, not a control. It is the only one, and that is a finding.

        Its controls cell reads "P0.10's read-back asserting every field of the evidence contract
        present" - which is not one of P0.10's ten numbered negative controls, so nothing this
        module checks can reach it, and the P0.10 review found separately that the read-back
        asserts four fields rather than every field. Registered here so that a SECOND such row
        cannot appear unnoticed; the row itself is #323's business, not this package's.
        """
        without = tuple(
            int(row.split("|")[1].strip())
            for row in matrix_rows()
            if not [m for m in ROW_CONTROLS.finditer(row) if m.group(1)]
        )
        self.assertEqual(
            ROWS_ON_A_MECHANISM, without,
            "the set of matrix rows resting on no numbered control has changed. A new one is a "
            f"row nothing here can check; a row that has gained a control leaves this tuple ({TICKET}).",
        )

    def test_the_matrix_names_the_same_designs(self) -> None:
        """Asserted by name. A mention that loses its 'P0.N ' prefix is dropped, not flagged."""
        self.assertEqual(
            tuple(sorted(CARRIED_DESIGNS)), tuple(sorted(carried())),
            "the set of designs the matrix names controls for has changed. A design that has "
            "vanished may have lost its prefix rather than its row; one that has appeared needs "
            "adding to CARRIED_DESIGNS deliberately.",
        )

    def test_the_same_designs_file_claims(self) -> None:
        """Asserted by name. A headcount passed when review traded one design's claim for another's."""
        filing = tuple(sorted(
            epic(p) for p in designs()
            if any(claimed(p.read_text(encoding="utf-8")))
        ))
        self.assertEqual(
            tuple(sorted(CLAIMING)), filing,
            "the set of designs filing a readable BT-G1 claim has changed. A design that has "
            "stopped claiming may have lost the claim or the label; one that has started needs "
            "adding to CLAIMING deliberately.",
        )


class TestTheMatrixReconciles(unittest.TestCase):
    def test_every_claim_is_carried(self) -> None:
        """Forward: what a design claims, a matrix row names.

        Registered designs are not read here - the ratchet owns them - so repairing one fires
        exactly one test.
        """
        rows = carried()
        for path in [p for p in designs() if epic(p) not in REGISTERED]:
            with self.subTest(design=path.name):
                found = mismatch(path, rows)
                self.assertEqual(
                    (), found,
                    f"{epic(path)} claims controls {list(found)} on the BT-G1 matrix that no "
                    f"matrix row names. Either the design's claim or the matrix is wrong; see "
                    f"{TICKET}. A new disagreement is a defect, not a registry entry.",
                )

    def test_every_carried_control_exists(self) -> None:
        """Backward: a control the matrix names is one the design has."""
        have = {epic(p): own_controls(p.read_text(encoding="utf-8")) for p in designs()}
        for name, numbers in sorted(carried().items()):
            with self.subTest(design=name):
                self.assertIn(name, have, f"the matrix names {name}, which is not a design in the pack")
                missing = sorted(numbers - have[name])
                self.assertEqual([], missing, f"the matrix names {name} controls {missing}, which that design does not have")


class TestTheRegistryIsARatchet(unittest.TestCase):
    def test_registered_mismatches_still_mismatch(self) -> None:
        """An entry must still be wrong, at exactly its numbers. A repaired design leaves the list."""
        rows = carried()
        by_epic = {epic(p): p for p in designs()}
        for name, (numbers, reason) in REGISTERED.items():
            with self.subTest(design=name):
                self.assertIn(name, by_epic, f"{name} is registered and is not a design in the pack")
                self.assertGreater(len(reason.split()), 12, f"{name}: a registry entry states its reason")
                self.assertEqual(
                    numbers, mismatch(by_epic[name], rows),
                    f"{name} no longer mismatches at {list(numbers)}. If it reconciles, delete "
                    f"REGISTERED[{name!r}]; if it mismatches elsewhere, something moved and that "
                    f"needs its own reason. Check the matrix, not only the design.",
                )

    def test_the_registry_only_shrinks(self) -> None:
        """Membership is a deliberate edit, not somewhere to put a new disagreement."""
        by_epic = {epic(p): p for p in designs()}
        for name, (numbers, _reason) in REGISTERED.items():
            with self.subTest(design=name):
                self.assertIn(name, by_epic, f"{name} is registered and is not a design in the pack")
                have = own_controls(by_epic[name].read_text(encoding="utf-8"))
                self.assertEqual([], sorted(set(numbers) - have), f"{name} is registered for controls it does not have")
                self.assertIn(name, CLAIMING, f"{name} is registered and files no readable claim")
        self.assertEqual(
            ["P0.12", "P0.3", "P0.4", "P0.5", "P0.7"], sorted(REGISTERED),
            f"the registry may only shrink; these five are what the reviews under #322 found, and "
            f"a sixth disagreement is a defect to fix, not to register ({TICKET}).",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
