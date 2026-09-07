#!/usr/bin/env python3
"""The BT-G1 matrix reconciles: a design's claim on it, and the proof's rows, say the same thing.

`BT-G1` is recorded against one artefact: the eleven rows of `docs/architecture/p0/
P0.SECURITY-PROOF.md`, each naming sibling controls by number. Twelve designs also state, in
their own words, which of their controls feed that matrix. Nothing compared the two, and they
disagree in five designs (#323, found by the thirteen design reviews under #322).

A design believing it is covered, when the proof does not carry it, is a hole nobody sees at
the gate. That is the whole reason for this module.

TWO DIRECTIONS, and both are needed.

  Forward   Every control a design claims feeds the matrix is named on a proof row.
            Five designs fail this today; each is REGISTERED below with its numbers.
  Backward  Every control the proof names exists in the design it names. Nothing fails this,
            so it is a live rule rather than a registered one - it is what would catch the
            proof citing a control that was renumbered or deleted out from under it.

HOW A CLAIM IS READ. Clause-bounded, as `tests/test_adr_citations.py` reads an ADR's status:
a line is split on `;` and `|`, and only a clause that mentions `BT-G1` is read. This matters.
P0.5's claim sits in a line that also says "Controls 1 to 3 and 5 are the manual's acceptance"
- true, and nothing to do with the matrix - so a line-level reader would invent three claims
the design never made. P0.12's sits inside a table cell, so the cell boundary is a clause
boundary too.

A clause saying "every control feeds the ..." claims the design's whole control set. A clause
saying "any control that feeds the matrix is not the implementer" claims nothing: it is a
conditional about the verifier, and the reader requires the verb `feed` after `every control`
so that the two do not read alike.

WHAT THIS DOES NOT DO. It does not check that a control the proof names is on the RIGHT row -
P0.7 puts its control 6 on the tampering row and the proof puts it on row 2, which is in #323
and is not machine-checkable without knowing what each row means. It does not read a design's
evidence contract, so P0.6 naming controls 2, 3, 5, 6 and 8 in its text and only 2, 3, 5 and 6
in its evidence table passes here. It does not notice a design that carries the matrix's
verifier language with no matrix row at all, which is P0.9's case. All three are in #323's
prose; a guard that caught them would need to know what a row means, and this one only counts.

Positive controls: the proof must yield rows and controls, and the designs must yield claims,
or every rule here holds over nothing.

Negative controls (run 2026-09-07 under WP-105, each on a copied tree, run as
`unittest discover -s tests -p test_btg1_matrix_reconciles.py` from that tree's root):
  * A design claims a control the proof does not name    -> test_every_claim_is_carried
  * A registered mismatch is repaired in the design      -> test_registered_mismatches_still_mismatch
    but left in the registry
  * A registered design's numbers change                 -> test_registered_mismatches_still_mismatch
  * The proof names a control no design has              -> test_every_carried_control_exists

The last two are the positive controls, and they are deliberately NOT isolated: taking the
corpus away breaks several rules at once, and claiming otherwise would be false precision. What
each asserts is that the rule which exists to notice an empty corpus is among the failures,
rather than the suite going green over nothing:
  * Every matrix row emptied of its controls             -> test_the_proof_yields_controls, +3
  * Every BT-G1 mention removed from the designs         -> test_the_designs_yield_claims, +1

WHAT THE REGISTRY IS ABSORBING. Emptying REGISTERED and running this module against the tree
it was written on reports exactly five designs, at exactly the numbers registered: P0.3 (10),
P0.4 (9), P0.5 (4), P0.7 (7, 8, 9, 10) and P0.12 (6). That is the check that the reader is
finding real disagreements rather than the registry covering for a reader that finds nothing,
and it is the same five a hand census and three independent reviewers found separately.

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

# Designs whose claim on the matrix the proof does not carry, with the exact controls and why
# each is registered rather than repaired. A ratchet, in the shape of
# test_checkpoints_match_schema.LEGACY: an entry must STILL mismatch at exactly these numbers,
# and the moment a design and the proof agree the entry has to go. It may only shrink.
#
# None is repaired here because repairing one edits a design, and whether that moves a design's
# version is unsettled (#316). WP-104 recorded the findings and fixed none of them, by the
# operator's instruction; this module stops any NEW disagreement joining them.
REGISTERED: dict[str, tuple[tuple[int, ...], str]] = {
    "P0.3": (
        (10,),
        "says 'Controls 1 to 7 and 10 are the BT-G1 matrix's ... rows' and separately that every "
        "control feeds it; the proof's rows name controls 1 to 9, and control 10 is on none",
    ),
    "P0.4": (
        (9,),
        "claims 'every control feeds the BT-G1 matrix' over nine controls, but its own control 9 "
        "is 'A measurement, not a protection' and the proof names 1 to 8",
    ),
    "P0.5": (
        (4,),
        "says 'control 4 is the tampering row of the BT-G1 (label B) matrix seen from the "
        "provisioning side'; no proof row names any P0.5 control, and P0.5 appears in the proof "
        "only as environment and acceptance",
    ),
    "P0.7": (
        (7, 8, 9, 10),
        "claims 'every control feeds the BT-G1 matrix' over ten controls while its own next "
        "sentence scopes that to controls 1 to 5; the proof names 1 to 6",
    ),
    "P0.12": (
        (6,),
        "says 'controls 2 and 6, which feed the BT-G1 matrix'; the proof names control 2, and row "
        "9 names 'the P0.12 design's log scan', which is not a numbered control",
    ),
}

# A clause claiming the design's whole control set. `feed` is required after `every control` so
# that "any control that feeds the matrix is not the implementer" - a conditional about the
# verifier, which P0.6 and P0.12 both write - is not read as a claim that every control feeds.
BLANKET = re.compile(r"\bevery control\b[^;|]*\bfeed", re.I)
NUMBERS = re.compile(r"\bcontrols?\s+((?:\d+(?:\s+to\s+\d+)?[,\s]*(?:and\s+)?)+)", re.I)
ROW = re.compile(r"^\| \d+ \|")
NAMED = re.compile(r"(?:(P0\.\d+)\s+)?controls?\s+((?:\d+(?:\s+to\s+\d+)?[,\s]*(?:and\s+)?)+)")


def spread(spec: str) -> set[int]:
    """The control numbers a phrase names: '1 to 3, 5 and 8' is {1,2,3,5,8}."""
    numbers = set()
    for run in re.finditer(r"(\d+)\s+to\s+(\d+)", spec):
        numbers |= set(range(int(run.group(1)), int(run.group(2)) + 1))
    numbers |= {int(n) for n in re.findall(r"\d+", re.sub(r"\d+\s+to\s+\d+", "", spec))}
    return numbers


def designs() -> list[Path]:
    return sorted(p for p in PACK.glob("P0.*.md") if p.name != PROOF.name)


def epic(path: Path) -> str:
    """The name the proof calls a design by: P0.06-... is P0.6."""
    return "P0." + str(int(re.match(r"P0\.(\d+)-", path.name).group(1)))


def own_controls(text: str) -> set[int]:
    """The numbers of a design's own negative-control rows."""
    body = text.split("## Negative controls", 1)[1].split("\n## ", 1)[0]
    return {int(m.group(1)) for m in re.finditer(r"^\| (\d+) \|", body, re.M)}


