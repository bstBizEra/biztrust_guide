#!/usr/bin/env python3
"""Negative controls for BIZTRUST-GUIDE-WP-113's control page (#352).

`scripts/wp111_controls.py` and `scripts/wp112_controls.py` are the model and this file follows
them: one mutation per fresh copy, the unmutated copy first and green, every mutation asserting
that the text it replaces was actually there so a control cannot quietly become a no-op.

TWO KINDS OF CONTROL.

  SUITE controls copy the repository, apply ONE mutation, run

      python -m unittest discover -s tests -p test_control_page.py -v

  from that copy's root, and assert the NAMED test fails. They mutate the projector, the committed
  page and the workflow alike, because all three are what the module holds.

  SCRIPT controls RUN `python scripts/build_control_page.py` in a fresh copy and assert what the
  written page says. They exist because of limit 1 of `tests/test_control_page.py`: that module
  never executes `observe()`, `read_json` or `build` - the git calls, the validator invocation and
  the file reads - in order to keep THAT MODULE subprocess-free, so a defect living only there is
  invisible to it. (Not `tests/` as a whole: four modules there do call a subprocess, and the list
  is in that module's docstring beside the command that measures it.) They come in TWO PAIRS, and
  in each pair the second member removes the guard that makes the first member's answer what it is,
  so neither green is green by accident.

    THE NO-REPOSITORY PAIR. A fresh copy is made with `shutil.copytree`, which drops `.git`, so the
    copy is NOT a repository: every git fact must degrade to UNKNOWN and the run must still exit 0
    and write a page. That is the degradation CI produces for a different reason -
    `actions/checkout@v7` with no `fetch-depth` gives a shallow clone - and it is the reading a
    published copy of this page will normally carry.

    THE ABSENT-RECORD PAIR. `badf/next-actions.json` is deleted from the copy, and the queue panel
    must render UNKNOWN carrying the reason `read_json` gave. Measured at d38040a, before the
    repair: it rendered an empty queue instead - "No recorded action matches the filter. That is a
    reading of badf/next-actions.json", which was false because nothing had been read - and exit 0.
    The second member restores `build`'s discarding of `read_json`'s reason and shows the same copy
    fall back to "no reason was recorded", so the reason on the page is known to come from
    `read_json` and not from the fallback.

ONE SUITE CONTROL EXPECTS GREEN. It is a DECLARED HOLE - a real defect the test module does not
catch, because of limit 1 - and it is here so that the limit is demonstrated rather than claimed.
If it starts failing, the hole has closed and limit 1 must be re-derived, not deleted.

THE ROT RISK, stated plainly because this file is committed. A control script that nothing runs
looks like evidence and is not. It is DELIBERATELY NOT WIRED INTO CI: every control makes a fresh
copy of the whole tree, and the script controls then run the validator inside it, which is minutes
of work repeated on every push. `scripts/build_control_page.py` also runs inside the Pages workflow,
where a step that flaked would be removed rather than fixed. Run this before changing
`tests/test_control_page.py`, and before believing any sentence that module's docstring states
about what it catches.

It lives in `scripts/` and not `tests/` on purpose: `unittest discover -s tests` must not collect
it, and the suite's no-subprocess property is a property of `tests/`, which this file would break.

Usage:  python scripts/wp113_controls.py [<repository>] [<scratch>]
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

PROJECTOR = "scripts/build_control_page.py"
PAGE = "control/index.html"
WORKFLOW = ".github/workflows/pages.yml"
STATE = "badf/current-state.json"
ACTIONS = "badf/next-actions.json"

# --- the exact text each mutation replaces -------------------------------------------------------

DOMAIN_RULE = (
    '    head, sep, _ = key.partition("_")\n'
    "    if not sep or not head:\n"
    "        return None\n"
    "    return head\n"
)
GROUP_VALUE = "        value = raw if isinstance(raw, str) else UNKNOWN\n"
GROUP_APPEND = "            grouped.setdefault(domain, []).append((key, value))\n"
AUTHORITY_TOKENS = 'AUTHORITY_TOKENS = ("HUMAN", "WAIT")'
QUEUE_RETURN = (
    "    return ([row for row in ordered if waits_on_a_human(row)],\n"
    "            [row for row in ordered if not waits_on_a_human(row)])\n"
)
PARSE_VERDICT = '        "verdict": verdict or UNKNOWN,\n'
FIELD_RETURN = (
    "    if isinstance(node, str) and node:\n"
    "        return node\n"
    "    return UNKNOWN\n"
)
PROVENANCE_RETURN = (
    "    return (\n"
    "        f'<p class=\"section-intro\">Source <code>{esc(source)}</code> at source commit '\n"
)
DECISION_HEADING = "        f'<div><h3>{esc(decision)}</h3><p>{detail}</p></div>'\n"
DECISION_BADGE = "        f'<b>{esc(primary_id)}</b>'\n"
QUEUE_RESIDUE = (
    '    residue = "".join(\n'
    "        f'<div><span>{esc(field(row, \"id\"))}</span><p><code>{esc(field(row, \"authority\"))}</code> '\n"
    "        f'&middot; owner role {esc(field(row, \"owner_role\"))}</p></div>'\n"
    "        for row in excluded\n"
    "    ) or '<div><span>None</span><p>The filter excluded no recorded action.</p></div>'\n"
)
BUILDERS_QUEUE = '    "queue": render_queue,\n'
PROVENANCE_BODY_RETURN = "    return f'<div class=\"definition-list\">{body}</div>'\n"
BUILT_BY_ROW = '        ("Built by", "scripts/build_control_page.py"),\n'
INJECT_REFUSAL = (
    "    if missing or unused:\n"
    "        raise ProjectionError(\n"
)
OBSERVE_COMMIT = '    commit = git(root, "rev-parse", "HEAD") or UNKNOWN\n'
QUEUE_ABSENT_GUARD = (
    '    if facts["actions_absent"]:\n'
    '        return render_unknown(facts, NEXT_ACTIONS, facts["actions_absent"],\n'
    '                              facts["actions_recorded_at"])\n'
)
DECISION_ABSENT_GUARD = (
    '    if facts["current_absent"]:\n'
    '        return render_unknown(facts, CURRENT_STATE, facts["current_absent"], facts["recorded_at"])\n'
    '    decision = facts["resume_decision"]\n'
)
UNKNOWN_BODY = (
    '        \'<div class="callout">\'\n'
    '        f\'<strong>{UNKNOWN}</strong>\'\n'
    "        f'<p>{esc(reason)}. Nothing else is shown in this panel. A count, a list or an empty '\n"
    "        f'table drawn from a record that was never read would report a measurement this projection '\n"
    "        f'does not have, and {UNKNOWN} is the honest answer rather than a convenient one.</p>'\n"
    "        '</div>'\n"
)
DECISION_TAIL = '    decision = facts["resume_decision"]\n'
EMPTY_BODY = "        ''\n"
NO_ACTIONS_ARRAY = (
    '    if not actions_absent and not isinstance((actions or {}).get("actions"), list):\n'
)

PACKAGE_REGION_END = "<!--/BTG-CONTROL:package-->\n"
DERIVED_CLAIM = "This page is <strong>derived and non-authoritative</strong>."
SHALLOW_CALLOUT_OPEN = (
    "  <div class=\"callout\">\n"
    "    <strong>An <code>UNKNOWN</code> here is expected, not a defect</strong>\n"
)
LIMITS_FIRST_ITEM = (
    "    <li>It records nothing and grants nothing."
)
PAGE_MAIN_CLOSE = "</main>\n"

WORKFLOW_STEP = (
    "      - name: Project the records into the staged control page\n"
    "        run: python3 scripts/build_control_page.py --out _site/control/index.html\n"
)
WORKFLOW_CONFIGURE = "      - name: Configure Pages\n"


def edit(root: Path, rel: str, old: str, new: str) -> None:
    """Replace `old` with `new` exactly once, and refuse to be a no-op."""
    path = root / rel
    text = path.read_text(encoding="utf-8")
    found = text.count(old)
    if found != 1:
        raise AssertionError(
            f"{rel}: expected exactly one occurrence of {old[:70]!r}, found {found}")
    path.write_text(text.replace(old, new), encoding="utf-8", newline="")


# --- the mutations -------------------------------------------------------------------------------


def a_key_naming_no_domain_placed_anyway(root: Path) -> None:
    """#346's defect, restored: `implementation` given a domain it does not name."""
    edit(root, PROJECTOR, DOMAIN_RULE, "    return key.partition(\"_\")[0]\n")


