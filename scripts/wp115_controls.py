#!/usr/bin/env python3
"""Negative controls for BIZTRUST-GUIDE-WP-115's authority-citation guard (#356).

`scripts/wp113_controls.py` is the model and this file follows it: one mutation per fresh copy, the
unmutated copy first and green, every mutation asserting that what it replaces was actually there
so a control cannot quietly become a no-op.

A COPY, NOT A CLONE. `scripts/wp114_controls.py` clones because its subject was git history and a
copy without `.git` answers UNKNOWN to every question it asks. This subject is two tracked JSON
files and one test module, so `shutil.copytree` is right and cheaper; nothing here reads a ref.

Each control copies the repository, applies ONE mutation, runs

    python -m unittest discover -s tests -p test_authority_citations.py -v

from that copy's root, and asserts the NAMED test fails. Four controls expect the suite to stay
GREEN and say why in their own docstrings, and one runs the validator instead of the suite; the
runner fails if any of those goes red, because a control that demonstrates a limit cannot drift
away from the code without this script noticing. Every
mutation asserts that what it replaces was really there - the exact string, or the exact field
value on the exact entry - so a control cannot become a no-op when the tree moves under it.

THE PAIRS. Two controls exist only to make another control's answer mean something, in the shape
WP-113 used for its script controls - the second member removes the guard that makes the first
member's answer what it is, so neither green is green by accident.

  THE ABSENCE PAIR, and it is the reason this runner exists at all. A registry entry that would
  pass when its subject is simply absent is worthless, and this repository has already been holed
  that way once. `dec_118_gone_from_the_log` removes DEC-118 and the suite goes RED; the same
  removal with `test_registered_citations_still_fail` weakened to skip an entry it cannot find runs
  GREEN. The first control alone proves the assertion fires; the pair proves that the weak form of
  the same registry really is the useless thing the module's docstring says it is.

  THE READ-FROM-THE-RECORD PAIR. Rule A reads the record's authority keys from the record. Remove
  `guide_v2_records_drafting` from `badf/current-state.json` and the five entries citing it stop
  resolving, loudly; do the same with `authority_keys()` replaced by a literal copy of today's
  eleven keys and the suite is GREEN over a record that no longer holds the grant. That is what a
  guard carrying its own copy of the keys buys, measured rather than asserted.

THE DECLARED HOLE, and it is demonstrated rather than asserted - the pattern WP-113 and WP-114 both
used for theirs. Rule A resolves a citation against `badf/current-state.json`, a record the citing
package may edit in the SAME COMMIT, and nothing freezes that block. `a_key_minted_and_cited_in_the
_same_tree` adds a key and cites it, and expects the suite to stay GREEN; a VALIDATOR control runs
`scripts/validate_continuity.py` over the same copy and expects `CONTINUITY_VALIDATION=PASS`, because
limit 8 claims both and a limit's claim needs a control per half. If either goes red the hole has
closed and limit 8 must be re-derived rather than deleted. The guard for it is #364 and waits on
#363, which settles which authority vocabulary is canonical.

TWENTY-FOUR CONTROLS. Nineteen expect a named test to fail; four expect the suite to stay GREEN -
the two pair members above, limit 8's declared hole, and a resolvable qualified citation being
added, which is not optional because a guard that rejects legitimate content gets switched off. One
runs the validator rather than the suite.

ISOLATED - exactly one test fails. Twelve of the nineteen:
  * DEC-118's citation copied into a new entry       -> test_no_unregistered_unresolvable_citations
  * a new unresolvable qualified citation            |
  * this package's own DEC-121 made unresolvable     |
  * DEC-118's citation repaired in place             -> test_registered_citations_still_fail
  * DEC-118 superseded by a later entry              |
  * the missing key added to the record              |
  * DEC-118 gone from the log                        |
  * one more entry on an existing bare form          -> test_the_legacy_population_is_frozen
  * one legacy form respelled as another             |
  * a new unresolvable citation filed in             -> test_the_registry_is_exactly_this
  * an authority that is a dict                      -> test_every_entry_carries_a_string_authority
  * an authority that is null                        |
    Both are APPENDED, so no count moves and the type assertion is the only thing that can fail.
    Without it each of these raises TypeError out of a reader and the module reports an ERROR
    rather than naming the entry - the same exit code, and less for a reader to act on.

NOT ISOLATED, and declared rather than trimmed, as `tests/test_stale_records.py` and
`scripts/wp114_controls.py` declare of theirs. What each breaks really does break more than one
rule, and saying otherwise would be false precision:
  * DEC-118 removed from the registry     -> test_no_unregistered_unresolvable_citations and
                                             test_the_registry_is_exactly_this. Both true: the
                                             citation does not resolve, and the registry asserted
                                             as exactly {"DEC-118"} is no longer that.
  * a new bare-form citation              -> test_the_legacy_forms_are_exactly_these and
  * a citation in a third shape           |  test_the_legacy_population_is_frozen. A new spelling
                                             is also a new member of the frozen population.
  * the qualified pattern narrowed        -> four tests. Rule A stops resolving, so all nine
                                             qualified citations arrive in Rule B's arm at once and
                                             the registered entry's own citation stops parsing.
  * the record's authority block emptied  -> test_anchors_exist and
                                             test_no_unregistered_unresolvable_citations
  * the log truncated to five entries     -> five tests, which is the corpus disappearing
  * a grant removed from the record       -> test_anchors_exist and
                                             test_no_unregistered_unresolvable_citations. The key
                                             floor moves and five citations stop resolving.

NOT WIRED INTO CI, deliberately, as wp111 to wp114's runners are not - and unlike theirs the reason
is not runtime, since this module's suite takes under a tenth of a second and the whole run is
under a minute. It is that these are controls on a guard rather than the guard itself: their
results are evidence about the tree at the commit someone last ran them against, and nothing
detects them rotting. A control script nothing runs looks like evidence and is not.

Stdlib only, no network beyond the subprocess it runs. Run it as:

    python scripts/wp115_controls.py [source] [holder]
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PYTHON = sys.executable

MODULE = "tests/test_authority_citations.py"
LOG = "badf/decision-log.jsonl"
STATE = "badf/current-state.json"

REGISTERED = "badf/current-state.json authority.documentation_implementation"
RESOLVES = "badf/current-state.json authority.implementation"


# --- primitives ----------------------------------------------------------------------------------


def edit(root: Path, rel: str, old: str, new: str) -> None:
    """Replace `old` with `new` exactly once, and refuse to be a no-op."""
    path = root / rel
    text = path.read_text(encoding="utf-8")
    found = text.count(old)
    if found != 1:
        raise AssertionError(
            f"{rel}: expected exactly one occurrence of {old[:70]!r}, found {found}")
    path.write_text(text.replace(old, new), encoding="utf-8", newline="")


def read_log(root: Path) -> list[dict]:
    return [json.loads(line) for line in (root / LOG).read_text(encoding="utf-8").splitlines()
            if line.strip()]


def write_log(root: Path, rows: list[dict]) -> None:
    (root / LOG).write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8", newline="")


def entry(dec: str, authority: str, supersedes: str | None = None) -> dict:
    """A well-formed decision entry, so that a control measures the citation and nothing else."""
    return {
        "id": dec,
        "timestamp": "2026-09-09T23:59:59Z",
        "work_package_id": "BIZTRUST-GUIDE-WP-115",
        "type": "TESTING",
        "decision": "A control's entry. Not a decision; it exists to carry one authority string.",
        "rationale": "Written by scripts/wp115_controls.py into a throwaway copy of the tree.",
        "authority": authority,
        "supersedes": supersedes,
    }


def set_authority(root: Path, dec: str, expected: str, new: str) -> None:
    """Retarget one entry's citation, asserting the value it replaces was really there."""
    rows = read_log(root)
    hit = [row for row in rows if row["id"] == dec]
    if len(hit) != 1:
        raise AssertionError(f"{LOG}: expected exactly one {dec}, found {len(hit)}")
    if hit[0]["authority"] != expected:
        raise AssertionError(f"{dec}: expected authority {expected!r}, found {hit[0]['authority']!r}")
    hit[0]["authority"] = new
    write_log(root, rows)


