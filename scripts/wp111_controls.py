#!/usr/bin/env python3
"""Negative controls for BIZTRUST-GUIDE-WP-111's tests/test_stale_records.py (#349).

Each control copies the repository to a fresh directory, applies ONE mutation, runs

    python -m unittest discover -s tests -p test_stale_records.py -v

from that copy's root, and asserts that the named test FAILS. The unmutated copy is run first and
must pass; a control set measured against a suite that was already red proves nothing.

Every mutation asserts that the text it is replacing was actually found, so a control cannot
silently become a no-op when the subject record is edited - which is how the first version of that
module shipped five controls that all passed while the guard was not guarding.

One control expects the suite to stay GREEN. It is a DECLARED HOLE - a real defect this module
does not catch - and it exists so that the limit declaring it is demonstrated rather than asserted.
If that control starts failing, the hole has closed and the limit must be re-derived, not deleted.

THE ROT RISK, stated plainly because this file is committed. A control script that nothing runs
looks like evidence and is not: it can drift out of agreement with the module it tests, and a
reader who sees it in the tree will assume it passed. It is DELIBERATELY NOT WIRED INTO CI -
nineteen fresh-copy suite runs is too slow for every push, and the sibling guards' controls
(tests/test_btg1_matrix_reconciles.py, tests/test_stale_asks.py) are not CI-run either; they record
their results in prose. This file is the same evidence in executable form, and it is worth more
than prose ONLY while somebody runs it. Run it before changing tests/test_stale_records.py, and
before believing any sentence that module's docstring states about what it catches. Five of those
sentences have already been measured false.

It lives in scripts/ and not tests/ on purpose: `unittest discover -s tests` must not collect it,
and the test suite's no-subprocess property is a property of tests/, which this file would break.

THE COPY, THE MUTATION HELPER, THE SUITE RUN AND THE REPORTING LOOP now come from
`scripts/control_harness.py` (#368), which classified every divergence across the six runners as
need or drift before moving anything. Four of this runner's differences from its siblings survive
as arguments rather than being flattened into them: a 60-character preview in the mutation
helper's failure message, Python's own newline translation on the write, a narrower copy-ignore
tuple, and no timeout on the suite run. Adoption was gated on this runner's full output being
byte-identical before and after, not on the suite staying green.

Usage:  python scripts/wp111_controls.py [<repository>] [<scratch>]
"""
from __future__ import annotations

from pathlib import Path

from control_harness import (HOLE_DECLARED, arguments, fresh, report_unmutated, run_suite,
                             suite_controls, summarise)
from control_harness import edit as harness_edit

# NARROWER than the harness default, which also drops `_site` and `node_modules`. This runner has
# always copied those when they exist, and what its controls run over is not this package's to
# change.
IGNORE = (".git", "__pycache__", "*.pyc")

REC = "docs/architecture/SOURCE_RECONCILIATION.md"
PLAN = "docs/architecture/BIZTRUST-PLAN-001.md"
MODULE = "tests/test_stale_records.py"
NEXT_STEPS = "docs/NEXT_STEPS.md"

ROW_ADR = (
    "| Required ADR set expanded 12 → 20 | `docs/NEXT_STEPS.md:89` — `ADR-001…012` | "
    "**Deferred**, [issue #35](https://github.com/bstBizEra/biztrust_guide/issues/35) | "
    "pull request #19 / issue #18 owns this file |"
)
ROW_G = (
    "| Gate namespaces `ENG-G*` / `BT-G*` (§2) | `index.html` ×9, "
    "`docs/AGENT_CONTINUITY.md:222` ×2 — bare `G0…G8` | "
    "**Deferred**, [issue #34](https://github.com/bstBizEra/biztrust_guide/issues/34) | "
    "unassigned; #19 / #18 owns `AGENT_CONTINUITY.md` |"
)
ROW_UPDATED = (
    "| Required ADR set expanded 12 → 20 (`ADR_REGISTER.md`, after issue #15) | `index.html` — "
    "repository tree, required outputs, ADR grid, roadmap freeze item, NS-005 council action "
    "(5 sites) | **Updated in this change**; the grid now carries all twenty and links to the "
    "register for status | BIZTRUST-GUIDE-WP-003 |"
)
SECTION_14 = "## 14. What this document does not yet carry"
SOURCES_15 = "\n## 15. Sources"

# A string no tracked file holds. The three F-round controls below swap the reconciled row for a
# NEW `**Deferred**` row waiting on it, which keeps the row count at 3 so that test_anchors_exist
# stays silent and the control measures the reader rather than the corpus floor.
ABSENT = "BT-G9…G12"