def an_unscoped_key_guessed_into_a_domain(root: Path) -> None:
    """The lookup table the derived rule exists instead of: it must place every key somewhere,
    and placing `implementation` is exactly the guess #346 is about."""
    edit(root, PROJECTOR, DOMAIN_RULE,
         '    table = {"implementation": "production"}\n'
         "    if key in table:\n"
         "        return table[key]\n"
         '    head, sep, _ = key.partition("_")\n'
         "    if not sep or not head:\n"
         "        return None\n"
         "    return head\n")


def a_wrong_typed_authority_value_dropped(root: Path) -> None:
    """A key silently missing from a panel about authority is the worst failure this page has."""
    edit(root, PROJECTOR, GROUP_VALUE,
         "        if not isinstance(raw, str):\n"
         "            continue\n"
         "        value = raw\n")


def an_authority_value_reworded(root: Path) -> None:
    """The page renders the record's own words. Re-wording one is #302's decision, not this
    page's, and #302 is open and an operator's."""
    edit(root, PROJECTOR, GROUP_APPEND,
         '            grouped.setdefault(domain, []).append(\n'
         '                (key, "Denied" if "NOT_GRANTED" in value else value))\n')


def the_queue_filter_narrowed_to_human(root: Path) -> None:
    """NS-033 waits on an authority no human word appears in. A filter on HUMAN alone drops it."""
    edit(root, PROJECTOR, AUTHORITY_TOKENS, 'AUTHORITY_TOKENS = ("HUMAN",)')