def append(root: Path, row: dict) -> None:
    rows = read_log(root)
    if any(existing["id"] == row["id"] for existing in rows):
        raise AssertionError(f"{LOG}: {row['id']} is already present")
    write_log(root, rows + [row])


def authority_block(root: Path) -> dict:
    return json.loads((root / STATE).read_text(encoding="utf-8"))["authority"]


def rewrite_authority(root: Path, block: dict) -> None:
    state = json.loads((root / STATE).read_text(encoding="utf-8"))
    state["authority"] = block
    (root / STATE).write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n",
                              encoding="utf-8", newline="")


# --- the mutations -------------------------------------------------------------------------------


def dec_118s_citation_copied_into_a_new_entry(root: Path) -> None:
    """#356's own scenario: DEC-118 is the model and the next author copies it.

    That is not hypothetical - the string was carried into a WP-113 draft for exactly this reason
    and caught in review there. The registration covers DEC-118 and nothing else, so the copy is
    read by Rule A and fails.
    """
    append(root, entry("DEC-900", REGISTERED))


def a_new_unresolvable_citation(root: Path) -> None:
    """The general case: a qualified citation naming a key nobody ever granted."""
    append(root, entry("DEC-900", "badf/current-state.json authority.no_such_grant"))


def this_packages_own_entry_made_unresolvable(root: Path) -> None:
    """DEC-121 must satisfy the rule it introduces, and this measures that it is really checked."""
    set_authority(root, "DEC-121", RESOLVES, "badf/current-state.json authority.testing_scope")


