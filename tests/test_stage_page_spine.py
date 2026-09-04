#!/usr/bin/env python3
"""Every stage page carries the full spine: entry, outputs, roles, gate, stop.

This is the precondition the exit-gate checks depend on. A rule of the form
"every gate item must name an artifact from the outputs section" cannot be
evaluated at all on a page that has no outputs section - it returns the same
verdict for a well-anchored item and a total orphan, which flags the page
rather than the item. So the structural question is asked first, and alone.

WHAT THIS DOES NOT CHECK, AND WHY
=================================

Four semantic checks were proposed alongside this one. All four were
prototyped against all nine pages and all four were REJECTED on measured
false-positive rates, not on taste. The numbers, at 73 gate items:

  (a) every gate item names an artifact from the outputs section
      44 flags (28 misses + 16 unjudgeable on the two pages with no outputs
      section). Adjudicated: 0 genuine defects, 2 arguable, 42 artifacts of
      wording. "Rollback is described in terms the change actually permits"
      does not contain the string "Rollback strategy"; "Each ADR records
      alternatives" does not contain "ADRs". Loosening the matcher to fix
      that made it unsound: the only word-level match it ever produced bound
      define.html's data-classification item to the WRONG artifact
      ("Requirement register"), because "requirement" and "register" occur in
      different phrases of the same sentence.

  (b) every gate item's subject has a section that explains it
      Flag count is a function of two free parameters with no calibration
      data behind either. Indexing section headings: 28 flags. Indexing
      section bodies: 0 flags at "any content word" and 54 at "all content
      words". Nothing distinguishes the vacuous setting from the noisy one,
      because - unlike the 0.741 drift pair that calibrates the duplication
      check - there is no corpus of known subject-orphans to tune against.

  (c) every gate item names an owner from the roles table
      47 misses of 73. Every one is the same fact: three pages (define,
      discover, learn) adopted a "artifact - role : criterion" convention and
      score 26/26; the other six write impersonally and score 0/47 between
      them. That is a house-style split, not 47 defects. The single apparent
      exception was a substring accident - "Architect" matched inside
      "the architecture" in an item that deliberately says "A named role".

  (d) INVERSE: every artifact and every role is named by some gate item
      Hypothesised to be structural rather than semantic. It is not. Orphan
      artifacts: 23 flags, 21 of them the same wording problem as (a) read
      backwards - release.html's "Smoke evidence" is orphaned only because
      the gate says "Smoke checks ran against the running system". Orphan
      roles: 21 flags, 16 from five pages whose gates name no role at all
      (degenerate in exactly the way (a) is degenerate on a page with no
      outputs section). Restricting to the four pages that demonstrably use
      the role convention leaves ONE flag, build.html's "Implementing agent",
      and that is a false positive: four of build's gate items are the
      implementing agent's obligations, written impersonally.

      (d) did once find a real defect - build.html's exit gate was
      satisfiable with zero review because both reviewer roles were
      gate-invisible. That defect is fixed, and on the corrected tree the
      check's precision is 0 of 1. The finding was worth having; the detector
      is not worth keeping.

A fifth idea was tried here and also dropped: four pages say "All four must
hold" above an entry section containing three <article> criteria. It flagged
4 of 4 pages and was wrong 4 times - the fourth criterion is a
<div class="callout">, not an <article>. It is recorded because it is this
file's own miniature of the failure it exists to avoid.

WHAT IS LEFT is mechanically decidable and, on the current tree, exact.

CALIBRATION
===========

Spine elements are located by the section-heading EYEBROW text, never by
`id`. Keying on `id="produces"` gets two answers wrong on the current nine
pages, in both directions, and `test_eyebrow_keying_is_load_bearing` holds
that rationale to a measurement rather than to this comment.

MIN_ITEMS is 2, uniformly. Observed minima across the tree are far above it:

    entry 3   outputs 5   roles 3   gate 7   stop 5

The margin is deliberate. This asserts that a spine element has substance,
not that it has kept its size - a check on the count would be "a count of
artifacts, not a measurement of behaviour", which is the defect plan.html
itself names and the reason the original rule was rejected. Never raise
MIN_ITEMS to accommodate a page; a section that cannot field two entries has
been gutted, and that is the finding.

KNOWN GAPS
==========

plan.html has NO outputs section. That is real, it is recorded in
KNOWN_GAPS with a reason, and it is the largest structural gap left in the
guide. operate.html had the same gap until WP-033 (issue #55) gave it one; its
entry was deleted then, as the ratchet below demands. It is registered rather than left red because this suite
shares one `unittest discover` run with two others, and a member that is red
on a clean tree takes their signal down with it.

The registry is a ratchet, not an amnesty: `test_known_gaps_are_still_gaps`
FAILS when a listed page gains the element it is excused for, and demands the
entry be deleted. An exemption that cannot expire is how a check gets
retired without anyone deciding to retire it.

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

STAGES = Path(__file__).resolve().parents[1] / "stages"

# Nine pages as of BIZTRUST-GUIDE-WP-010. Asserted as a floor, so a tenth
# stage is checked automatically and a deleted stage fails loudly.
EXPECTED_PAGES = 9

MIN_ITEMS = 2

# key -> (accepted eyebrow texts, human name). The eyebrow is the small
# <p> above the <h2> in a .section-heading block.
SPINE: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("entry", ("preconditions",), "entry section"),
    ("outputs", ("outputs", "what is produced"), "outputs section"),
    ("roles", ("who does what",), "roles table"),
    ("gate", ("transition",), "exit gate"),
    ("stop", ("halt",), "stop conditions"),
)

# (page, spine key) -> why it is absent. Delete an entry the moment the page
# gains the element; test_known_gaps_are_still_gaps will insist on it.
KNOWN_GAPS: dict[tuple[str, str], str] = {
    ("plan.html", "outputs"): (
        "Plan's artifact is the Work Package, described field-by-field under "
        "'Work Package anatomy' (#anatomy) instead of an outputs section. "
        "The content exists; the spine element does not, so nothing on the "
        "page distinguishes a produced artifact from a described concept."
    ),
}

_SECTION = re.compile(r"<section\b([^>]*)>(.*?)</section>", re.S)
_HEADING = re.compile(
    r'<div class="section-heading">.*?<div>\s*<p>(.*?)</p>\s*<h2>(.*?)</h2>', re.S
)
# One counter per list shape a section may use. Counted with max(), not
# sum(): each section has one dominant shape, and max() cannot inflate a
# gutted section past the floor by adding two shapes' partial counts.
_SHAPES = (
    re.compile(r"<label\b"),          # exit-gate checkboxes
    re.compile(r"<article\b"),        # entry criteria
    re.compile(r"<div><span>"),       # definition lists
    re.compile(r"<tbody>(.*?)</tbody>", re.S),  # tables, rows counted below
    re.compile(r"<li\b"),             # stop conditions, check lists
)


def _text(fragment: str) -> str:
    """Tag-stripped, entity-folded, whitespace-collapsed text."""
    out = re.sub(r"<[^>]+>", " ", fragment)
    for entity, char in (
        ("&ndash;", "-"), ("&mdash;", "-"), ("&nbsp;", " "),
        ("&amp;", "&"), ("&quot;", '"'), ("&#39;", "'"),
    ):
        out = out.replace(entity, char)
    return re.sub(r"\s+", " ", out).strip()


def sections(path: Path) -> list[dict]:
    """Every <section> on a page, with its id and its heading eyebrow.

    Stage pages nest no sections (verified: max depth 1 on all nine), so a
    non-greedy match is exact here rather than merely convenient.
    """
    html = path.read_text(encoding="utf-8")
    found = []
    for match in _SECTION.finditer(html):
        attrs, body = match.group(1), match.group(2)
        ident = re.search(r'id="([^"]*)"', attrs)
        heading = _HEADING.search(body)
        found.append({
            "id": ident.group(1) if ident else "",
            "eyebrow": _text(heading.group(1)) if heading else "",
            "h2": _text(heading.group(2)) if heading else "",
            "body": body,
        })
    return found


def item_count(body: str) -> int:
    """Entries in the section's dominant list shape."""
    counts = []
    for shape in _SHAPES:
        if shape.pattern.startswith("<tbody>"):
            counts.append(sum(len(re.findall(r"<tr\b", m)) for m in shape.findall(body)))
        else:
            counts.append(len(shape.findall(body)))
    return max(counts)