def the_excluded_actions_lost(root: Path) -> None:
    """The residue is what lets a reader check the count instead of trusting it."""
    edit(root, PROJECTOR, QUEUE_RESIDUE,
         '    residue = "<div><span>None</span><p>nothing</p></div>"\n')


def an_action_in_neither_list(root: Path) -> None:
    """A row that is in neither the queue nor the residue has left the page without a line
    anywhere saying it was dropped."""
    edit(root, PROJECTOR, QUEUE_RETURN,
         "    return ([row for row in ordered if waits_on_a_human(row)], [])\n")


def the_queue_left_unordered(root: Path) -> None:
    edit(root, PROJECTOR, QUEUE_RETURN,
         "    ordered = list(reversed(ordered))\n"
         "    return ([row for row in ordered if waits_on_a_human(row)],\n"
         "            [row for row in ordered if not waits_on_a_human(row)])\n")


def the_validators_silence_read_as_a_pass(root: Path) -> None:
    """A validator that could not be run must not leave the integrity panel saying PASS."""
    edit(root, PROJECTOR, PARSE_VERDICT, '        "verdict": verdict or "PASS",\n')


def a_missing_field_rendered_blank(root: Path) -> None:
    """A blank panel that looks like real data reporting nothing is the failure mode this page
    was specified against. UNKNOWN is a value; an empty string is a disguise."""
    edit(root, PROJECTOR, FIELD_RETURN,
         "    if isinstance(node, str) and node:\n"
         "        return node\n"
         '    return ""\n')


def a_panel_that_cannot_say_where_its_numbers_came_from(root: Path) -> None:
    edit(root, PROJECTOR, PROVENANCE_RETURN,
         "    return (\n"
         "        f'<p class=\"section-intro\">Projected from the records.'\n")


def the_resume_decision_demoted_from_a_heading(root: Path) -> None:
    """A reader must not be able to miss it."""
    edit(root, PROJECTOR, DECISION_HEADING,
         "        f'<div><p>{esc(decision)}</p><p>{detail}</p></div>'\n")


def a_write_control_on_the_page(root: Path) -> None:
    """No Authorize, no Accept, no Record Gate, no Close. The page links to where a decision is
    recorded; it never records one."""
    edit(root, PROJECTOR, DECISION_BADGE,
         "        f'<button>Authorize {esc(primary_id)}</button>'\n")


def a_data_request_on_the_page(root: Path) -> None:
    """No network call, in the projector, the browser or the suite. #311 is open."""
    edit(root, PROJECTOR, PROVENANCE_BODY_RETURN,
         "    return (f'<div class=\"definition-list\">{body}</div>'\n"
         "            '<script>fetch(\"https://api.github.com/\")</script>')\n")


def a_completion_percentage_on_the_page(root: Path) -> None:
    """Forbidden unless its denominator and metric are both on the page; neither is settled."""
    edit(root, PROJECTOR, BUILT_BY_ROW,
         '        ("Built by", "scripts/build_control_page.py, 100% of panels projected"),\n')