def carried() -> dict[str, set[int]]:
    """Every control the proof's matrix rows name, by design.

    A row names several designs in one cell and continues without repeating the last one -
    "P0.7 controls 1 to 5, through the bypass path, and control 6" - so the design most
    recently named carries forward within the row.
    """
    found: dict[str, set[int]] = {}
    for line in PROOF.read_text(encoding="utf-8").splitlines():
        if not ROW.match(line):
            continue
        current = None
        for m in NAMED.finditer(line):
            if m.group(1):
                current = m.group(1)
            if current:
                found.setdefault(current, set()).update(spread(m.group(2)))
    return found


def claimed(text: str) -> tuple[set[int], bool]:
    """The controls a design says feed the matrix, and whether it said so as a blanket."""
    numbers: set[int] = set()
    blanket = False
    for line in text.splitlines():
        for clause in re.split(r"[;|]", line):
            if "BT-G1" not in clause:
                continue
            if BLANKET.search(clause):
                blanket = True
            for m in NUMBERS.finditer(clause):
                numbers |= spread(m.group(1))
    return numbers, blanket


def mismatch(path: Path, rows: dict[str, set[int]]) -> tuple[int, ...]:
    """The controls this design claims on the matrix that the proof does not name."""
    text = path.read_text(encoding="utf-8")
    numbers, blanket = claimed(text)
    if blanket:
        numbers |= own_controls(text)
    return tuple(sorted(numbers - rows.get(epic(path), set())))