def stale_row(claim: str, reference: str) -> str:
    return (f"| {claim} | `{reference}` — bare `{ABSENT}` | "
            f"**Deferred**, [issue #99](https://github.com/bstBizEra/biztrust_guide/issues/99) | "
            f"unassigned |")


def edit(root: Path, rel: str, old: str, new: str) -> None:
    """Replace `old` with `new` exactly once, and refuse to be a no-op.

    Two arguments this runner alone gives the harness: a 60-character preview of `old` in the
    failure message, and `newline=None`, which lets Python translate every line ending in the file
    on the way out. The second is a real difference in the bytes written, not a formatting one,
    which is why it is passed rather than quietly aligned with the other five runners.
    """
    harness_edit(root, rel, old, new, preview=60, newline=None)


# --- the mutations ------------------------------------------------------------------------------


def annotate_status_inside_the_bold_run(root: Path) -> None:
    """`**Deferred (closed by b93c701)**`. GREEN under the first-word comparison."""
    edit(root, REC, ROW_ADR, ROW_ADR.replace("**Deferred**", "**Deferred (closed by b93c701)**"))


def annotate_status_after_the_bold_run(root: Path) -> None:
    """`**Deferred** — resolved 2026-09-05 by b93c701`. GREEN under the first-word comparison."""
    edit(root, REC, ROW_ADR,
         ROW_ADR.replace("**Deferred**,", "**Deferred** — resolved 2026-09-05 by b93c701,"))


def drop_a_file_from_the_row(root: Path) -> None:
    """`index.html` leaves the `G0…G8` row. GREEN while the registered files tuple was read."""
    edit(root, REC, ROW_G, ROW_G.replace("`index.html` ×9, ", ""))


def repoint_the_row_at_a_file_that_holds_the_string(root: Path) -> None:
    """The ADR row now names a file that DOES contain `ADR-001…012`. GREEN, as above."""
    holder = root / REC
    assert "ADR-001…012" in holder.read_text(encoding="utf-8"), "the repoint target must hold it"
    edit(root, REC, ROW_ADR,
         ROW_ADR.replace("`docs/NEXT_STEPS.md:89`", "`docs/architecture/SOURCE_RECONCILIATION.md:89`"))


def delete_a_registered_row(root: Path) -> None:
    edit(root, REC, ROW_G + "\n", "")


def restore_the_string_to_its_file(root: Path) -> None:
    """The defect is genuinely repaired in the FILE while the row still says it is not."""
    path = root / NEXT_STEPS
    path.write_text(path.read_text(encoding="utf-8")
                    + "\n\nThe required ADR set was once written `ADR-001…012`.\n",
                    encoding="utf-8")


def one_bullet_both_landed_and_outstanding(root: Path) -> None:
    """The shape the `if/elif` classifier could not see: one bullet carrying both vocabularies."""
    edit(root, PLAN, SOURCES_15,
         "- **A thirteenth manual**: "
         "[#199](https://github.com/bstBizEra/biztrust_guide/issues/199) is a pointer to section 12 "
         "here, and it has not moved.\n" + SOURCES_15)


def a_bullet_in_unknown_wording(root: Path) -> None:
    edit(root, PLAN, SOURCES_15,
         "- **An appendix**: the finance cell table, transcribed at "
         "[`../research/appendix.md`](../research/appendix.md).\n" + SOURCES_15)


def add_an_entry_to_a_registry(root: Path) -> None:
    edit(root, MODULE, "CONTRADICTED: dict[str, dict] = {",
         "CONTRADICTED: dict[str, dict] = {\n"
         '    "999": {"digests": ("' + "0" * 64 + '",),\n'
         '            "why": ("a new defect filed into the registry instead of being repaired, "\n'
         '                    "which is the one thing a ratchet exists to refuse to absorb")},')


def rename_the_section_14_anchor(root: Path) -> None:
    edit(root, PLAN, SECTION_14, "## 14. What this document does not carry yet")


def rename_the_table_header(root: Path) -> None:
    edit(root, REC, "| Reconciled claim | Published summary | Status | Owner |",
         "| Reconciled claim | Published summary | Reconciliation status | Owner |")