def a_panel_dropped_from_the_projector(root: Path) -> None:
    """A builder removed while its region stays is a published page with a hole in it."""
    edit(root, PROJECTOR, BUILDERS_QUEUE, "")


def the_injection_made_permissive(root: Path) -> None:
    """Fail closed: a region with no builder, or a builder with no region, is an error."""
    edit(root, PROJECTOR, INJECT_REFUSAL,
         "    if False:\n"
         "        raise ProjectionError(\n")


def a_record_value_committed_into_the_placeholder(root: Path) -> None:
    """Committing generated state creates a file true when written and false thereafter - the
    defect class #343, #345, #346 and #347 all describe.

    THE VALUE IS READ FROM THE RECORD, not written literally. It was `WAIT_FOR_AUTHORITY` in the
    source, and the test it is aimed at compares against whatever `badf/current-state.json` spells;
    the day the record's resume_decision moves, a literal mutation would stop tripping that test
    while the defect it injects was as real as ever. WP-112 lost three of nineteen controls to
    exactly that, and the rule it left is that a control whose expectation depends on the record it
    happens to run against is not a control.
    """
    recorded = json.loads((root / STATE).read_text(encoding="utf-8"))["resume_decision"]
    edit(root, PAGE, "<h3>This page has not been generated</h3>", f"<h3>{recorded}</h3>")


def a_placeholder_that_does_not_say_it_is_one(root: Path) -> None:
    edit(root, PAGE,
         "<p class=\"section-intro\">This panel has not been generated. Run <code>python "
         "scripts/build_control_page.py</code> to project <code>badf/current-state.json</code> "
         "into it.</p><!--/BTG-CONTROL:package-->",
         "<p class=\"section-intro\">Nothing to report. Run <code>python "
         "scripts/build_control_page.py</code>.</p><!--/BTG-CONTROL:package-->")


def a_region_with_no_builder_added_to_the_page(root: Path) -> None:
    edit(root, PAGE, PAGE_MAIN_CLOSE,
         "<section id=\"extra\"><!--BTG-CONTROL:extra-->x<!--/BTG-CONTROL:extra--></section>\n"
         "</main>\n")


def the_decision_projected_below_another_panel(root: Path) -> None:
    """The decision must be the FIRST thing projected, not merely present."""
    page = root / PAGE
    text = page.read_text(encoding="utf-8")
    start = text.index("<!--BTG-CONTROL:decision-->")
    end = text.index("<!--/BTG-CONTROL:decision-->") + len("<!--/BTG-CONTROL:decision-->")
    block = text[start:end]
    assert block.startswith("<!--BTG-CONTROL:decision-->"), "the decision region was not found"
    moved = text[:start] + text[end:]
    anchor = PACKAGE_REGION_END
    assert moved.count(anchor) == 1, "the package region's end marker is not unique"
    # AFTER the package region's closing marker, not before it. Inserting before nested the
    # decision markers INSIDE the package region, and the non-greedy pattern then found no
    # decision region at all - which is a different defect from the one this control is named for.
    page.write_text(moved.replace(anchor, anchor + block + "\n"), encoding="utf-8", newline="")


def the_derived_and_non_authoritative_claim_removed(root: Path) -> None:
    edit(root, PAGE, DERIVED_CLAIM, "This page is a summary.")


def the_shallow_note_removed(root: Path) -> None:
    """A reader must not think the published copy's UNKNOWN is a defect."""
    page = root / PAGE
    text = page.read_text(encoding="utf-8")
    start = text.index(SHALLOW_CALLOUT_OPEN)
    end = text.index("  </div>\n", start) + len("  </div>\n")
    page.write_text(text[:start] + text[end:], encoding="utf-8", newline="")


def a_map_ticket_run_added_to_the_page(root: Path) -> None:
    """No second map index. #301 is open."""
    edit(root, PAGE, LIMITS_FIRST_ITEM,
         "    <li>Map #91 carries #102, #103, #104, #105 and #106.</li>\n"
         "    <li>It records nothing and grants nothing.")


def the_workflow_step_writing_into_the_tree(root: Path) -> None:
    """Written into the tracked tree, the page becomes committed generated state."""
    edit(root, WORKFLOW,
         "        run: python3 scripts/build_control_page.py --out _site/control/index.html\n",
         "        run: python3 scripts/build_control_page.py\n")