def find(page_sections: list[dict], eyebrows: tuple[str, ...]) -> list[dict]:
    return [s for s in page_sections if s["eyebrow"].lower() in eyebrows]


class SpineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.pages = {p.name: sections(p) for p in sorted(STAGES.glob("*.html"))}


class TestCorpusIsPresent(SpineTestCase):
    """Without this, every assertion below passes over an empty dict."""

    def test_stage_pages_are_present(self) -> None:
        self.assertGreaterEqual(
            len(self.pages), EXPECTED_PAGES,
            f"expected at least {EXPECTED_PAGES} stage pages, found "
            f"{sorted(self.pages)} - a deleted page must fail here, not pass "
            f"silently by shrinking the corpus",
        )

    def test_pages_parse_into_sections(self) -> None:
        for name, secs in self.pages.items():
            with self.subTest(page=name):
                self.assertGreaterEqual(
                    len(secs), len(SPINE),
                    f"{name}: parsed {len(secs)} sections, fewer than the "
                    f"{len(SPINE)} the spine requires - if the markup changed "
                    f"shape, the parser is wrong before the page is",
                )
                self.assertTrue(
                    any(s["eyebrow"] for s in secs),
                    f"{name}: no section-heading eyebrow parsed at all; every "
                    f"lookup below would report ABSENT for the wrong reason",
                )


