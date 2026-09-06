#!/usr/bin/env python3
"""A design under docs/architecture/p0/ never counts one set two ways.

This is not one of the pack README's rules, which is why it is not in tests/test_p0_design_pack.py:
that module holds every design to the template the README fixes, and reads its rules from the README.
This module holds one rule the README does not state and the pack's own history earned.

WP-096 corrected a design that contradicted itself. The P0.12 design at 0.3 said four operator-invoked
runs read the Management API credential and, two dozen lines later, refused the credential's use
"outside those three runs". It reached main because the only check of that kind was a person reading,
and a person reading does not rerun.

The blanket rule -- a design must not count one noun two ways -- is false of this pack, and was probed
before being rejected: the P0.2 design counts two packages of documents and four packages created by a
Work Package; it counts its own seven boundary rules and the two rules a checker's configuration grows
by; the P0.4 design counts four ticket outcomes and the five its own next sentence makes of them. Each
is two sets, not a contradiction.

What holds is the back-reference. "Those N nouns" and "these N nouns" point back at a set the design has
already counted, so a second count of that noun in the same file contradicts the pointer rather than
counting a second set. A design whose back-reference cannot agree should name its set instead of
counting it; there is no allow-list.

Markdown is normalised away before the text is read, because this pack backticks and bolds its names
throughout and "those three `runs`" is the same sentence as "those three runs". The noun is the word
after the number, of two letters or more, so that an article is never read as the noun: this pack
already writes "gives two a screen", and "those two a screen" must not be held on "a".

Negative controls (run 2026-09-06 under WP-097, on in-memory copies):
  * P0.12 as it stood at df6115e, before WP-096   -> test_back_references_agree FAILS
    ("those three runs" against "four runs read it")
  * the same text with the noun backticked        -> test_back_references_agree FAILS
    (the rule read markdown before the WP-097 review; it does not now)
Positive control: at least one design must exist, and the pack at bb6a1f3 holds two back-references,
"those four runs" and "those two roles", both agreeing with their file.

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "docs" / "architecture" / "p0"

NUMBER_WORDS = ("one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|"
                "fifteen|sixteen|seventeen|eighteen|nineteen|twenty")
MARKUP = re.compile(r"[`*]+")
BACK_REFERENCE = re.compile(rf"\b(?:those|these)\s+({NUMBER_WORDS})\s+([a-z][a-z-]+)\b", re.I)


def plain(text: str) -> str:
    """The text with backticks and asterisks removed, so styling cannot hide a count.

    Underscores are left alone: an underscore is a word character, so it never stood between a
    number and its noun, and removing it would only join the halves of a snake_case name.
    """
    return MARKUP.sub("", text)


def counts_of(text: str, noun: str) -> set[str]:
    """Every number word this text attaches to `noun`, lowercased."""
    return {m.group(1).lower() for m in re.finditer(rf"\b({NUMBER_WORDS})\s+{re.escape(noun)}\b", text, re.I)}


def disagreements(text: str) -> list[tuple[str, str, set[str]]]:
    """Each 'those N nouns' whose noun this text also counts differently: (number, noun, other counts)."""
    text = plain(text)
    found = []
    for m in BACK_REFERENCE.finditer(text):
        number, noun = m.group(1).lower(), m.group(2).lower()
        others = counts_of(text, noun) - {number}
        if others:
            found.append((number, noun, others))
    return found


def designs() -> list[Path]:
    return sorted(p for p in PACK.glob("P0.*.md"))


class TestTheRuleReadsWhatItClaims(unittest.TestCase):
    def test_a_design_exists(self) -> None:
        self.assertGreaterEqual(len(designs()), 1, "no design has landed under docs/architecture/p0/")

    def test_a_disagreement_is_found(self) -> None:
        text = "Four runs read it.\n\nMay not be used outside those three runs."
        self.assertEqual([("three", "runs", {"four"})], disagreements(text))

    def test_markdown_does_not_hide_a_disagreement(self) -> None:
        text = "`Four` runs read it.\n\nMay not be used outside those three **runs**."
        self.assertEqual([("three", "runs", {"four"})], disagreements(text),
                         "styling around a number or a noun must not hide a back-reference")

    def test_an_article_is_never_read_as_the_noun(self) -> None:
        text = "P0 gives two a screen. Those two a screen are the ones above; three a screen exist."
        self.assertEqual([], disagreements(text), "an article after the number is not a noun")

    def test_two_sets_of_the_same_noun_are_not_a_disagreement(self) -> None:
        text = "Two packages hold the documents. The Work Package created four packages."
        self.assertEqual([], disagreements(text), "only a back-reference is held, never a bare second count")


class TestEveryDesignAgreesWithItself(unittest.TestCase):
    def test_back_references_agree(self) -> None:
        for p in designs():
            with self.subTest(design=p.name):
                for number, noun, others in disagreements(p.read_text(encoding="utf-8")):
                    self.fail(f"{p.name}: 'those {number} {noun}' points back at a set this design counts as "
                              f"{' and '.join(sorted(others))}; one of them is wrong, or the back-reference should "
                              f"name its set rather than count it")


if __name__ == "__main__":
    unittest.main()