def the_workflow_step_moved_after_verification(root: Path) -> None:
    """After the verification steps, the artifact is checked before the data is in it."""
    edit(root, WORKFLOW, WORKFLOW_STEP, "")
    edit(root, WORKFLOW, WORKFLOW_CONFIGURE, WORKFLOW_STEP + "\n" + WORKFLOW_CONFIGURE)


def the_queues_absent_record_guard_removed(root: Path) -> None:
    """The live defect restored: an absent badf/next-actions.json renders as an EMPTY QUEUE.

    Measured on the tree at d38040a by deleting the file from a copy and running the projector: the
    panel read "No recorded action matches the filter. That is a reading of badf/next-actions.json"
    - false, because nothing had been read - then "The 0 recorded action(s) the filter did NOT
    admit" and "The filter excluded no recorded action", exit 0. #352 requires UNKNOWN where a fact
    is absent, and an empty rendering is a convenient value.
    """
    edit(root, PROJECTOR, QUEUE_ABSENT_GUARD, "")


def the_state_panels_absent_record_guard_removed(root: Path) -> None:
    """The same defect on the other record: the decision panel drawn over an unread state file."""
    edit(root, PROJECTOR, DECISION_ABSENT_GUARD, DECISION_TAIL)


def the_unknown_panel_reduced_to_its_provenance_line(root: Path) -> None:
    """The panel says nothing in its own body and leans on the shared provenance sentence.

    That sentence carries UNKNOWN for the source commit of any tree git cannot read, so a test
    asserting UNKNOWN over the whole rendering passes while the body says nothing. That is how the
    near-vacuous version of the named test passed at d38040a, and this control is what stops the
    repair being undone.
    """
    edit(root, PROJECTOR, UNKNOWN_BODY, EMPTY_BODY)


def the_no_actions_array_case_read_as_an_empty_queue(root: Path) -> None:
    """A document that loaded and carries no `actions` array still says nothing about the queue."""
    edit(root, PROJECTOR, NO_ACTIONS_ARRAY, "    if False:\n")


def the_head_commit_read_as_a_short_sha(root: Path) -> None:
    """THE DECLARED HOLE, and this control asserts the suite stays GREEN.

    `observe()` is the projector's impure half, and `tests/test_control_page.py` never runs it -
    limit 1 of that module. So a defect confined to it is invisible there: this mutation makes the
    provenance panel report a 7-character abbreviation where the page's own prose calls it the
    source commit, and the suite does not notice. The script controls below are where `observe()`
    is exercised at all.

    If this control ever goes red, the hole has closed and limit 1 must be re-derived rather than
    deleted.
    """
    edit(root, PROJECTOR, OBSERVE_COMMIT,
         '    commit = git(root, "rev-parse", "--short", "HEAD") or UNKNOWN\n')