def a_stale_row_naming_a_repo_root_file(root: Path) -> None:
    """F1, the reviewer's exact case: a `**Deferred**` row waiting on `AGENTS.md`.

    GREEN at 6ee0968, because the reader kept a backticked token only if it held "/" or ended
    ".html", so every repo-root record - AGENTS.md, README.md, CHANGELOG.md - was never parsed.
    """
    assert ABSENT not in (root / "AGENTS.md").read_text(encoding="utf-8"), "the target must be absent"
    edit(root, REC, ROW_UPDATED, stale_row("Gate namespaces `BT-G9*` (§3)", "AGENTS.md:12"))


def a_stale_row_whose_file_reference_is_unreadable(root: Path) -> None:
    """The residual of F1: a live row naming a file in a form FILE_REFERENCE does not know.

    `Makefile:3` has no dot-extension. No recogniser is complete, so the guard is that the reader's
    silence is a failure: this must trip test_every_live_row_is_readable rather than pass by being
    skipped, which is what the whole class of F1 defects did.
    """
    edit(root, REC, ROW_UPDATED, stale_row("Build namespaces `BT-G9*` (§3)", "Makefile:3"))


def an_unreadable_reference_beside_a_readable_one(root: Path) -> None:
    """The reviewer's exact case: one unreadable tick hiding behind a sibling that parses.

    GREEN at 5efb267, because the rule asserted only that a live row yielded SOME file. The parse
    kept `docs/architecture/SOURCE_RECONCILIATION.md` and DROPPED `Makefile:3` unchecked, and the
    target `Reconciled claim` really is in that file, so the unregistered arm was satisfied too.
    The same defect as the AGENTS.md case, one size smaller.
    """
    edit(root, REC, ROW_UPDATED,
         "| Gate namespaces `BT-G9*` (§3) | `Makefile:3` ×1, "
         "`docs/architecture/SOURCE_RECONCILIATION.md` ×2 — bare `Reconciled claim` | "
         "**Deferred**, [issue #99](https://github.com/bstBizEra/biztrust_guide/issues/99) | "
         "unassigned |")


def a_negated_status_containing_the_word_updated(root: Path) -> None:
    """`**Not yet Updated**` is not a reconciliation, and must not exempt the row.

    GREEN at a176856, because RECONCILED was a SEARCH over the status cell: any bold run holding
    the word `Updated` exempted the row from check A entirely.
    """
    assert ABSENT not in (root / NEXT_STEPS).read_text(encoding="utf-8"), "the target must be absent"
    edit(root, REC, ROW_UPDATED,
         "| Gate namespaces `BT-G9*` (§3) | `docs/NEXT_STEPS.md:12` — bare `" + ABSENT + "` | "
         "**Not yet Updated**, [issue #99](https://github.com/bstBizEra/biztrust_guide/issues/99) | "
         "unassigned |")


def a_deferred_status_mentioning_another_file_as_updated(root: Path) -> None:
    """A `**Deferred**` row whose status prose says a DIFFERENT file was updated.

    GREEN at a176856, for the same reason: the search found `**Updated in this change**` later in
    the cell and exempted a row that says in its own first words that it is deferred.
    """
    assert ABSENT not in (root / NEXT_STEPS).read_text(encoding="utf-8"), "the target must be absent"
    edit(root, REC, ROW_UPDATED,
         "| Gate namespaces `BT-G9*` (§3) | `docs/NEXT_STEPS.md:12` — bare `" + ABSENT + "` | "
         "**Deferred**, [issue #99](https://github.com/bstBizEra/biztrust_guide/issues/99); "
         "`index.html` was **Updated in this change** but this file was not | unassigned |")


def a_third_status_over_an_absent_string(root: Path) -> None:
    """A row given a status outside the table's vocabulary still has to hold its string.

    This is the control that limit 6 is written from. Limit 6 asserted this behaviour for three
    rounds while RECONCILED was a search; nothing measured it until now.
    """
    assert ABSENT not in (root / NEXT_STEPS).read_text(encoding="utf-8"), "the target must be absent"
    edit(root, REC, ROW_UPDATED,
         "| Gate namespaces `BT-G9*` (§3) | `docs/NEXT_STEPS.md:12` — bare `" + ABSENT + "` | "
         "**Closed**, [issue #99](https://github.com/bstBizEra/biztrust_guide/issues/99) | "
         "unassigned |")


