"""Two gate namespaces exist and must never be confused.

`ENG-G0…ENG-G8` are the Work Package delivery lifecycle. `BT-G0…BT-G6` are BizTrust
platform capability gates. `DELIVERY_PLAN.md` says of them: "Two gate systems exist and
must never be confused."

Before #40 the guide used the bare form `G0…G8`, so `G0` meant "Discover" in the guide
and `BT-G0` meant "Architecture Ready" in the delivery plan. #40 renamed 11 occurrences
and left the invariant unguarded: `SOURCE_RECONCILIATION.md` §2 records the counts as a
measurement, not as something that fails. This module makes it fail.

A reintroduced bare `G0` is not a typo. It silently merges two namespaces that gate
different things, and neither `html-refs`, nor the spine test, nor the duplication
detector can see it.

THE REGEX TRAP, documented because it already cost one round:

    $ echo 'BT-G0 and ENG-G3' | grep -o '\\bG[0-8]\\b'
    G0
    G3

`-` is a word boundary, so `\\bG[0-8]\\b` matches INSIDE `BT-G0` and `ENG-G0` and reports
phantom bare gates after a perfectly correct rename. The acceptance criteria on #34 said
exactly that and were unusable; the engineer was right to re-derive instead of satisfying
them. Use a lookbehind that excludes `-`. `test_the_naive_regex_would_be_wrong` pins this
so the next person cannot repeat it.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The published guide surface. `docs/architecture/` is excluded on purpose: the
# architecture pack legitimately owns `BT-G*`, and mixing the two sets here would
# make the disjointness check assert against its own subject.
GUIDE = (
    [ROOT / "index.html", ROOT / "README.md", ROOT / "AGENTS.md"]
    + sorted((ROOT / "stages").glob("*.html"))
    + sorted((ROOT / "reference").glob("*.html"))
    + sorted(p for p in (ROOT / "docs").glob("*.md"))
)

BARE = re.compile(r"(?<![-\w])G[0-8]\b")
LIFECYCLE = re.compile(r"\bENG-G[0-8]\b")
CAPABILITY = re.compile(r"\bBT-G[0-6]\b")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


class TestGateNamespaces(unittest.TestCase):
    def test_the_guide_surface_is_findable(self) -> None:
        """Positive control. If GUIDE silently empties - a rename, a moved directory -
        every assertion below passes vacuously and hardest at the moment it stops
        checking."""
        present = [p for p in GUIDE if p.is_file()]
        self.assertGreaterEqual(len(present), 12, f"guide surface looks unresolved: {present}")
        self.assertTrue(any(LIFECYCLE.search(read(p)) for p in present),
                        "no ENG-G* found anywhere; either the rename was reverted "
                        "or this test is looking at the wrong files")

    def test_the_naive_regex_would_be_wrong(self) -> None:
        """Pin the trap itself, so the fix cannot be un-fixed by a 'simplification'."""
        sample = "BT-G0 and ENG-G3 and a real bare G5"
        self.assertEqual(["G0", "G3", "G5"], re.findall(r"\bG[0-8]\b", sample),
                         "if this changes, the naive form stopped over-matching and the "
                         "warning in this module needs revisiting")
        self.assertEqual(["G5"], BARE.findall(sample),
                         "the guarding regex must match only the genuinely bare gate")

    def test_no_bare_lifecycle_gate_identifier(self) -> None:
        offenders = []
        for path in GUIDE:
            for line_no, line in enumerate(read(path).splitlines(), start=1):
                for hit in BARE.findall(line):
                    offenders.append(f"{path.relative_to(ROOT)}:{line_no}: bare {hit}")
        self.assertEqual(
            [], offenders,
            "lifecycle gates must be written ENG-G<n>. A bare G<n> collides with the "
            "architecture pack's BT-G<n>, which gates something else:\n  "
            + "\n  ".join(offenders),
        )

    def test_gate_namespaces_are_disjoint(self) -> None:
        """No guide file may carry a bare gate alongside a prefixed one. That state is
        worse than uniformly-bare: it looks deliberate."""
        mixed = [
            str(path.relative_to(ROOT))
            for path in GUIDE
            if BARE.search(read(path)) and (LIFECYCLE.search(read(path))
                                            or CAPABILITY.search(read(path)))
        ]
        self.assertEqual([], mixed, f"bare and prefixed gate forms in one file: {mixed}")


if __name__ == "__main__":
    unittest.main()