class TestSpinePresence(SpineTestCase):
    def test_every_page_has_each_spine_element(self) -> None:
        missing = []
        for name, secs in sorted(self.pages.items()):
            for key, eyebrows, human in SPINE:
                if find(secs, eyebrows):
                    continue
                if (name, key) in KNOWN_GAPS:
                    continue
                missing.append(
                    f"  {name} has no {human} "
                    f"(no section whose heading eyebrow is one of {list(eyebrows)})"
                )
        if missing:
            self.fail(
                f"{len(missing)} stage page(s) are missing a spine element. Every "
                "page must carry all five, because the gate cannot be evaluated "
                "against outputs and roles that do not exist:\n" + "\n".join(missing)
            )

    def test_spine_element_lookup_is_unambiguous(self) -> None:
        """Two sections answering to one eyebrow makes the lookup arbitrary.

        This is the failure mode that eyebrow-keying trades for: `id` is
        unique by construction, eyebrow text is not. A silent first-match
        would pick a section by document order and report a confident answer
        about the wrong one.
        """
        clashes = []
        for name, secs in sorted(self.pages.items()):
            for key, eyebrows, human in SPINE:
                hits = find(secs, eyebrows)
                if len(hits) > 1:
                    clashes.append(
                        f"  {name}: {len(hits)} sections claim to be the {human} - "
                        f"{[h['id'] or '(no id)' for h in hits]}"
                    )
        self.assertEqual(clashes, [], "ambiguous spine lookup:\n" + "\n".join(clashes))


class TestSpineSubstance(SpineTestCase):
    def test_present_spine_elements_are_not_empty(self) -> None:
        """A section that exists but lists nothing is the emptier failure.

        A check that runs against an empty section reports the same PASS it
        reports against a full one.
        """
        thin = []
        for name, secs in sorted(self.pages.items()):
            for key, eyebrows, human in SPINE:
                for sec in find(secs, eyebrows):
                    n = item_count(sec["body"])
                    if n < MIN_ITEMS:
                        thin.append(
                            f"  {name} #{sec['id'] or '(no id)'} ({human}): "
                            f"{n} item(s), below the floor of {MIN_ITEMS}"
                        )
        if thin:
            self.fail(
                f"{len(thin)} spine element(s) carry no substance. Do not lower "
                f"MIN_ITEMS - the floor is already far below every observed "
                f"section:\n" + "\n".join(thin)
            )

    def test_exit_gate_items_are_checkboxes(self) -> None:
        """The gate's items must be the disabled checkboxes, not prose.

        item_count() accepts five shapes, so a gate whose <label> list was
        replaced by paragraphs would still clear the floor above on some
        other shape. This pins the gate to the one shape that means "an item
        someone ticks".
        """
        for name, secs in sorted(self.pages.items()):
            for sec in find(secs, ("transition",)):
                with self.subTest(page=name):
                    boxes = re.findall(r"<label>\s*<input type=\"checkbox\"", sec["body"])
                    self.assertGreaterEqual(
                        len(boxes), MIN_ITEMS,
                        f"{name} #{sec['id']}: {len(boxes)} gate checkbox(es); the "
                        f"exit gate must list ticked conditions, not prose",
                    )