def a_correctly_formed_but_factually_wrong_reconciliation(root: Path) -> None:
    """THE DECLARED HOLE, and this control asserts the suite stays GREEN.

    A row whose status is exactly the reconciled vocabulary is exempt from check A on its own word.
    If that word is false - the file does not hold the string and the row was never really
    reconciled - nothing here notices. Limit 8 is written from this control, and a control that
    demonstrates a hole is worth more than a sentence claiming one.
    """
    assert ABSENT not in (root / NEXT_STEPS).read_text(encoding="utf-8"), "the target must be absent"
    edit(root, REC, ROW_UPDATED,
         "| Gate namespaces `BT-G9*` (§3) | `docs/NEXT_STEPS.md:12` — bare `" + ABSENT + "` | "
         "**Updated in this change**; it was not | unassigned |")


def the_word_updated_in_a_claim_cell(root: Path) -> None:
    """F3: a live row whose CLAIM cell holds a bold `Updated`, on a nested path so F1 is not in play.

    GREEN at 6ee0968, because the status pattern searched the whole ROW rather than the status
    cell, so this row read as already reconciled and was skipped.
    """
    assert ABSENT not in (root / NEXT_STEPS).read_text(encoding="utf-8"), "the target must be absent"
    edit(root, REC, ROW_UPDATED,
         stale_row("Gate namespaces, **register Updated separately**", "docs/NEXT_STEPS.md:12"))


CONTROLS = [
    ("status annotated inside the bold run", annotate_status_inside_the_bold_run,
     "test_registered_rows_still_fail"),
    ("status annotated after the bold run", annotate_status_after_the_bold_run,
     "test_registered_rows_still_fail"),
    ("index.html dropped from the G0-G8 row", drop_a_file_from_the_row,
     "test_registered_rows_still_fail"),
    ("ADR row repointed at a file that holds the string",
     repoint_the_row_at_a_file_that_holds_the_string, "test_registered_rows_still_fail"),
    ("a registered row deleted", delete_a_registered_row, "test_registered_rows_still_fail"),
    ("the string restored to its file", restore_the_string_to_its_file,
     "test_registered_rows_still_fail"),
    ("one bullet citing a ticket as landed AND outstanding",
     one_bullet_both_landed_and_outstanding, "test_no_unregistered_contradictions"),
    ("a bullet in wording neither vocabulary knows", a_bullet_in_unknown_wording,
     "test_every_bullet_is_classified"),
    ("an entry added to a registry", add_an_entry_to_a_registry,
     "test_registries_are_exactly_these"),
    ("the section 14 anchor renamed", rename_the_section_14_anchor, "test_anchors_exist"),
    ("the reconciliation table header renamed", rename_the_table_header, "test_anchors_exist"),
    ("F1: a stale row naming a repo-root file (AGENTS.md)", a_stale_row_naming_a_repo_root_file,
     "test_no_unregistered_stale_rows"),
    ("F1 residual: a live row whose file reference is unreadable",
     a_stale_row_whose_file_reference_is_unreadable, "test_every_live_row_is_readable"),
    ("F3: a bold `Updated` in a live row's claim cell", the_word_updated_in_a_claim_cell,
     "test_no_unregistered_stale_rows"),
    ("NEW: an unreadable reference beside a readable one",
     an_unreadable_reference_beside_a_readable_one, "test_every_live_row_is_readable"),
    ("a negated status: `**Not yet Updated**`", a_negated_status_containing_the_word_updated,
     "test_no_unregistered_stale_rows"),
    ("a `**Deferred**` status whose prose says another file was updated",
     a_deferred_status_mentioning_another_file_as_updated, "test_no_unregistered_stale_rows"),
    ("a third status, `**Closed**`, over an absent string", a_third_status_over_an_absent_string,
     "test_no_unregistered_stale_rows"),
    # HOLE, not a defect: expected GREEN. See a_correctly_formed_but_factually_wrong_reconciliation.
    ("DECLARED HOLE: a correctly formed but factually wrong `**Updated in this change**`",
     a_correctly_formed_but_factually_wrong_reconciliation, None),
]

def run(root: Path) -> tuple[int, set[str]]:
    """The subject module, run inside `root` with NO timeout, as this runner has always run it."""
    return run_suite(root, "test_stale_records.py", timeout=None)


def main() -> int:
    source, holder = arguments(__file__)

    code, failures = run(fresh(source, holder, "control_00_unmutated", ignore=IGNORE))
    bad = report_unmutated(code, failures, "copy")
    bad += suite_controls(CONTROLS,
                          lambda name: fresh(source, holder, name, ignore=IGNORE), run,
                          hole=HOLE_DECLARED)
    return summarise(len(CONTROLS), bad)


if __name__ == "__main__":
    raise SystemExit(main())
