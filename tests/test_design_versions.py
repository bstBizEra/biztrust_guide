#!/usr/bin/env python3
"""A design's version agrees with its own `Landed by` row.

NOT ADOPTED. The rule this module holds is #316's recommendation, and #316 is an OPEN
`wayfinder:grilling` ticket with no answer from the operator. AGENTS.md: "Approval | Explicit
authority record; never inferred". This module and the README paragraph it enforces are prepared
and must not land until #316 is answered; the branch is a draft for that reason. The one part
that stands on its own is P0.12's corrected row, which git settles whatever rule is chosen.

The pack's README was silent on when a version moves and what `Landed by` records, and the
silence was filled in by practice until WP-101 repaired forty-eight broken links across all
fourteen files of the pack - thirteen designs and the README - moved no version and added itself
to no row. Its review accepted that judgement
and asked for the gap to be named; #316 named it; WP-108 wrote the two rules into README section
4.1. This module holds the half a test can hold.

  Held here     A version agrees with its own `Landed by` row: the last version that row names is
                the version the design carries, and a design whose row names none is at `0.1`.
                Every revision entry names the version it moved to. Every Work Package named
                exists as a checkpoint.

  NOT held here Whether a change altered a claim. "A version moves when what the design says
                changes" is a rule for a reviewer, and no test can tell a repaired link from a
                withdrawn control. That is stated in the README as the sharp rule precisely
                because nothing mechanical can enforce it.

WHAT THIS FOUND. Of the thirteen `Landed by` rows, EIGHT carry a revision, holding NINE revision
entries between them, and eight of those nine name the version they moved to - "revised to `0.2`
by `BIZTRUST-GUIDE-WP-088`". The ninth, in P0.12's row, read "revised by
`BIZTRUST-GUIDE-WP-075` from the research of #240" and named no version, while git shows that
package moving the design from `0.1` to `0.2` in c3e255a: c3e255a~1 carries `| Version | 0.1 |`
and c3e255a carries `0.2`. The row was completed by WP-108, which is a correction to the design's
own history rather than a change to what the design says, so no version moved for it.

(This paragraph first said "twelve of the thirteen rows" name their version. That counted the
five rows carrying no revision at all as having done it correctly; they did nothing. The figure
is seven of eight rows, or eight of nine entries. It was the fifth count this author published
from a reading rather than from a measurement, and review caught it.)

That is also why the rule is worth having as a rule: the pack's practice was consistent in every
entry but one, and nothing would have said which one.

Positive controls, by name: every design must be found, and the set of designs carrying a
revision is asserted, so a row losing its revision clause fails rather than passing quietly.

Negative controls (run 2026-09-07 under WP-108, each on a copied tree, run as
`unittest discover -s tests -p test_design_versions.py` from that tree's root):
  * A version bumped with no matching revision entry  -> test_version_agrees_with_landed_by
  * A revision entry naming no version                -> test_every_revision_names_its_version
  * A revision entry naming a version the design does -> test_version_agrees_with_landed_by
    not carry
  * Two revisions naming the same version              -> test_versions_only_go_forward
  * A row whose revisions run backward                 -> test_versions_only_go_forward
  * A second `| Landed by |` row on one design         -> test_every_design_is_readable
  * A design's revision clause removed entirely       -> test_the_same_designs_carry_revisions
  * A Landed-by row naming a Work Package with no     -> test_every_named_work_package_exists
    checkpoint

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "docs" / "architecture" / "p0"
CHECKPOINTS = ROOT / "sessions" / "checkpoints"

LANDED_BY = re.compile(r"^\| Landed by \| (.+?) \|$", re.M)
# A suffix is permitted: `1.0-draft` is a form this repository already uses.
VERSION = re.compile(r"^\| Version \| `([0-9.]+(?:-[a-z]+)?)` \|$", re.M)
WORK_PACKAGE = re.compile(r"`(BIZTRUST-GUIDE-WP-\d+)`")
# "revised to `0.2` by `WP-088`"; the continuation a second revision takes, "and to `0.3` by
# `WP-095`"; and "revised by `WP-075`", the shape that names no version and is the defect this
# module catches. A CONTINUATION MUST NAME ITS VERSION: an earlier form allowed "and by `WP-x`",
# which read a row's descriptive prose - "reviewed by `WP-097` and by `WP-101`" - as a revision.
# A guard that fails on correct content is worse than one that misses incorrect content.
REVISION = re.compile(
    r"(?:revised(?:\s+to\s+`([0-9.]+)`)?|and\s+to\s+`([0-9.]+)`)\s+by\s+`(BIZTRUST-GUIDE-WP-\d+)`"
)


def revisions(row: str) -> list[tuple[str, str]]:
    """(version or "", package) for each revision a Landed-by row records."""
    return [(started or continued, package) for started, continued, package in REVISION.findall(row)]

# Designs whose Landed-by row records at least one revision. Asserted by name: a row that loses
# its revision clause would otherwise make every rule here quieter rather than failing.
REVISED = (
    "P0.02-repository-and-boundaries.md", "P0.04-tenant-mapping.md", "P0.05-tenant-provisioning.md",
    "P0.06-tenancy-data-model.md", "P0.07-rls-enforcement.md", "P0.08-api-conventions.md",
    "P0.10-audit-framework.md", "P0.12-secrets-and-configuration.md",
)
FIRST_VERSION = "0.1"


def designs() -> list[Path]:
    return sorted(PACK.glob("P0.*.md"))


def landed_by(text: str) -> str:
    """The one Landed-by row. Reading only the first hid a second row entirely."""
    found = LANDED_BY.findall(text)
    if len(found) != 1:
        return ""
    return found[0]


def version(text: str) -> str:
    found = VERSION.search(text)
    return found.group(1) if found else ""


class TestTheReaderReadsSomething(unittest.TestCase):
    def test_every_design_is_readable(self) -> None:
        found = designs()
        self.assertEqual(13, len(found), "the pack no longer holds thirteen designs")
        for path in found:
            with self.subTest(design=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertNotEqual("", version(text), f"{path.name} states no version")
                self.assertEqual(
                    1, len(LANDED_BY.findall(text)),
                    f"{path.name} does not have exactly one Landed by row; a second row is not read "
                    f"by anything here and would carry claims nothing checks",
                )

    def test_the_same_designs_carry_revisions(self) -> None:
        carrying = tuple(
            p.name for p in designs() if revisions(landed_by(p.read_text(encoding="utf-8")))
        )
        self.assertEqual(
            tuple(sorted(REVISED)), tuple(sorted(carrying)),
            "the set of designs recording a revision has changed. One that has gone may have lost "
            "its revision clause rather than its revision; one that has appeared needs adding to "
            "REVISED deliberately.",
        )


class TestAVersionAgreesWithItsRow(unittest.TestCase):
    def test_every_revision_names_its_version(self) -> None:
        """README 4.1: `Landed by` names each package that moved the version, and the version.

        P0.12's row named a package and no version until WP-108, while git showed that package
        moving the design from 0.1 to 0.2. Twelve rows did it correctly and one did not, which is
        exactly the kind of thing a rule written down and held stops recurring.
        """
        for path in designs():
            row = landed_by(path.read_text(encoding="utf-8"))
            for moved_to, package in revisions(row):
                with self.subTest(design=path.name, package=package):
                    self.assertNotEqual(
                        "", moved_to,
                        f"{path.name}: '{package}' is recorded as revising the design and names no "
                        f"version. Write 'revised to `X.Y` by `{package}`', or if it moved no "
                        f"version it does not belong in Landed by at all (README 4.1).",
                    )

    def test_version_agrees_with_landed_by(self) -> None:
        """The version a design carries is the last one its own row names."""
        for path in designs():
            text = path.read_text(encoding="utf-8")
            row = landed_by(text)
            named = [v for v, _ in revisions(row) if v]
            with self.subTest(design=path.name):
                expected = named[-1] if named else FIRST_VERSION
                self.assertEqual(
                    expected, version(text),
                    f"{path.name} carries version {version(text)} and its Landed by row "
                    f"{'last names ' + named[-1] if named else 'names no revision, so it should be ' + FIRST_VERSION}. "
                    f"A version moves when what the design says changes, and the row records the "
                    f"package that moved it (README 4.1).",
                )

    def test_versions_only_go_forward(self) -> None:
        """A row's revisions climb. Backward or repeated versions passed an earlier form."""
        for path in designs():
            row = landed_by(path.read_text(encoding="utf-8"))
            named = [v for v, _ in revisions(row) if v]
            with self.subTest(design=path.name):
                ordered = sorted(named, key=lambda v: [int(n) for n in v.split("-")[0].split(".")])
                self.assertEqual(ordered, named, f"{path.name}: revisions do not climb: {named}")
                self.assertEqual(len(set(named)), len(named), f"{path.name}: two packages claim the same version: {named}")

    def test_every_named_work_package_exists(self) -> None:
        """A row cites Work Packages; each should have left a checkpoint behind."""
        for path in designs():
            row = landed_by(path.read_text(encoding="utf-8"))
            packages = sorted(set(WORK_PACKAGE.findall(row)))
            with self.subTest(design=path.name):
                self.assertNotEqual([], packages, f"{path.name}'s Landed by row names no Work Package")
                missing = [
                    p for p in packages
                    if not list(CHECKPOINTS.glob(f"{p}-*.json"))
                ]
                self.assertEqual([], missing, f"{path.name} names {missing}, which left no checkpoint")


if __name__ == "__main__":
    unittest.main(verbosity=2)