class TestKnownGapsRatchet(SpineTestCase):
    """The exemption list must be able to shrink, and only to shrink."""

    def test_known_gap_entries_name_a_real_page_and_key(self) -> None:
        valid_keys = {key for key, _, _ in SPINE}
        for (page, key), reason in KNOWN_GAPS.items():
            with self.subTest(gap=(page, key)):
                # assertTrue, not assertIn: assertIn appends a repr of every
                # parsed page to the message and buries the finding.
                self.assertTrue(
                    page in self.pages,
                    f"KNOWN_GAPS names a page that does not exist: {page!r}. "
                    f"Pages present: {sorted(self.pages)}",
                )
                self.assertTrue(
                    key in valid_keys,
                    f"KNOWN_GAPS names an unknown spine key: {key!r}. "
                    f"Valid keys: {sorted(valid_keys)}",
                )
                self.assertGreater(
                    len(reason.split()), 12,
                    f"KNOWN_GAPS[{page}, {key}] must carry a reason, not a shrug",
                )

    def test_known_gaps_are_still_gaps(self) -> None:
        """Fails when a gap is FIXED. That is the point.

        Without this, KNOWN_GAPS becomes permanent cover: the page gains its
        outputs section, nothing changes, and the entry stays forever - which
        is how a check gets retired without anyone deciding to retire it.
        """
        healed = []
        for (page, key), _reason in sorted(KNOWN_GAPS.items()):
            eyebrows = next(e for k, e, _ in SPINE if k == key)
            hits = find(self.pages.get(page, []), eyebrows)
            if hits:
                healed.append(
                    f"  {page} now HAS its {key} section "
                    f"(#{hits[0]['id'] or '(no id)'}) - delete KNOWN_GAPS[('{page}', '{key}')]"
                )
        if healed:
            self.fail(
                "A known gap has been closed. Remove it from the registry so "
                "the page is checked like every other:\n" + "\n".join(healed)
            )


class TestEyebrowKeyingRationale(SpineTestCase):
    """Hold the design decision to a measurement, not to a comment."""

    def test_eyebrow_keying_is_load_bearing(self) -> None:
        """id-keying must still get answers wrong, in both directions.

        If this ever passes trivially, the ids have been normalised and the
        whole eyebrow apparatus can be simplified away - so the assertion is
        written to FAIL at that moment and say so, rather than to sit here
        defending a constraint that no longer exists.
        """
        outputs_eyebrows = next(e for k, e, _ in SPINE if k == "outputs")

        false_absent, false_present = [], []
        for name, secs in sorted(self.pages.items()):
            by_eyebrow = {s["id"] for s in find(secs, outputs_eyebrows)}
            by_id = {s["id"] for s in secs if s["id"] == "produces"}
            for ident in by_eyebrow - by_id:
                false_absent.append(f"{name}#{ident}")
            # An id-keyed rule widened to cover the above would reach for
            # "evidence" next, and collect a section that is not outputs.
            for sec in secs:
                if sec["id"] == "evidence" and sec["id"] not in by_eyebrow:
                    false_present.append(f"{name}#{sec['id']} ({sec['h2']})")

        self.assertTrue(
            false_absent,
            "No page's outputs section has an id other than 'produces' any "
            "more. Eyebrow-keying now buys nothing over id-keying: simplify "
            "SPINE to id lookups and delete this test.",
        )
        self.assertTrue(
            false_present,
            "No page carries a non-outputs section with a colliding id any "
            "more. The second half of the eyebrow-keying rationale has "
            "expired; re-derive it or drop this assertion.",
        )
        # Named, so the failure above is reproducible from the record.
        self.assertEqual(
            false_absent, ["assure.html#evidence"],
            "the set of outputs sections invisible to id-keying changed",
        )
        self.assertEqual(
            false_present,
            ["discover.html#evidence (Evidence sources and their reliability)"],
            "the set of non-outputs sections an id-keyed rule would collect changed",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