def dec_118_removed_from_the_registry(root: Path) -> None:
    """DEC-118 ITSELF, read by Rule A. The defect the guard exists for, on its live instance.

    `UNRESOLVED_CITATIONS.clear()` runs at import, after the dict is built, so the registry is
    empty by the time any test reads it. NOT ISOLATED, and both failures are true: DEC-118's
    citation does not resolve, and a registry asserted as exactly {"DEC-118"} is no longer that.
    """
    edit(root, MODULE, '\nif __name__ == "__main__":',
         '\nUNRESOLVED_CITATIONS.clear()\n\n\nif __name__ == "__main__":')


def dec_118s_citation_repaired(root: Path) -> None:
    """The ratchet's first clause: repaired in place, the registration must stop matching."""
    set_authority(root, "DEC-118", REGISTERED, RESOLVES)


def dec_118_superseded(root: Path) -> None:
    """The ratchet's fourth clause, and the repair route #356 item 1 actually names.

    A superseding entry carries the corrected citation and leaves DEC-118's own line untouched, so
    the exact-string clause would not notice it. Without the supersedes assertion this registration
    would survive the very repair it is waiting for.
    """
    append(root, entry("DEC-900", RESOLVES, supersedes="DEC-118"))


def the_missing_key_added_to_the_record(root: Path) -> None:
    """The other way the citation stops being broken: the record grows the key it names."""
    block = authority_block(root)
    if "documentation_implementation" in block:
        raise AssertionError(f"{STATE} already holds documentation_implementation")
    block["documentation_implementation"] = "GRANTED_BY_USER_REQUEST_2026_09_03"
    rewrite_authority(root, block)


def dec_118_gone_from_the_log(root: Path) -> None:
    """THE ABSENCE CONTROL. A registry satisfied by its subject's absence is worthless.

    DEC-118's line is REPLACED by a well-formed entry rather than deleted, so the corpus floor is
    not what fails and the failure is the registration itself no longer describing the repository.
    """
    rows = read_log(root)
    hit = [row for row in rows if row["id"] == "DEC-118"]
    if len(hit) != 1:
        raise AssertionError(f"{LOG}: expected exactly one DEC-118, found {len(hit)}")
    rows[rows.index(hit[0])] = entry("DEC-900", RESOLVES)
    write_log(root, rows)


def dec_118_gone_and_the_registry_weakened(root: Path) -> None:
    """THE PAIR: expects GREEN. The weak form of this registry, and what it costs.

    One `continue` turns "the registered entry is still broken" into "the registered entry is
    still broken IF IT IS STILL THERE" - which is the shape that holed an earlier module in this
    repository and went green while the defect it named had been repaired. If this control ever
    goes RED the weakening has stopped being a weakening and this pair must be re-derived.
    """
    dec_118_gone_from_the_log(root)
    edit(root, MODULE,
         "                self.assertIn(\n"
         "                    dec, by_id,\n",
         "                if dec not in by_id:\n"
         "                    continue\n"
         "                self.assertIn(\n"
         "                    dec, by_id,\n")


def a_new_bare_form(root: Path) -> None:
    """Rule B pushes an author onto the checkable form. NOT ISOLATED and both failures are true:
    the set of unqualified strings has a new member, and the frozen population has grown."""
    append(root, entry("DEC-900", "REVIEWER_JUDGEMENT"))


def one_more_of_an_existing_bare_form(root: Path) -> None:
    """The quieter half of Rule B: a new entry joining a form already in the set changes no
    spelling at all, so the set equality sees nothing and only the counts do."""
    append(root, entry("DEC-900", "IMPLEMENTATION_SCOPE"))