SUITE_CONTROLS = [
    ("a key naming no domain placed anyway", a_key_naming_no_domain_placed_anyway,
     "test_a_single_segment_key_names_no_domain"),
    ("an unscoped key guessed into a domain", an_unscoped_key_guessed_into_a_domain,
     "test_the_live_unscoped_key_is_exactly_the_one_346_names"),
    ("a wrong-typed authority value dropped", a_wrong_typed_authority_value_dropped,
     "test_a_non_string_value_becomes_unknown_and_the_key_survives"),
    ("an authority value re-worded", an_authority_value_reworded,
     "test_values_are_copied_verbatim"),
    ("the human-queue filter narrowed to HUMAN", the_queue_filter_narrowed_to_human,
     "test_the_filter_admits_a_wait_that_names_no_human"),
    ("the excluded actions lost from the page", the_excluded_actions_lost,
     "test_the_excluded_actions_are_listed_with_their_authority"),
    ("an action in neither the queue nor the residue", an_action_in_neither_list,
     "test_the_queue_and_the_residue_partition_every_recorded_action"),
    ("the queue left unordered", the_queue_left_unordered,
     "test_the_queue_is_in_the_records_own_priority_order"),
    ("the validator's silence read as a PASS", the_validators_silence_read_as_a_pass,
     "test_silence_becomes_unknown_and_not_a_pass"),
    ("a missing field rendered blank rather than UNKNOWN", a_missing_field_rendered_blank,
     "test_a_missing_field_is_unknown_rather_than_empty"),
    ("a panel that cannot say where its numbers came from",
     a_panel_that_cannot_say_where_its_numbers_came_from,
     "test_every_panel_says_where_its_numbers_came_from"),
    ("the resume decision demoted from a heading", the_resume_decision_demoted_from_a_heading,
     "test_the_resume_decision_is_the_first_region_and_is_a_heading"),
    ("a write control on the page", a_write_control_on_the_page,
     "test_the_projection_offers_no_write_control"),
    ("a data request on the page", a_data_request_on_the_page,
     "test_the_projection_requests_no_data"),
    ("a completion percentage on the page", a_completion_percentage_on_the_page,
     "test_the_page_shows_no_completion_percentage"),
    ("a panel dropped from the projector", a_panel_dropped_from_the_projector,
     "test_every_region_has_a_builder_and_every_builder_a_region"),
    ("the injection made permissive", the_injection_made_permissive,
     "test_a_region_with_no_builder_is_refused"),
    ("a record value committed into the placeholder",
     a_record_value_committed_into_the_placeholder,
     "test_no_committed_region_carries_a_value_read_from_a_record"),
    ("a placeholder that does not say it is one", a_placeholder_that_does_not_say_it_is_one,
     "test_every_committed_region_says_it_is_not_generated"),
    ("a region added to the page with no builder", a_region_with_no_builder_added_to_the_page,
     "test_every_region_has_a_builder_and_every_builder_a_region"),
    ("the decision projected below another panel", the_decision_projected_below_another_panel,
     "test_the_resume_decision_is_the_first_region_and_is_a_heading"),
    ("the derived and non-authoritative claim removed",
     the_derived_and_non_authoritative_claim_removed,
     "test_the_page_states_it_is_derived_and_non_authoritative"),
    ("the shallow-clone note removed", the_shallow_note_removed,
     "test_the_page_says_an_unknown_is_expected_on_the_published_copy"),
    ("a map ticket run added to the page", a_map_ticket_run_added_to_the_page,
     "test_the_page_lists_no_map_ticket_run"),
    ("the workflow step writing into the tree", the_workflow_step_writing_into_the_tree,
     "test_the_projection_writes_into_the_artifact_and_not_into_the_tree"),
    ("the workflow step moved after verification", the_workflow_step_moved_after_verification,
     "test_the_projection_runs_after_staging_and_before_both_verifications"),
    ("the queue's absent-record guard removed", the_queues_absent_record_guard_removed,
     "test_a_missing_actions_record_is_unknown_and_never_an_empty_queue"),
    ("the state panels' absent-record guard removed",
     the_state_panels_absent_record_guard_removed,
     "test_a_missing_state_record_is_unknown_in_every_panel_it_feeds"),
    ("the UNKNOWN panel reduced to its provenance line",
     the_unknown_panel_reduced_to_its_provenance_line,
     "test_a_missing_record_renders_unknown_in_every_panel_without_raising"),
    ("a loaded document with no actions array read as an empty queue",
     the_no_actions_array_case_read_as_an_empty_queue,
     "test_an_actions_document_with_no_actions_array_is_unknown"),
    # HOLE, not a defect: expected GREEN. See the_head_commit_read_as_a_short_sha.
    ("DECLARED HOLE: the head commit read as a short SHA", the_head_commit_read_as_a_short_sha,
     None),
]


def the_unknown_guard_weakened(root: Path) -> None:
    """`observe()` stops turning a git call it could not make into UNKNOWN."""
    edit(root, PROJECTOR, OBSERVE_COMMIT, '    commit = git(root, "rev-parse", "HEAD") or ""\n')


ABSENT_THREADED = "    absent = {CURRENT_STATE: current_why, NEXT_ACTIONS: actions_why}\n"


def the_absence_reason_discarded_again(root: Path) -> None:
    """`build` stops passing `read_json`'s reason to `gather`, as it did at d38040a.

    `read_json` has always returned (document, reason) and both call sites read
    `current, _ = read_json(...)`, so the module docstring's promise of "UNKNOWN with the reason
    beside it" was never kept by anything. Paired with the control above so that the reason in the
    unmutated run is known to come from `read_json` rather than from the fallback: with this
    applied the same copy renders "no reason was recorded" instead of the FileNotFoundError.
    """
    edit(root, PROJECTOR, ABSENT_THREADED, "    absent = {}\n")


