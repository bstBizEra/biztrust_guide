#!/usr/bin/env python3
"""Detect restated guidance across stage pages.

`operate.html` declared the rule — other stages must link rather than restate —
and `assure.html` violated it anyway. A declared rule caught nothing, because
nothing failed when two pages disagreed. This is the mechanical form.

CALIBRATION, against the drift that actually shipped rather than a guess:

    the drift pair, as it stood on main          0.741
    highest scoring pair on the corrected tree   0.579
    THRESHOLD                                    0.70

So the check fires on the defect that occurred and stays silent on the
deliberate cross-references and parallel ledes that remain. If a legitimate
pair ever scores above the threshold, add it to DELIBERATE_PARALLELS with a
reason — never raise the threshold, which would silently retire the check.

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import difflib
import itertools
import re
import unittest
from pathlib import Path

STAGES = Path(__file__).resolve().parents[1] / "stages"

THRESHOLD = 0.70
MIN_WORDS = 8

# Pairs that are similar on purpose. Each needs a reason, and the reason must
# say why linking is not the right answer.
DELIBERATE_PARALLELS: list[tuple[str, str]] = [
    # The stage ledes share a rhetorical frame ("X is where a change stops
    # being A and becomes B"). That parallelism is the point; it is not
    # restated guidance, and neither page could link to the other for it.
    ("is where a change stops being", "is where a change stops being"),
]


def body_elements(path: Path) -> list[str]:
    """Normalised text of each leaf element: <td>, <li>, <p>, <label>.

    A SECOND granularity, because the sentence splitter below is blind to a
    shape it cannot see from inside: a table row's cells strip into one long
    run with no terminal punctuation, so a cell-for-cell lift of another
    page's roles table never becomes a comparable unit. That is exactly how a
    lifted "Accepting authority" row survived both a shingle check and the
    sentence pass here. Found by an agent re-implementing this detector and
    disagreeing with it.
    """
    html = path.read_text(encoding="utf-8")
    match = re.search(r"<main\b.*?>(.*)</main>", html, re.S)
    body = match.group(1) if match else html
    body = re.sub(r"<(script|style).*?</\1>", " ", body, flags=re.S)
    units = []
    for chunk in re.findall(r"<(?:td|li|p|label)\b[^>]*>(.*?)</(?:td|li|p|label)>", body, re.S):
        text = re.sub(r"<[^>]+>", " ", chunk)
        text = text.replace("&ndash;", "-").replace("&nbsp;", " ").replace("&amp;", "&")
        text = re.sub(r"\s+", " ", text).strip().lower()
        text = re.sub(r"[^a-z0-9 ]", "", text)
        if len(text.split()) >= MIN_WORDS:
            units.append(text)
    return units


def body_sentences(path: Path) -> list[str]:
    """Normalised sentences from a page's <main>, long enough to be meaningful."""
    html = path.read_text(encoding="utf-8")
    match = re.search(r"<main\b.*?>(.*)</main>", html, re.S)
    body = match.group(1) if match else html
    body = re.sub(r"<(script|style).*?</\1>", " ", body, flags=re.S)
    # Strip the section-heading blocks. Every page carries the same spine
    # ("01 / Preconditions / Entry criteria"), which is the shared PATTERN and
    # not restated guidance - leaving it in makes the structure look like
    # duplication and trains a reader to ignore the check.
    body = re.sub(r'<div class="section-heading">.*?</div>\s*</div>', " ", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    body = body.replace("&ndash;", "-").replace("&nbsp;", " ").replace("&amp;", "&")
    sentences = []
    for raw in re.split(r"(?<=[.!?])\s+", body):
        text = re.sub(r"\s+", " ", raw).strip().lower()
        text = re.sub(r"[^a-z0-9 ]", "", text)
        if len(text.split()) >= MIN_WORDS:
            sentences.append(text)
    return sentences


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.split(), b.split()).ratio()


def is_deliberate(a: str, b: str) -> bool:
    return any(fa in a and fb in b for fa, fb in DELIBERATE_PARALLELS)


class TestNoCrossPageDuplication(unittest.TestCase):
    def setUp(self) -> None:
        self.pages = {p: body_sentences(p) for p in sorted(STAGES.glob("*.html"))}
        self.elements = {p: body_elements(p) for p in sorted(STAGES.glob("*.html"))}

    def test_pages_exist_and_have_content(self) -> None:
        """A detector over zero pages passes trivially and proves nothing."""
        self.assertGreaterEqual(len(self.pages), 6, "expected the stage manuals to be present")
        for path, sentences in self.pages.items():
            self.assertGreater(
                len(sentences), 15, f"{path.name}: too little body prose to check meaningfully"
            )

    def test_no_stage_restates_another_element_for_element(self) -> None:
        """Catches a lifted table row, which the sentence pass cannot see."""
        self._assert_no_duplicates(self.elements, "element")

    def test_no_stage_restates_another(self) -> None:
        self._assert_no_duplicates(self.pages, "sentence")

    def _assert_no_duplicates(self, corpus: dict, level: str) -> None:
        offenders = []
        for (pa, sa), (pb, sb) in itertools.combinations(corpus.items(), 2):
            for x in sa:
                for y in sb:
                    score = similarity(x, y)
                    if score >= THRESHOLD and not is_deliberate(x, y):
                        offenders.append((score, pa.name, pb.name, x, y))
        offenders.sort(reverse=True)
        if offenders:
            report = "\n".join(
                f"\n  {s:.3f}  {a} <-> {b}\n    A: {x[:150]}\n    B: {y[:150]}"
                for s, a, b, x, y in offenders[:10]
            )
            self.fail(
                f"{len(offenders)} cross-page {level}-level near-duplicate(s) "
                f"at or above {THRESHOLD}.\n"
                f"Link to the owning stage instead of restating it:{report}"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