def one_legacy_form_respelled_as_another(root: Path) -> None:
    """The set is unchanged and both counts move. Only the population test can see this."""
    set_authority(root, "DEC-002", "REPOSITORY_CHARTER", "IMPLEMENTATION_SCOPE")


def a_citation_in_a_third_shape(root: Path) -> None:
    """Limit 4, measured. The grant is real and the path is nearly right; QUALIFIED does not read
    it, so it falls into Rule B's arm and the equality there fails it rather than skipping it."""
    append(root, entry("DEC-900", "current-state.json authority.implementation"))


def the_qualified_pattern_broken(root: Path) -> None:
    """A reader scoped to nothing reads nothing and reports success.

    QUALIFIED is narrowed to a path no entry uses, so Rule A resolves nothing. The corpus floor is
    what catches it first, and all nine qualified citations then arrive in Rule B's arm at once.
    """
    edit(root, MODULE,
         r'QUALIFIED = re.compile(r"^badf/current-state\.json authority\.([A-Za-z0-9_]+)$")',
         r'QUALIFIED = re.compile(r"^badf/no-such-record\.json authority\.([A-Za-z0-9_]+)$")')


def a_new_unresolvable_citation_filed_into_the_registry(root: Path) -> None:
    """Membership is asserted so that a new defect cannot be quieted by filing it in.

    The filed entry is genuinely broken, so `test_registered_citations_still_fail` is satisfied by
    it and `test_no_unregistered_unresolvable_citations` skips it. Only the membership equality
    stands between this registry and a waiver.
    """
    append(root, entry("DEC-900", "badf/current-state.json authority.no_such_grant"))
    edit(root, MODULE,
         'UNRESOLVED_CITATIONS: dict[str, dict] = {\n',
         'UNRESOLVED_CITATIONS: dict[str, dict] = {\n'
         '    "DEC-900": {\n'
         '        "citation": "badf/current-state.json authority.no_such_grant",\n'
         '        "why": "a control filing a new unresolvable citation into the registry, which is '
         'exactly what the membership equality exists to refuse, at length",\n'
         '    },\n')


def an_authority_that_is_a_dict(root: Path) -> None:
    """A citation of the wrong TYPE must fail by name, not crash a reader.

    `re.match` raises TypeError on a dict, which would report the module as an ERROR from the middle
    of a reader rather than as a failure naming the entry. The entry is APPENDED, so the corpus
    counts are untouched and the only thing that can fail is the type assertion itself.
    """
    row = entry("DEC-900", RESOLVES)
    row["authority"] = {"key": "implementation"}
    append(root, row)


def an_authority_that_is_null(root: Path) -> None:
    """The other shape of the same defect, and the one a hand-edited record produces."""
    row = entry("DEC-900", RESOLVES)
    row["authority"] = None
    append(root, row)


def the_authority_block_emptied(root: Path) -> None:
    """The record read as empty. NOT ISOLATED, and that is the point.

    A registry that asserts a key is ABSENT is satisfied by a record that is absent too, so the
    anchors are what stop this module passing over a tree it cannot read. Rule A fails here as
    well, loudly, because nothing resolves.
    """
    rewrite_authority(root, {})


def the_log_truncated(root: Path) -> None:
    """The other anchor: a corpus that has stopped being read is not the same as a clean one."""
    write_log(root, read_log(root)[:5])


def a_resolvable_qualified_citation_added(root: Path) -> None:
    """EXPECTS GREEN, and it is not optional. A guard that rejects legitimate content gets switched
    off. Rule A checks a qualified citation; it never rations them."""
    append(root, entry("DEC-900", "badf/current-state.json authority.wayfinder_charting"))


def a_key_minted_and_cited_in_the_same_tree(root: Path) -> None:
    """THE DECLARED HOLE, and this control asserts the suite stays GREEN. Limit 8.

    Rule A resolves a citation against a record the citing package may edit in the same commit, and
    nothing in this repository freezes that block. A key is added to `badf/current-state.json` and
    an entry citing it is appended in the same tree: the pointer resolves, and a self-minted grant
    is indistinguishable here from one an operator gave.

    If this control ever goes RED the hole has closed and limit 8 must be re-derived rather than
    deleted. The guard for it is #364 and must wait on #363, which settles which authority
    vocabulary is canonical; a freeze designed before that would freeze the wrong key set.
    """
    block = authority_block(root)
    if "self_minted_grant" in block:
        raise AssertionError(f"{STATE} already holds self_minted_grant")
    block["self_minted_grant"] = "GRANTED_BY_THIS_VERY_COMMIT"
    rewrite_authority(root, block)
    append(root, entry("DEC-900", "badf/current-state.json authority.self_minted_grant"))