def remove_next_actions(root: Path) -> None:
    """Delete the ledger from the copy. Not a code mutation - the CONDITION the panel must survive."""
    (root / ACTIONS).unlink()


# (name, how to prepare the copy, what the written page must carry)
#
# The first pair demonstrates the no-repository degradation; the second demonstrates the
# absent-record degradation and that the reason reaching the page is the one `read_json` gave. Both
# are pairs on purpose: the second member removes the guard that makes the first member's answer
# what it is, so neither green is green by accident.
SCRIPT_CONTROLS = [
    ("THE NO-REPOSITORY DEMONSTRATION: the projector run in a copy with no .git, unmutated",
     None, "<div><span>Source commit</span><p>UNKNOWN</p></div>"),
    ("the same copy with the UNKNOWN guard weakened to an empty string",
     the_unknown_guard_weakened, "<div><span>Source commit</span><p></p></div>"),
    ("THE ABSENT-RECORD DEMONSTRATION: badf/next-actions.json deleted from the copy, code unmutated",
     remove_next_actions,
     "badf/next-actions.json could not be read: FileNotFoundError. Nothing else is shown"),
    ("the same deletion with read_json's reason discarded in build, as it was at d38040a",
     lambda root: (remove_next_actions(root), the_absence_reason_discarded_again(root)) and None,
     "badf/next-actions.json is not available and no reason was recorded"),
]

FAILED = re.compile(r"^(?:FAIL|ERROR): (\w+) ", re.M)


def run_suite(root: Path) -> tuple[int, set[str]]:
    done = subprocess.run(
        [PYTHON, "-m", "unittest", "discover", "-s", "tests", "-p", "test_control_page.py", "-v"],
        cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    return done.returncode, set(FAILED.findall(done.stdout + done.stderr))


def run_projector(root: Path) -> tuple[int, str]:
    """Run the projector into a scratch path inside the copy and return (exit code, page)."""
    out = root / "_site" / "control" / "index.html"
    done = subprocess.run(
        [PYTHON, "-B", str(root / PROJECTOR), "--out", str(out)],
        cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    if done.returncode != 0 or not out.is_file():
        return done.returncode, ""
    return done.returncode, out.read_text(encoding="utf-8")


def fresh(source: Path, into: Path, name: str) -> Path:
    """A copy WITHOUT `.git`. That is a property the script controls depend on: the copy is not a
    repository, so every git fact must degrade rather than be answered from somewhere else."""
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

    for index, (name, mutate, expected) in enumerate(SUITE_CONTROLS, start=1):
        root = fresh(source, holder, f"control_{index:02d}")
        mutate(root)
        code, failures = run_suite(root)
        if expected is None:
            # A DECLARED HOLE. The mutation is a real defect and the suite is expected to stay
            # green, because nothing in it reads what the mutation changes. A control that
            # demonstrates a limit cannot drift away from the code without this script noticing.
            ok = code == 0 and not failures
            bad += 0 if ok else 1
            print(f"[{'PASS' if ok else 'BAD '}] {name}")
            print(f"       DECLARED HOLE: expected the suite to stay GREEN; exit {code}; "
                  f"failed: {sorted(failures) or 'nothing'}"
                  f"{'' if ok else '  <- the hole has closed; re-derive the limit that declares it'}")
            continue
        ok = code != 0 and expected in failures
        isolated = failures == {expected}
        bad += 0 if ok else 1
        print(f"[{'PASS' if ok else 'BAD '}] {name}")
        print(f"       expected {expected} to fail; exit {code}; "
              f"failed: {sorted(failures) or 'NOTHING'}"
              f"{'' if isolated else '  <- NOT ISOLATED' if ok else ''}")

    for index, (name, mutate, expected) in enumerate(SCRIPT_CONTROLS, start=1):
        root = fresh(source, holder, f"script_{index:02d}")
        if mutate is not None:
            mutate(root)
        code, page = run_projector(root)
        ok = code == 0 and expected in page
        bad += 0 if ok else 1
        print(f"[{'PASS' if ok else 'BAD '}] {name}")
        print(f"       copy with no .git: expected exit 0 and the written page to carry "
              f"{expected!r}; got exit {code} and {'it' if expected in page else 'it NOT'} present")

    total = len(SUITE_CONTROLS) + len(SCRIPT_CONTROLS)
    print(f"\n{total} controls, {bad} not behaving as declared")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
