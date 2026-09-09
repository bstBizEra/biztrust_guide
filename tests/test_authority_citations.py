#!/usr/bin/env python3
"""A decision's authority citation must name a grant that exists.

Every entry in `badf/decision-log.jsonl` carries an `authority` field. It is the pointer a reader
follows to check that a decision was made under a grant that exists, and until this module nothing
in the repository resolved it: neither `scripts/validate_continuity.py` nor any test under `tests/`
asked whether the string named a key `badf/current-state.json` actually holds. So an entry could
name no grant at all and still read as governed. One does - DEC-118 (#356) - and it was copied into
a WP-113 draft precisely because it was the model, caught there in review while the merged one
stayed as the pattern anyone would copy next.

THE CORPUS, measured at 8adda10 with

    python -c "import json,collections;print(collections.Counter(json.loads(l)['authority'] for l in
    open('badf/decision-log.jsonl',encoding='utf-8') if l.strip()).most_common())"

was 118 entries in two shapes:

    106  IMPLEMENTATION_SCOPE                                            legacy bare form
      5  badf/current-state.json authority.guide_v2_records_drafting     qualified, resolves
      2  REPOSITORY_CHARTER                                              legacy bare form
      2  OPERATOR_INSTRUCTION                                            legacy bare form
      2  badf/current-state.json authority.implementation                qualified, resolves
      1  badf/current-state.json authority.documentation_implementation  qualified, DOES NOT RESOLVE

Eight qualified citations, seven of which resolve. This package appends DEC-121, qualified and
resolving, making nine.

TWO RULES, and they are not the same kind of rule.

  A  A QUALIFIED CITATION MUST RESOLVE. Any `authority` of the form
     `badf/current-state.json authority.<key>` must name a key present in that record's `authority`
     block. The keys are READ FROM THE RECORD, never listed here: a guard that carried its own copy
     of the eleven keys would go on passing after the record changed, which is the defect class this
     repository keeps meeting.

  B  THE LEGACY BARE FORMS ARE FROZEN. `IMPLEMENTATION_SCOPE`, `REPOSITORY_CHARTER` and
     `OPERATOR_INSTRUCTION` are unqualified: they name no file, no block and no key, so there is
     nothing to resolve them against and nothing here tries.

     RULE B FREEZES A LEGACY POPULATION RATHER THAN VALIDATING IT. It says nothing about whether
     those 110 entries were made under a real grant - it cannot, because the strings point nowhere.
     What it does is fix the exact set of legacy strings and the exact count of entries using each,
     so a NEW bare-form citation fails and its author is pushed onto the form Rule A can check. The
     count of a form that is checked by nothing is the only thing about it that can be guarded.

DEC-118 IS REGISTERED, NOT REPAIRED. The log is append-only under the extend-only principle,
DEC-118 is merged on `main`, and #356 item 1 puts its repair behind the version-and-record judgement
in #316. Editing it here would be this package deciding a question that is explicitly somebody
else's, so the entry is registered as a ratchet in the shape of `tests/test_stale_records.py`.

THE REGISTRY IS PROVEN STILL-BROKEN, NOT MERELY LISTED. A registry entry that would pass when its
subject is simply absent is worthless, and this repository has already paid for that exact defect
once: an earlier package's registry compared a SUMMARY of its record, so a repair that left the
summary alone kept the entry registered and the suite green. `test_registered_citations_still_fail`
therefore asserts four things about DEC-118 rather than one, and every one of them is a way the
registration could stop describing the repository:

  * the entry is STILL IN THE LOG                     - a deleted entry forces the registration out
  * its `authority` is STILL EXACTLY the registered string - any repair, in any wording, forces it out
  * the key it names is STILL ABSENT from the record  - adding the key forces it out
  * NO LATER ENTRY SUPERSEDES IT                      - the repair route #356 item 1 names is a
                                                        superseding entry, which would not touch
                                                        DEC-118's own line at all; without this
                                                        clause the registration would survive the
                                                        very repair it is waiting for

Each of those four has a control in `scripts/wp115_controls.py` that measures it, and a fifth
control pairs with the first: the same deletion, with this test weakened to a membership listing,
runs GREEN. That pair is what makes "proven still-broken" a measurement instead of a claim.

AN EXACT STRING, NOT A DIGEST. `tests/test_stale_records.py` registers a SHA-256 because its
subjects are prose - a table row, a bullet - where a repair can move text the registration never
read. Here the registered subject is ONE FIELD holding ONE value, so the exact value IS the record
and equality over it is the same ratchet with nothing left out. The `supersedes` clause above is
what covers the one repair route that does not change that field.

WHAT THIS DOES NOT DO. Every item is a real limit, not a caveat.

 1. IT ASKS WHETHER THE POINTER RESOLVES, NEVER WHETHER THE GRANT IS THE RIGHT ONE. An entry citing
    `authority.implementation` passes here whatever it decided. Whether that key is even a sensible
    target is open defect #346 - it names no domain and sits beside `production_platform_implementation`,
    so a reader can take one for the other - and #356's closing paragraph raises it. That is a
    judgement about grants; this module is about pointers. No check for it is built here.
 2. THE KEY'S VALUE IS NOT READ. `production_platform_implementation` reads `NOT_GRANTED` and
    `architecture_drafting_ahead_of_s01` reads `WAIT_FOR_OPERATOR_WAIVER_ISSUE_92`. An entry citing
    either RESOLVES and passes. A resolving pointer is not a granted authority, and nothing here
    says otherwise.
 3. ONLY `badf/decision-log.jsonl` IS READ. `badf/next-actions.json` gives every action an
    `authority` too - `HUMAN_DECISION_REQUIRED`, `WAIT_FOR_AUTHORITY_ON_ASSERTED_KEYS_ISSUE_52` and
    the dated operator instructions - and every session checkpoint carries an `authority` object.
    Neither is checked. That omission has a measured edge worth naming, because it is where DEC-118's
    string came from:

        python -c "import json,glob,collections;c=collections.Counter();[c.update(list(json.load(
        open(p,encoding='utf-8')).get('authority') or {})) for p in glob.glob(
        'sessions/checkpoints/*.json')];print(c.most_common(4))"

    reports `documentation_implementation` in 85 of the 96 checkpoints, against 4 for
    `implementation`. The checkpoints run their own authority vocabulary, and
    `authority.documentation_implementation` is what you get when a checkpoint's key is written
    against the record's path. Reconciling the two vocabularies is a records decision nobody has
    taken and is not taken here.
 4. ONE SYNTACTIC FORM IS QUALIFIED: exactly `badf/current-state.json authority.<key>`, anchored at
    both ends. A citation of the same grant written any other way - a URL, `current-state.json
    authority.x`, a nested path - is NOT qualified and is not resolved. It does not vanish, though:
    every STRING that QUALIFIED does not match falls into Rule B's arm, whose set is an EQUALITY, so
    `test_the_legacy_forms_are_exactly_these` fails on it. (A citation that is not a string at all
    cannot be matched against either pattern and is limit 6's bucket, named there rather than here.)
    An unreadable citation is loud rather
    than silent, which is what makes an incomplete pattern safe - the same rule
    `tests/test_stale_records.py` limit 7 rests on. There is deliberately no second test asserting
    the same set operation under a different name.
 5. NOTHING HERE CHECKS ID UNIQUENESS, ORDERING OR SCHEMA. `scripts/validate_continuity.py` and
    `tests/test_badf_match_schemas.py` own those, and `schemas/decision-record.schema.json` records
    why `authority` is an open string there: nothing in the repository declares its vocabulary, and
    closing it in the schema would invent one. This module declares part of it instead, from the
    corpus rather than from a design.
 6. A CITATION OF THE WRONG TYPE IS EXCLUDED FROM BOTH RULES, AND IS NAMED FOR IT. `malformed()`
    is a third bucket, not a third shape: an `authority` that is a dict or `null` cannot be matched
    against a pattern at all, so neither rule reads it, and
    `test_every_entry_carries_a_string_authority` turns that exclusion into a named failure rather
    than a `TypeError` out of the middle of a reader. The schema and
    `tests/test_badf_match_schemas.py` own the rule that it must be a string; what is owned here is
    that being unreadable is never a way out of the corpus. Limit 4 refuses that for a citation
    whose SHAPE is unknown; this is the same refusal for one whose TYPE is.
 7. THE ENTRY FLOOR IS A FLOOR, NOT AN EQUALITY, because the log grows by one entry per package and
    an equality would make every future package edit this file for no reason. The equalities that
    matter are elsewhere and are real equalities: the legacy per-form counts, the legacy total and
    the registry's membership and size. A qualified citation may be ADDED freely - Rule A checks it
    - and that is the whole point of freezing the other form.

Stdlib only: no third-party import, no network, no subprocess. Four modules under `tests/` do call a
subprocess and this is not a fifth; the four are `test_resume_reconciliation.py`,
`test_resume_schema_identity.py`, `test_validator_fails_closed.py` and
`test_wp024_fixtures_are_sealed.py`, measured with

    grep -lnE "subprocess[.](run|Popen|check_output|check_call)" tests/*.py

GREPPING FOR THE WORD IS THE WRONG FILTER, and the reason is a property rather than a number: it
matches every module that merely NAMES `subprocess` - THIS ONE INCLUDED, in the sentence you are
reading - so it returns a strict superset of the modules that call one, and the gap between the two
widens every time a docstring mentions it. At this commit `grep -l subprocess tests/*.py` returns 7
against the 4 above, and 7 is not a fact about the suite. WP-114 recorded the same correction as
"a count is only as good as its filter" and it reached a fourth file by being copied; this is the
fifth, and it is written as an inequality so that copying it cannot make it false.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LOG = ROOT / "badf/decision-log.jsonl"
STATE = ROOT / "badf/current-state.json"

# The qualified citation, anchored at both ends. See limit 4: a citation written any other way is
# not read as qualified, and test_every_citation_is_one_of_the_two_known_forms fails it rather than
# letting it pass unchecked.
QUALIFIED = re.compile(r"^badf/current-state\.json authority\.([A-Za-z0-9_]+)$")

# --- Rule A's registry -------------------------------------------------------------------------
#
# Entries whose qualified citation does not resolve TODAY, keyed by decision id and holding the
# exact citation string. The string is the whole of the registered record - one field, one value -
# so equality over it is the ratchet; see "AN EXACT STRING, NOT A DIGEST" above. An entry may only
# LEAVE, when its subject is repaired or superseded.
UNRESOLVED_CITATIONS: dict[str, dict] = {
    "DEC-118": {
        "citation": "badf/current-state.json authority.documentation_implementation",
        "why": ("#356: the record's authority block has no documentation_implementation, so this "
                "entry reads as governed while naming no grant; the log is append-only and #356 "
                "item 1 puts the repair behind the records judgement in #316, so it is registered "
                "here rather than edited. The key it names is the checkpoints' own vocabulary - 85 "
                "of 96 carry it - written against this record's path, which is limit 3"),
    },
}

# --- Rule B's frozen population ------------------------------------------------------------------
#
# The legacy bare forms and the exact number of entries using each, measured at 8adda10. These are
# EQUALITIES. A new entry reusing one of these strings moves a count; a new bare form of any other
# spelling changes the set; either way the author is pushed onto the qualified form Rule A can
# check. Nothing here resolves these strings, because nothing can - see rule B above.
LEGACY_CITATIONS: dict[str, int] = {
    "IMPLEMENTATION_SCOPE": 106,
    "REPOSITORY_CHARTER": 2,
    "OPERATOR_INSTRUCTION": 2,
}
LEGACY_ENTRIES = 110

# Corroborating floors. The qualified floor is what stops the Rule A arm reading nothing and
# reporting success: 8 at 8adda10 plus DEC-121, appended by this package. The entry floor is limit 7.
QUALIFIED_CITATIONS_FLOOR = 9
ENTRIES_FLOOR = 119
AUTHORITY_KEYS_FLOOR = 11


def entries() -> list[dict]:
    """Every decision entry, or [] when the log is missing.

    Empty rather than raising, so that test_anchors_exist owns the diagnosis; that is the house
    pattern from tests/test_stale_records.reconciliation_table() and
    tests/test_btg1_matrix_reconciles.matrix_rows(). It matters more than usual here: a registry
    that asserts a key is ABSENT is satisfied by a record that is absent too, so the anchors are
    what keep this module from passing over an empty tree.
    """
    if not LOG.is_file():
        return []
    return [json.loads(line) for line in LOG.read_text(encoding="utf-8").splitlines() if line.strip()]


def authority_keys() -> frozenset[str]:
    """The keys the record holds, READ FROM THE RECORD. Never a list carried here - see rule A."""
    if not STATE.is_file():
        return frozenset()
    block = json.loads(STATE.read_text(encoding="utf-8")).get("authority")
    return frozenset(block) if isinstance(block, dict) else frozenset()


def citations() -> list[tuple[object, object]]:
    """(decision id, authority) for every entry, in log order, WHATEVER TYPE THE RECORD HOLDS.

    Nothing is coerced here. `schemas/decision-record.schema.json` requires `authority` to be a
    non-empty string and `tests/test_badf_match_schemas.py` enforces it, so a non-string is a defect
    a sibling guard already reports - but a guard that CRASHES where a sibling would fail cleanly
    tells its reader less than one that names what it found. `malformed()` is that named answer, and
    the two readers below skip anything that is not a string rather than handing it to `re.match`.
    """
    return [(entry.get("id", ""), entry.get("authority", "")) for entry in entries()]


def malformed() -> list[tuple[object, object]]:
    """Entries whose id or authority is not a non-empty string, which NEITHER rule can read.

    Excluded from `qualified()` and `legacy()` alike, so this is a third bucket rather than a third
    shape of citation - and `test_every_entry_carries_a_string_authority` is what stops the
    exclusion being silent. Without it, an entry could leave the corpus by being unreadable, which
    is the failure mode limit 4 exists to refuse for citations written in an unknown SHAPE; a
    citation of the wrong TYPE is the same defect one level down.
    """
    return [(dec, value) for dec, value in citations()
            if not (isinstance(dec, str) and dec and isinstance(value, str) and value)]


def qualified() -> list[tuple[str, str, str]]:
    """(decision id, citation, key) for every citation of the qualified form."""
    out = []
    for dec, citation in citations():
        if not isinstance(citation, str):
            continue
        found = QUALIFIED.match(citation)
        if found:
            out.append((str(dec), citation, found.group(1)))
    return out


def legacy() -> list[tuple[str, str]]:
    """(decision id, citation) for every STRING citation that is NOT of the qualified form."""
    return [(str(dec), citation) for dec, citation in citations()
            if isinstance(citation, str) and not QUALIFIED.match(citation)]


class TestAnchorsExist(unittest.TestCase):
    """A guard that reads nothing reports success. These are the assertions that stop it."""

    def test_anchors_exist(self) -> None:
        self.assertTrue(LOG.is_file(), LOG)
        self.assertTrue(STATE.is_file(), STATE)
        rows = entries()
        self.assertGreaterEqual(
            len(rows), ENTRIES_FLOOR,
            f"badf/decision-log.jsonl holds {len(rows)} entries, against a floor of "
            f"{ENTRIES_FLOOR}. Entries are appended and never removed, so a count below the floor "
            f"means the log was truncated or is not being read - either way this module is "
            f"checking less than it should. A floor rather than an equality: limit 7.")
        keys = authority_keys()
        self.assertGreaterEqual(
            len(keys), AUTHORITY_KEYS_FLOOR,
            f"badf/current-state.json's authority block holds {len(keys)} keys, against a floor of "
            f"{AUTHORITY_KEYS_FLOOR}. Rule A resolves against this block and the registry asserts "
            f"one key is ABSENT from it, so an empty or unread block would let BOTH pass while "
            f"checking nothing. Removing an authority key is the operator's and is not routine.")

    def test_every_entry_carries_a_string_authority(self) -> None:
        """A citation of the wrong TYPE fails by name here rather than crashing a reader.

        `re.match` raises `TypeError` on a dict or on `None`, which would report this module as an
        ERROR from the middle of a reader instead of as a failure naming the entry. That is not a
        loophole - the exit code is 1 either way and nothing gets past the guard - but a guard that
        crashes tells a reader less than one that fails, and the entries excluded from both rules
        are exactly the ones a reader most needs named.

        It is not this module's job to enforce the schema: `schemas/decision-record.schema.json`
        requires a non-empty string and `tests/test_badf_match_schemas.py` holds the log to it. This
        assertion exists so that the two guards fail in the same register, and its message says
        which one owns the rule.
        """
        broken = malformed()
        self.assertFalse(
            broken,
            f"these entries carry an id or an authority that is not a non-empty string: "
            f"{[(dec, type(value).__name__) for dec, value in broken]}. Neither Rule A nor Rule B "
            f"can read them, so they are in the corpus and checked by nothing. "
            f"schemas/decision-record.schema.json requires a non-empty string for both and "
            f"tests/test_badf_match_schemas.py enforces it; this assertion is here so that a "
            f"wrong-typed entry is NAMED rather than raising TypeError out of a reader.")


class TestQualifiedCitationsResolve(unittest.TestCase):
    """Rule A: a citation of the qualified form must name a key the record holds."""

    def test_the_qualified_arm_reads_a_real_corpus(self) -> None:
        found = qualified()
        self.assertGreaterEqual(
            len(found), QUALIFIED_CITATIONS_FLOOR,
            f"{len(found)} citations are of the qualified form, against a floor of "
            f"{QUALIFIED_CITATIONS_FLOOR}. Qualified citations are only ever added, so a count "
            f"below the floor means QUALIFIED has stopped matching the corpus and Rule A is "
            f"resolving nothing while passing.")

    def test_no_unregistered_unresolvable_citations(self) -> None:
        """Every qualified citation but the registered one names a key the record holds."""
        keys = authority_keys()
        for dec, citation, key in qualified():
            if dec in UNRESOLVED_CITATIONS:
                continue
            with self.subTest(decision=dec):
                self.assertIn(
                    key, keys,
                    f"{dec} cites {citation!r}, and badf/current-state.json's authority block has "
                    f"no {key!r}. The entry reads as governed while naming no grant, which is the "
                    f"#356 defect. Its keys are {sorted(keys)}. Cite one of those, or record the "
                    f"new grant in the record first - do not file this entry into "
                    f"UNRESOLVED_CITATIONS, which is a ratchet on one merged entry and not a "
                    f"waiver.")

    def test_registered_citations_still_fail(self) -> None:
        """The registered entry is STILL broken, at STILL exactly the registered value.

        Four assertions, and each is a way the registration could stop describing the repository:
        the entry removed, its citation repaired, the record grown the key it names, or a later
        entry superseding it. The last is the repair route #356 item 1 actually names, and it
        touches DEC-118's own line not at all - without it this ratchet would survive the repair it
        is waiting for. A registry entry that passes because its subject is gone is worthless.
        """
        rows = entries()
        by_id = {entry.get("id"): entry for entry in rows}
        superseded = {entry.get("supersedes") for entry in rows if entry.get("supersedes")}
        keys = authority_keys()
        for dec, reg in UNRESOLVED_CITATIONS.items():
            with self.subTest(decision=dec):
                self.assertIn(
                    dec, by_id,
                    f"{dec} is no longer in badf/decision-log.jsonl, so this registration "
                    f"describes nothing. Registered because: {reg['why']}. Remove the entry from "
                    f"UNRESOLVED_CITATIONS.")
                self.assertEqual(
                    reg["citation"], by_id[dec].get("authority"),
                    f"{dec}'s authority is no longer the registered string. It was repaired or "
                    f"reworded, so the registration no longer describes the repository. Registered "
                    f"because: {reg['why']}. Remove the entry from UNRESOLVED_CITATIONS - do not "
                    f"re-register the new value, which would ratchet nothing.")
                found = QUALIFIED.match(reg["citation"])
                self.assertTrue(
                    found,
                    f"UNRESOLVED_CITATIONS[{dec!r}] registers a citation that is not of the "
                    f"qualified form, so Rule A would never have read it and this entry suppresses "
                    f"nothing it needs to suppress")
                self.assertNotIn(
                    found.group(1), keys,
                    f"badf/current-state.json now holds an authority key named "
                    f"{found.group(1)!r}, so {dec}'s citation resolves and is no longer broken. "
                    f"Remove the entry from UNRESOLVED_CITATIONS.")
                self.assertNotIn(
                    dec, superseded,
                    f"a later entry supersedes {dec}, which is the repair route #356 item 1 names. "
                    f"The superseding entry carries the corrected citation and {dec}'s own line is "
                    f"untouched, so nothing else here would notice. Remove the entry from "
                    f"UNRESOLVED_CITATIONS.")


class TestLegacyFormsAreFrozen(unittest.TestCase):
    """Rule B: the bare forms are frozen, which is not the same as validated.

    None of these strings names a file, a block or a key, so no assertion in this class resolves
    anything or says any of the 110 entries was made under a real grant. What is guarded is the
    population: its exact spellings and its exact size, so that a NEW bare-form citation fails and
    its author writes a citation Rule A can check instead.
    """

    def test_the_legacy_forms_are_exactly_these(self) -> None:
        """The exact set of strings QUALIFIED does not match. This is also limit 4's whole basis.

        Everything the qualified pattern does not read arrives here, so this one equality catches
        both of the ways a citation can be unreadable: a NEW bare form, and a citation of a real
        grant written in a shape Rule A does not recognise - `current-state.json authority.x`, a
        URL, a nested path. Neither is skipped, which is what makes an incomplete pattern safe. It
        is also what stops the pattern itself rotting: break QUALIFIED and all nine qualified
        citations arrive here at once.
        """
        found = {citation for _, citation in legacy()}
        self.assertEqual(
            set(LEGACY_CITATIONS), found,
            f"the set of authority strings that are NOT of the qualified form has changed. "
            f"Registered {sorted(LEGACY_CITATIONS)}; found {sorted(found)}. A bare form names no "
            f"file, no block and no key, so nothing can resolve it and nothing here tries - which "
            f"is why the set is frozen. A citation of a real grant that landed here instead is "
            f"written in a shape Rule A does not read. Either way: write it as "
            f"'badf/current-state.json authority.<key>', exactly.")

    def test_the_legacy_population_is_frozen(self) -> None:
        counts: dict[str, int] = {}
        for _, citation in legacy():
            counts[citation] = counts.get(citation, 0) + 1
        for form, expected in LEGACY_CITATIONS.items():
            with self.subTest(form=form):
                self.assertEqual(
                    expected, counts.get(form, 0),
                    f"{counts.get(form, 0)} entries cite {form!r}, against {expected} registered. "
                    f"This is a legacy population and it is frozen: a new entry may not join it. "
                    f"If an entry was added, cite 'badf/current-state.json authority.<key>' "
                    f"instead; if one was removed, the log is append-only and something is wrong.")
        self.assertEqual(
            LEGACY_ENTRIES, len(legacy()),
            f"{len(legacy())} entries carry an unqualified authority string, against "
            f"{LEGACY_ENTRIES} registered. The per-form counts above name which moved.")


class TestTheRegistryIsARatchet(unittest.TestCase):
    """Membership is asserted, so a new unresolvable citation cannot be quieted by filing it in."""

    def test_the_registry_is_exactly_this(self) -> None:
        self.assertEqual(
            {"DEC-118"}, set(UNRESOLVED_CITATIONS),
            "UNRESOLVED_CITATIONS changed. An entry may only LEAVE, when its subject is repaired "
            "or superseded. Filing a NEW unresolvable citation in here would turn a ratchet on one "
            "merged entry into a waiver for the defect it exists to stop.")
        self.assertEqual(
            1, len(UNRESOLVED_CITATIONS),
            f"UNRESOLVED_CITATIONS holds {len(UNRESOLVED_CITATIONS)} entries against 1 registered. "
            f"An equality, not a floor: a registry that may only grow is not a ratchet.")

    def test_every_registration_gives_a_reason(self) -> None:
        """As tests/test_stale_records.py and tests/test_btg1_matrix_reconciles.py require of theirs."""
        for dec, reg in UNRESOLVED_CITATIONS.items():
            with self.subTest(decision=dec):
                self.assertGreater(
                    len(reg["why"].split()), 12,
                    f"UNRESOLVED_CITATIONS[{dec!r}] has no real reason; a registry entry without "
                    f"one is a suppression")
                self.assertRegex(
                    dec, r"^DEC-\d{3}$",
                    f"UNRESOLVED_CITATIONS is keyed by decision id; {dec!r} is not one")


if __name__ == "__main__":
    unittest.main()