def a_granted_key_removed_from_the_record(root: Path) -> None:
    """THE READ-FROM-THE-RECORD PAIR, first member. Five entries cite guide_v2_records_drafting.

    NOT ISOLATED: the key floor in the anchors moves as well, and both failures are true - the
    record holds fewer grants than the module was written against, and five citations no longer
    resolve.
    """
    block = authority_block(root)
    if "guide_v2_records_drafting" not in block:
        raise AssertionError(f"{STATE} does not hold guide_v2_records_drafting")
    del block["guide_v2_records_drafting"]
    rewrite_authority(root, block)


def a_granted_key_removed_with_the_keys_hardcoded(root: Path) -> None:
    """THE PAIR: expects GREEN. What a guard carrying its own copy of the keys buys.

    The same removal, with `authority_keys()` returning a literal copy of the eleven keys the
    record held when this module was written. Five citations now name a grant the record no longer
    holds and the suite is green over it. That is the whole argument for reading the record, and it
    is measured here rather than asserted in a docstring.
    """
    a_granted_key_removed_from_the_record(root)
    edit(root, MODULE,
         '    block = json.loads(STATE.read_text(encoding="utf-8")).get("authority")\n'
         "    return frozenset(block) if isinstance(block, dict) else frozenset()\n",
         '    return frozenset({"implementation", "repository_publish", '
         '"github_pages_activation",\n'
         '                      "resume_decision_taxonomy", "experiment_rerun",\n'
         '                      "production_platform_implementation", "architecture_acceptance",\n'
         '                      "architecture_drafting_ahead_of_s01", "wayfinder_charting",\n'
         '                      "p0_design_pack_drafting", "guide_v2_records_drafting"})\n')


# (name, mutation, the test that must fail - or None where the suite must stay GREEN)
CONTROLS = [
    ("DEC-118's citation copied into a new entry - #356's own scenario",
     dec_118s_citation_copied_into_a_new_entry, "test_no_unregistered_unresolvable_citations"),
    ("a new unresolvable qualified citation", a_new_unresolvable_citation,
     "test_no_unregistered_unresolvable_citations"),
    ("this package's own entry made unresolvable", this_packages_own_entry_made_unresolvable,
     "test_no_unregistered_unresolvable_citations"),
    ("DEC-118 removed from the registry and read by Rule A", dec_118_removed_from_the_registry,
     "test_no_unregistered_unresolvable_citations"),
    ("DEC-118's citation repaired in place", dec_118s_citation_repaired,
     "test_registered_citations_still_fail"),
    ("DEC-118 superseded by a later entry", dec_118_superseded,
     "test_registered_citations_still_fail"),
    ("the missing key added to the record", the_missing_key_added_to_the_record,
     "test_registered_citations_still_fail"),
    ("THE ABSENCE CONTROL: DEC-118 gone from the log", dec_118_gone_from_the_log,
     "test_registered_citations_still_fail"),
    ("THE PAIR: the same removal with the registry weakened to skip an absent entry",
     dec_118_gone_and_the_registry_weakened, None),
    ("a new bare-form citation", a_new_bare_form, "test_the_legacy_forms_are_exactly_these"),
    ("one more entry on an existing bare form", one_more_of_an_existing_bare_form,
     "test_the_legacy_population_is_frozen"),
    ("one legacy form respelled as another", one_legacy_form_respelled_as_another,
     "test_the_legacy_population_is_frozen"),
    ("a citation in a third shape", a_citation_in_a_third_shape,
     "test_the_legacy_forms_are_exactly_these"),
    ("the qualified pattern narrowed to match nothing", the_qualified_pattern_broken,
     "test_the_qualified_arm_reads_a_real_corpus"),
    ("a new unresolvable citation filed into the registry",
     a_new_unresolvable_citation_filed_into_the_registry, "test_the_registry_is_exactly_this"),
    ("an authority that is a dict rather than a string", an_authority_that_is_a_dict,
     "test_every_entry_carries_a_string_authority"),
    ("an authority that is null", an_authority_that_is_null,
     "test_every_entry_carries_a_string_authority"),
    ("the record's authority block emptied", the_authority_block_emptied, "test_anchors_exist"),
    ("the decision log truncated to five entries", the_log_truncated, "test_anchors_exist"),
    ("A GRANT REMOVED FROM THE RECORD, first of the read-from-the-record pair",
     a_granted_key_removed_from_the_record, "test_no_unregistered_unresolvable_citations"),
    ("THE PAIR: the same removal with the record's keys hardcoded in the module",
     a_granted_key_removed_with_the_keys_hardcoded, None),
    ("EXPECTS GREEN: a resolvable qualified citation added", a_resolvable_qualified_citation_added,
     None),
    ("DECLARED HOLE (limit 8): a key minted and cited in the same tree",
     a_key_minted_and_cited_in_the_same_tree, None),
]