class TestTheReaderReadsSomething(unittest.TestCase):
    """Positive controls. Every rule below is vacuous if these do not hold."""

    def test_the_proof_yields_controls(self) -> None:
        rows = carried()
        self.assertGreaterEqual(len(rows), 6, "the proof's rows name fewer designs than the pack has")
        self.assertGreaterEqual(sum(len(v) for v in rows.values()), 30, "too few controls read from the proof's rows")

    def test_the_designs_yield_claims(self) -> None:
        rows = carried()
        claiming = [p.name for p in designs() if claimed(p.read_text(encoding="utf-8"))[0] or
                    claimed(p.read_text(encoding="utf-8"))[1]]
        self.assertGreaterEqual(len(claiming), 6, f"only {len(claiming)} designs claim anything; the reader has stopped reading")
        self.assertNotEqual({}, rows)


class TestTheMatrixReconciles(unittest.TestCase):
    def test_every_claim_is_carried(self) -> None:
        """Forward: what a design claims, the proof names.

        Registered designs are not checked here at all - the ratchet below owns them entirely,
        so repairing one fires exactly one test instead of two.
        """
        rows = carried()
        unregistered = [p for p in designs() if epic(p) not in REGISTERED]
        self.assertGreaterEqual(len(unregistered), 7, "too few unregistered designs; this rule reads almost nothing")
        for path in unregistered:
            with self.subTest(design=path.name):
                found = mismatch(path, rows)
                self.assertEqual(
                    (), found,
                    f"{epic(path)} claims controls {list(found)} on the BT-G1 matrix that the "
                    f"proof's rows do not name. Either the design's claim or the proof's rows "
                    f"are wrong; see {TICKET}. A new disagreement is a defect, not a registry entry.",
                )

    def test_every_carried_control_exists(self) -> None:
        """Backward: a control the proof names is one the design has.

        Nothing fails this today, which is the point: it catches a control renumbered or
        deleted out from under a proof row that still cites it.
        """
        rows = carried()
        have = {epic(p): own_controls(p.read_text(encoding="utf-8")) for p in designs()}
        for name, numbers in sorted(rows.items()):
            with self.subTest(design=name):
                self.assertIn(name, have, f"the proof names {name}, which is not a design in the pack")
                missing = sorted(numbers - have[name])
                self.assertEqual([], missing, f"the proof's rows name {name} controls {missing}, which that design does not have")


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
                    f"needs its own reason.",
                )

    def test_the_registry_only_shrinks(self) -> None:
        """Membership is a deliberate edit, not a place to put a new disagreement.

        Structural, not a literal list: every registered design must exist, and every number
        registered against it must be a control that design actually has - so an entry cannot
        be invented for a design or a control that is not there.
        """
        by_epic = {epic(p): p for p in designs()}
        for name, (numbers, _reason) in REGISTERED.items():
            with self.subTest(design=name):
                have = own_controls(by_epic[name].read_text(encoding="utf-8"))
                self.assertEqual([], sorted(set(numbers) - have), f"{name} is registered for controls it does not have")
        self.assertEqual(
            ["P0.12", "P0.3", "P0.4", "P0.5", "P0.7"], sorted(REGISTERED),
            f"the registry may only shrink; these five are what the reviews under #322 found, and "
            f"a sixth disagreement is a defect to fix, not to register ({TICKET}).",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