# (name, how to prepare the copy, what the validator's stdout must carry)
#
# ONE CONTROL, and it exists because limit 8 makes a claim about the VALIDATOR and not only about
# this module. A limit that says "the suite is green and the validator PASSes" needs both halves
# measured; the suite half is the control above, and this is the other half.
#
# The copy has no `.git`, so STATE_RECONCILIATION reads UNKNOWN there - WP-113's declared shape for
# a copy rather than a defect, and advisory in any case, since the reconciliation never changes the
# exit code. What is asserted is the verdict the gates are read through.
VALIDATOR_CONTROLS = [
    ("DECLARED HOLE (limit 8): the validator over the same minted tree",
     a_key_minted_and_cited_in_the_same_tree, "CONTINUITY_VALIDATION=PASS"),
]

FAILED = re.compile(r"^(?:FAIL|ERROR): (\w+) ", re.M)


def run_validator(root: Path) -> tuple[int, str]:
    done = subprocess.run(
        [PYTHON, "-B", str(root / "scripts/validate_continuity.py")],
        cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    return done.returncode, done.stdout + done.stderr


def run_suite(root: Path) -> tuple[int, set[str]]:
    done = subprocess.run(
        [PYTHON, "-B", "-m", "unittest", "discover", "-s", "tests",
         "-p", "test_authority_citations.py", "-v"],
        cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    return done.returncode, set(FAILED.findall(done.stdout + done.stderr))


def fresh(source: Path, into: Path, name: str) -> Path:
    root = into / name
    shutil.copytree(source, root,
                    ignore=shutil.ignore_patterns(".git", "_site", "node_modules",
                                                  "__pycache__", "*.pyc"))
    return root


def main() -> int:
    source = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    holder = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(tempfile.mkdtemp())
    holder.mkdir(parents=True, exist_ok=True)
    bad = 0

    code, failures = run_suite(fresh(source, holder, "control_00_unmutated"))
    print(f"[{'PASS' if code == 0 else 'BAD '}] unmutated copy: exit {code}, "
          f"failures {sorted(failures) or 'none'}")
    if code != 0:
        print("       the unmutated copy is already red; every control below proves nothing")
        bad += 1

    for index, (name, mutate, expected) in enumerate(CONTROLS, start=1):
        root = fresh(source, holder, f"control_{index:02d}")
        mutate(root)
        code, failures = run_suite(root)
        if expected is None:
            ok = code == 0 and not failures
            bad += 0 if ok else 1
            print(f"[{'PASS' if ok else 'BAD '}] {name}")
            print(f"       expected the suite to stay GREEN; exit {code}; "
                  f"failed: {sorted(failures) or 'nothing'}"
                  f"{'' if ok else '  <- re-derive the claim this control stands behind'}")
            continue
        ok = code != 0 and expected in failures
        isolated = failures == {expected}
        bad += 0 if ok else 1
        print(f"[{'PASS' if ok else 'BAD '}] {name}")
        print(f"       expected {expected} to fail; exit {code}; "
              f"failed: {sorted(failures) or 'NOTHING'}"
              f"{'' if isolated else '  <- NOT ISOLATED' if ok else ''}")

    for index, (name, mutate, expected) in enumerate(VALIDATOR_CONTROLS, start=1):
        root = fresh(source, holder, f"validator_{index:02d}")
        mutate(root)
        code, out = run_validator(root)
        ok = code == 0 and expected in out
        bad += 0 if ok else 1
        print(f"[{'PASS' if ok else 'BAD '}] {name}")
        print(f"       expected exit 0 and the validator to print {expected!r}; got exit {code} "
              f"and {'it' if expected in out else 'it NOT'} present"
              f"{'' if ok else '  <- the hole has closed; re-derive the limit that declares it'}")

    total = len(CONTROLS) + len(VALIDATOR_CONTROLS)
    print(f"\n{total} controls, {bad} not behaving as declared")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
