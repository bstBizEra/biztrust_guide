#!/usr/bin/env python3
"""The control page projects the records and invents nothing (#352).

`control/index.html` is a DERIVED surface: `scripts/build_control_page.py` reads
`badf/current-state.json`, `badf/next-actions.json` and whatever
`scripts/validate_continuity.py` prints, and injects the result into marked regions of the tracked
page at build time. The tracked page itself carries an empty placeholder. This module holds three
different things, and they are worth naming apart:

  THE PLACEHOLDER      the committed file must say it has not been generated, in every region, and
                       must carry no value read from a record. A blank panel that looks like real
                       data reporting nothing is the failure mode; an honest "not generated" is not.
  THE DERIVATIONS      the pure functions - the authority grouping, the human-queue filter, the
                       validator parse - measured against the real records and against fixtures
                       built to be awkward.
  THE WIRING           the marked regions, the injection's fail-closed behaviour, and the workflow
                       step that writes into the staged artifact rather than into the tree.

THIS MODULE RUNS NO SUBPROCESS AND TOUCHES NO NETWORK. `tests/` is subprocess-free apart from
`tests/test_resume_reconciliation.py` and `tests/test_wp024_fixtures_are_sealed.py`, and that is
worth keeping. `scripts/build_control_page.py` is split for it: `observe()` runs git and the
validator, `gather()` is pure, and every test here hands `gather()` a synthetic observation. The
consequence is limit 1 below.

WHAT THIS DOES NOT DO. Every item is a limit, not a caveat.

 1. NOTHING HERE RUNS THE PROJECTOR END TO END. `observe()` - the git calls and the validator
    invocation - is never executed by this module, so a defect that lives only in those calls is
    invisible here. It is covered instead by `scripts/wp113_controls.py`, which runs
    `python scripts/build_control_page.py` in a fresh copy, and by the workflow itself, whose
    step fails the build if the projector cannot run. The seam is deliberate; the hole is real.
 2. NOTHING HERE ASSERTS THAT A PARTICULAR RECORD VALUE IS CORRECT. The page copies what the
    records spell. If `badf/current-state.json` records the wrong Work Package, this module is
    green and the page is wrong, faithfully. Reconciling the record against observed git is
    `scripts/validate_continuity.py`'s step 8 and `tests/test_resume_reconciliation.py`'s.
 3. THE HUMAN-QUEUE FILTER IS A SUBSTRING RULE AND THIS MODULE HOLDS IT TO ITS OWN WORDING, NOT
    TO A JUDGEMENT ABOUT WHO IS REALLY BLOCKED. `HUMAN` or `WAIT` in the recorded authority, or
    `human` in the recorded owner_role. An action that waits on a person while spelling neither
    is missed, and the page prints the excluded actions with their authority strings for exactly
    that reason - so the reader can see the residue rather than trust the count. Measured against
    the live record below, action by action, so the wording cannot drift from the record silently.
 4. THE GROUPING RULE IS DERIVED, NOT SEMANTIC. The first underscore-separated segment of a key
    is treated as the domain it names. `resume_decision_taxonomy` therefore groups under `resume`,
    which is a spelling and not a claim about what the key governs. What the rule guarantees is
    narrower and is what #346 asked for: a key that names NO domain is never placed under a
    guessed one.
 5. THE PAGE'S APPEARANCE IS NOT TESTED. That a `.next-action` renders with an amber border, or
    that the decision is legible, is a review responsibility. What is tested is that the decision
    region is the FIRST region in the document and that the recorded decision appears inside a
    heading in it.
 6. THE FONT LINK IS A NETWORK REQUEST AND IS DELIBERATELY NOT FORBIDDEN HERE. Every page in this
    guide loads Google Fonts, and the control page copies the shared skeleton. What the network
    assertions below forbid is a DATA request: a script, a fetch, a tracker call. #311's rule is
    about reading the tracker, not about typography.

MEASURED by `scripts/wp113_controls.py` - twenty-nine controls, run only after an unmutated copy
comes back green: twenty-six mutations each trip the test named for them, one is the declared hole
above and expects the suite to stay GREEN, and two run the projector itself in a copy that is not a
repository to demonstrate the UNKNOWN degradation rather than assert it. Three of those controls
found a defect in this module's own harness before they behaved: `inject` raised `SystemExit`,
which `unittest` lets out of the runner, so a copy with one builder removed exited 1 with no named
failure at all and the control could not say what had caught it.
"""

from __future__ import annotations

import importlib.util
import json
import re
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTOR = ROOT / "scripts" / "build_control_page.py"
PAGE = ROOT / "control" / "index.html"
WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"
CURRENT_STATE = ROOT / "badf" / "current-state.json"
NEXT_ACTIONS = ROOT / "badf" / "next-actions.json"

# The phrases the committed placeholder must carry. Both of them: "not generated" without the
# command leaves a reader with nothing to do about it, and the command without the statement reads
# as an aside beside what looks like data.
NOT_GENERATED = "has not been generated"
THE_COMMAND = "python scripts/build_control_page.py"

# The workflow steps this one must sit between, by their exact names.
STAGE_STEP = "- name: Stage immutable site artifact"
PROJECT_STEP = "- name: Project the records into the staged control page"
VERIFY_PAGES_STEP = "- name: Verify every tracked page reached the artifact"
VERIFY_ASSETS_STEP = "- name: Verify every tracked asset reached the artifact"


def _load_projector():
    """Import the projector by PATH, so a copy of the tree loads that copy's own module."""
    spec = importlib.util.spec_from_file_location("wp113_projector_under_test", PROJECTOR)
    assert spec is not None and spec.loader is not None, f"cannot load {PROJECTOR}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILD = _load_projector()

# A synthetic observation, in the shape `observe()` returns. It is synthetic ON PURPOSE: running
# the real one would put a subprocess in `tests/`. Every field is a value a real run can produce.
OBSERVED = {
    "validator_exit": 0,
    "validator_stdout": (
        "CONTINUITY_VALIDATION=PASS\n"
        "PASS: required-files:20\n"
        "PASS: checkpoint:linked\n"
        "RESUME_DECISION=WAIT_FOR_AUTHORITY\n"
        "PRIMARY_NEXT_ACTION=NS-041\n"
        "STATE_RECONCILIATION=UNKNOWN\n"
        "STATE_RECONCILIATION_REASON=this clone is shallow, so the history before HEAD is absent\n"
    ),
    "commit": "0" * 40,
    "commit_subject": "[BIZTRUST-GUIDE-WP-113] a fixture subject",
    "commit_at": "2026-09-09T00:00:00+00:00",
    "clone_depth": "full history",
}

NOW = datetime(2026, 9, 9, 12, 0, 0, tzinfo=timezone.utc)


def records() -> tuple[dict, dict]:
    return (json.loads(CURRENT_STATE.read_text(encoding="utf-8")),
            json.loads(NEXT_ACTIONS.read_text(encoding="utf-8")))


def live_facts() -> dict:
    current, actions = records()
    return BUILD.gather(current, actions, OBSERVED, NOW)


def regions_of(source: str) -> dict[str, str]:
    """{name: body} for every marked region, read with the projector's own pattern."""
    return {m.group("name"): m.group("body") for m in BUILD.REGION.finditer(source)}


def body_of(rendered: str) -> str:
    """A panel's own rendering, with the shared provenance sentence removed.

    Every panel ends with `<p class="section-intro">Source …`, and that sentence contains UNKNOWN
    whenever git cannot read the tree - so an assertion for UNKNOWN over the whole rendering can be
    satisfied without the panel body saying anything at all. That is how
    `test_a_missing_record_renders_unknown_in_every_panel_without_raising` passed while the queue
    panel was drawing an empty table over a file it had never read.
    """
    return rendered.split('<p class="section-intro">Source', 1)[0]


class TestControlsCanFire(unittest.TestCase):
    """Positive controls. Every rule below is measured over something; these prove there is
    something to measure. A refactor that emptied any of these would leave the rest vacuous."""

    def test_the_projector_declares_builders(self) -> None:
        self.assertGreaterEqual(len(BUILD.BUILDERS), 7, "fewer panels than #352's table names")

    def test_the_page_is_present_and_not_empty(self) -> None:
        self.assertTrue(PAGE.is_file(), f"{PAGE} is not a file")
        self.assertGreater(len(PAGE.read_text(encoding="utf-8")), 2000, "the page is a stub")

    def test_the_committed_page_carries_marked_regions(self) -> None:
        found = regions_of(PAGE.read_text(encoding="utf-8"))
        self.assertNotEqual({}, found, "no marked region in the committed page")

    def test_the_records_are_readable_and_populated(self) -> None:
        current, actions = records()
        self.assertIn("authority", current)
        self.assertGreater(len(actions.get("actions", [])), 0, "no recorded action to project")

    def test_the_live_queue_filter_admits_some_actions_and_excludes_others(self) -> None:
        """Positive control for the two live-record queue assertions further down.

        `test_the_excluded_actions_are_listed_with_their_authority` iterates the excluded list, so
        an empty one would make it pass while measuring nothing at all. This declares the premise
        rather than leaving it implicit; if it fires, the record has changed shape and that test
        needs re-deriving, not deleting.
        """
        queue, excluded = BUILD.human_queue(records()[1])
        self.assertGreater(len(queue), 0, "no recorded action waits on a human")
        self.assertGreater(len(excluded), 0, "the filter excluded nothing, so the residue is empty")


class TestTheCommittedPageIsAPlaceholder(unittest.TestCase):
    """Nothing generated is committed, and the committed file says so in every panel."""

    def setUp(self) -> None:
        self.source = PAGE.read_text(encoding="utf-8")
        self.regions = regions_of(self.source)

    def test_every_region_has_a_builder_and_every_builder_a_region(self) -> None:
        self.assertEqual(sorted(BUILD.BUILDERS), sorted(self.regions),
                         "the page and the projector disagree about which panels exist")

    def test_no_region_appears_twice(self) -> None:
        found = BUILD.regions(self.source)
        self.assertEqual(sorted(set(found)), sorted(found), "a region marker is repeated")

    def test_every_committed_region_says_it_is_not_generated(self) -> None:
        for name, body in sorted(self.regions.items()):
            with self.subTest(region=name):
                self.assertIn(NOT_GENERATED, body,
                              "a committed panel that does not say it is a placeholder")
                self.assertIn(THE_COMMAND, body,
                              "a committed panel that does not name the command that fills it")

    def test_no_committed_region_carries_a_value_read_from_a_record(self) -> None:
        """The honest-placeholder guard, and the reason the whole page is not just generated once.

        A committed value is true when written and false thereafter - the defect class #343, #345,
        #346 and #347 describe. The values checked are the ones a stale copy would be read for.
        """
        current, _ = records()
        leaked = [
            value for value in (
                current["active_work_package"]["id"],
                current["resume_decision"],
                current["primary_next_action_id"],
                current["source"]["baseline_commit"],
                current["updated_at"],
            )
            if any(value in body for body in self.regions.values())
        ]
        self.assertEqual([], leaked, f"record values committed into the page: {leaked}")

    def test_the_page_states_it_is_derived_and_non_authoritative(self) -> None:
        """Static prose, so it is true of the placeholder and of the projection alike."""
        prose = re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", self.source)).lower()
        self.assertIn("derived and non-authoritative", prose)
        self.assertIn("grants nothing", prose)

    def test_the_page_says_an_unknown_is_expected_on_the_published_copy(self) -> None:
        """CI checks out shallow. A reader must not read that UNKNOWN as a defect."""
        prose = re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", self.source))
        self.assertIn("shallow", prose)
        self.assertRegex(prose, r"UNKNOWN[^.]{0,80}expected|expected[^.]{0,80}UNKNOWN")


class TestInjectionFailsClosed(unittest.TestCase):
    """A projector that silently skips a panel publishes a page with a hole and no line saying so."""

    def blocks(self, names) -> dict[str, str]:
        return {name: f"<p>{name}</p>" for name in names}

    def test_injection_replaces_every_body_and_keeps_the_markers(self) -> None:
        template = ("<!--BTG-CONTROL:decision-->placeholder<!--/BTG-CONTROL:decision-->"
                    "<!--BTG-CONTROL:queue-->placeholder<!--/BTG-CONTROL:queue-->")
        out = BUILD.inject(template, self.blocks(["decision", "queue"]))
        self.assertNotIn("placeholder", out)
        self.assertEqual(["decision", "queue"], BUILD.regions(out))
        self.assertIn("<p>decision</p>", out)

    def test_a_region_with_no_builder_is_refused(self) -> None:
        template = "<!--BTG-CONTROL:decision-->x<!--/BTG-CONTROL:decision-->"
        with self.assertRaises(BUILD.ProjectionError) as raised:
            BUILD.inject(template, self.blocks([]))
        self.assertIn("regions with no builder", str(raised.exception))

    def test_a_builder_with_no_region_is_refused(self) -> None:
        template = "<!--BTG-CONTROL:decision-->x<!--/BTG-CONTROL:decision-->"
        with self.assertRaises(BUILD.ProjectionError) as raised:
            BUILD.inject(template, self.blocks(["decision", "queue"]))
        self.assertIn("builders with no region", str(raised.exception))

    def test_a_repeated_region_is_refused(self) -> None:
        template = ("<!--BTG-CONTROL:decision-->x<!--/BTG-CONTROL:decision-->"
                    "<!--BTG-CONTROL:decision-->y<!--/BTG-CONTROL:decision-->")
        with self.assertRaises(BUILD.ProjectionError) as raised:
            BUILD.inject(template, self.blocks(["decision"]))
        self.assertIn("repeats region", str(raised.exception))

    def test_the_refusal_is_an_ordinary_exception_and_not_a_system_exit(self) -> None:
        """A `SystemExit` escapes `unittest` and aborts the run with no summary, so a suite in a
        copy with one builder removed exited 1 with not one named failure. Measured on three
        controls of `scripts/wp113_controls.py` at once; this is the guard on the repair."""
        template = "<!--BTG-CONTROL:decision-->x<!--/BTG-CONTROL:decision-->"
        self.assertFalse(issubclass(BUILD.ProjectionError, SystemExit))
        try:
            BUILD.inject(template, self.blocks([]))
        except BUILD.ProjectionError:
            pass
        except BaseException as exc:  # noqa: BLE001 - the point is which base class it has
            self.fail(f"inject raised {type(exc).__name__}, which unittest cannot record")

    def test_projecting_over_a_projection_replaces_rather_than_appends(self) -> None:
        """The published page is built from the tracked template, but a person regenerating in
        place runs this against the previous output. The markers must survive."""
        template = PAGE.read_text(encoding="utf-8")
        once = BUILD.render(live_facts(), template)
        twice = BUILD.render(live_facts(), once)
        self.assertEqual(BUILD.regions(once), BUILD.regions(twice))
        self.assertEqual(len(once), len(twice), "re-projection changed the page's length")


class TestAuthorityGrouping(unittest.TestCase):
    """#346: a key that names no domain must render under `Unscoped`, never guessed at."""

    def test_a_single_segment_key_names_no_domain(self) -> None:
        self.assertIsNone(BUILD.domain_of("implementation"))
        self.assertIsNone(BUILD.domain_of("deployment"))

    def test_a_qualified_key_names_its_first_segment(self) -> None:
        self.assertEqual("production", BUILD.domain_of("production_platform_implementation"))
        self.assertEqual("architecture", BUILD.domain_of("architecture_acceptance"))
        self.assertEqual("architecture", BUILD.domain_of("architecture_drafting_ahead_of_s01"))

    def test_a_key_that_is_only_a_separator_names_no_domain(self) -> None:
        self.assertIsNone(BUILD.domain_of("_leading"))
        self.assertIsNone(BUILD.domain_of(""))

    def test_every_recorded_key_lands_where_the_rule_puts_it(self) -> None:
        """THE RULE, re-derived over whatever the record happens to hold.

        Unconditional and record-independent: a key with a separator lands under its first segment,
        a key without one lands in Unscoped. It says nothing about which keys exist, so a records
        edit cannot turn it red. The test below is the deliberate exception and declares itself.
        """
        current, _ = records()
        groups, unscoped = BUILD.group_authority(current["authority"])
        for domain, entries in groups:
            for key, _value in entries:
                with self.subTest(key=key):
                    self.assertEqual(key.partition("_")[0], domain)
                    self.assertIn("_", key)
        for key, _value in unscoped:
            with self.subTest(key=key):
                self.assertNotIn("_", key.strip("_") or "_",
                                 "a key with a domain segment was left unscoped")

    def test_the_live_unscoped_key_is_exactly_the_one_346_names(self) -> None:
        """The defect, live. `implementation` beside `production_platform_implementation`.

        A DECLARED DEPENDENCE ON THE RECORD, and the only one in this module. WP-112 learned that a
        control whose expectation depends on the record it happens to run against is not a control;
        this is a TEST rather than a control, and the dependence is the point - it is a ratchet on
        #346 being live, which is why the page carries a callout about it.

        IF THIS GOES RED, #346 HAS BEEN FIXED IN THE RECORD. The repair is then to delete this test
        and the page's Unscoped callout together, and to leave
        `test_every_recorded_key_lands_where_the_rule_puts_it` above standing. Do not weaken the
        rule to keep this green. `test_the_unscoped_group_is_named_on_the_page` rests on the same
        premise and goes with it.
        """
        current, _ = records()
        groups, unscoped = BUILD.group_authority(current["authority"])
        self.assertIn("implementation", [key for key, _ in unscoped])
        placed = [key for _, entries in groups for key, _ in entries]
        self.assertIn("production_platform_implementation", placed)
        self.assertNotIn("implementation", placed,
                         "the unscoped key was placed under a guessed domain")

    def test_every_recorded_key_is_rendered_exactly_once(self) -> None:
        current, _ = records()
        groups, unscoped = BUILD.group_authority(current["authority"])
        seen = [key for _, entries in groups for key, _ in entries] + [k for k, _ in unscoped]
        self.assertEqual(sorted(current["authority"]), sorted(seen),
                         "a recorded authority key was dropped or duplicated")

    def test_values_are_copied_verbatim(self) -> None:
        current, _ = records()
        groups, unscoped = BUILD.group_authority(current["authority"])
        rendered = dict([(k, v) for _, e in groups for k, v in e] + list(unscoped))
        self.assertEqual(current["authority"], rendered, "an authority value was re-worded")

    def test_a_non_string_value_becomes_unknown_and_the_key_survives(self) -> None:
        """A key silently missing from a panel about authority is the worst failure this page has."""
        groups, unscoped = BUILD.group_authority({"a_b": None, "c": 7})
        self.assertEqual([("a", [("a_b", BUILD.UNKNOWN)])], groups)
        self.assertEqual([("c", BUILD.UNKNOWN)], unscoped)

    def test_a_non_object_authority_block_groups_nothing(self) -> None:
        self.assertEqual(([], []), BUILD.group_authority(None))
        self.assertEqual(([], []), BUILD.group_authority(["implementation"]))


class TestHumanQueue(unittest.TestCase):
    """The filter is stated on the page; these hold it to that wording against the live record."""

    def test_the_filter_admits_an_authority_naming_a_human(self) -> None:
        self.assertTrue(BUILD.waits_on_a_human(
            {"authority": "HUMAN_DECISION_REQUIRED", "owner_role": "architecture-owner"}))

    def test_the_filter_admits_a_wait_that_names_no_human(self) -> None:
        """NS-033's authority is WAIT_FOR_AUTHORITY_ON_ASSERTED_KEYS_ISSUE_52 and its owner_role
        names no human. A filter on `HUMAN` alone would have dropped it."""
        self.assertTrue(BUILD.waits_on_a_human(
            {"authority": "WAIT_FOR_AUTHORITY_ON_ASSERTED_KEYS_ISSUE_52",
             "owner_role": "documentation-engineer"}))

    def test_the_filter_admits_a_human_owner_role(self) -> None:
        self.assertTrue(BUILD.waits_on_a_human(
            {"authority": "GRANTED", "owner_role": "human-reviewer"}))

    def test_the_filter_excludes_an_operator_instruction_to_proceed(self) -> None:
        """An operator instruction to PROCEED is authority already given, not a queue entry."""
        self.assertFalse(BUILD.waits_on_a_human(
            {"authority": "OPERATOR_INSTRUCTION_2026_09_05_PROCEED_ON_YOUR_CALL_PROPOSED_ONLY",
             "owner_role": "documentation-engineer"}))

    def test_the_queue_and_the_residue_partition_every_recorded_action(self) -> None:
        """A count is only as good as its filter, so nothing may fall out of both lists."""
        _, actions = records()
        queue, excluded = BUILD.human_queue(actions)
        ids = [row["id"] for row in queue] + [row["id"] for row in excluded]
        self.assertEqual(sorted(row["id"] for row in actions["actions"]), sorted(ids))

    def test_the_queue_is_in_the_records_own_priority_order(self) -> None:
        _, actions = records()
        queue, _ = BUILD.human_queue(actions)
        priorities = [row["priority"] for row in queue]
        self.assertEqual(sorted(priorities), priorities, "the queue is not in priority order")

    def test_the_live_queue_is_the_actions_the_stated_filter_admits(self) -> None:
        """Re-derived here from the record's own fields rather than copied from a list, so that a
        change to the filter's wording that changes who is in the queue is visible."""
        _, actions = records()
        queue, _ = BUILD.human_queue(actions)
        expected = [
            row["id"] for row in sorted(actions["actions"], key=lambda r: r["priority"])
            if "HUMAN" in row["authority"] or "WAIT" in row["authority"]
            or "human" in row["owner_role"]
        ]
        self.assertEqual(expected, [row["id"] for row in queue])

    def test_an_action_with_no_priority_sorts_last_rather_than_disappearing(self) -> None:
        queue, excluded = BUILD.human_queue(
            {"actions": [{"id": "B", "authority": "HUMAN_DECISION_REQUIRED"},
                         {"id": "A", "authority": "HUMAN_DECISION_REQUIRED", "priority": 1}]})
        self.assertEqual(["A", "B"], [row["id"] for row in queue])
        self.assertEqual([], excluded)

    def test_a_malformed_actions_document_yields_two_empty_lists(self) -> None:
        self.assertEqual(([], []), BUILD.human_queue(None))
        self.assertEqual(([], []), BUILD.human_queue({"actions": "NS-041"}))


class TestValidatorParse(unittest.TestCase):
    """The integrity panel is the validator's OWN output. Parsing only; it counts nothing itself."""

    def test_checks_are_read_in_the_order_printed(self) -> None:
        parsed = BUILD.parse_validator(
            "CONTINUITY_VALIDATION=PASS\nPASS: required-files:20\nPASS: checkpoint:linked\n")
        self.assertEqual([("required-files", "20"), ("checkpoint", "linked")], parsed["checks"])
        self.assertEqual("PASS", parsed["verdict"])

    def test_a_failing_run_keeps_its_error_lines(self) -> None:
        parsed = BUILD.parse_validator(
            "CONTINUITY_VALIDATION=FAIL\nERROR: State/action Work Package IDs do not match\n")
        self.assertEqual("FAIL", parsed["verdict"])
        self.assertEqual(["State/action Work Package IDs do not match"], parsed["errors"])
        self.assertEqual([], parsed["checks"])

    def test_the_reconciliation_is_read_by_name_and_not_by_position(self) -> None:
        parsed = BUILD.parse_validator(
            "STATE_RECONCILIATION_REASON=because\nSTATE_RECONCILIATION=LAG_EXPECTED\n")
        self.assertEqual("LAG_EXPECTED", parsed["reconciliation"])
        self.assertEqual("because", parsed["reconciliation_reason"])

    def test_silence_becomes_unknown_and_not_a_pass(self) -> None:
        parsed = BUILD.parse_validator("")
        self.assertEqual(BUILD.UNKNOWN, parsed["verdict"])
        self.assertEqual(BUILD.UNKNOWN, parsed["reconciliation"])
        self.assertEqual([], parsed["checks"])


class TestAbsentFactsBecomeUnknown(unittest.TestCase):
    """UNKNOWN is a value, not a failure - and never a convenient one."""

    def test_a_missing_record_renders_unknown_in_every_panel_without_raising(self) -> None:
        """UNKNOWN in the panel's BODY, with the shared provenance sentence stripped first.

        This test was near-vacuous when it was written: the queue panel satisfied it only through
        the provenance line, which every panel carries and which says UNKNOWN for the source commit
        of any tree git cannot read. The body was meanwhile rendering "No recorded action matches
        the filter" over a file that had not been read. Splitting the provenance sentence off is
        what makes the assertion about the panel rather than about the sentence under it.
        """
        facts = BUILD.gather(None, None, {"validator_stdout": ""}, NOW)
        for name, builder in sorted(BUILD.BUILDERS.items()):
            with self.subTest(panel=name):
                body = body_of(builder(facts))
                self.assertNotEqual("", body.strip(), "the panel is nothing but its provenance")
                self.assertIn(BUILD.UNKNOWN, body,
                              "a panel with no data that does not say UNKNOWN in its own body")

    def test_a_missing_actions_record_is_unknown_and_never_an_empty_queue(self) -> None:
        """#352: the projector emits UNKNOWN where a fact is absent, never a convenient value.

        AN EMPTY RENDERING IS A CONVENIENT VALUE, and it was the live behaviour. Measured before
        the fix by deleting badf/next-actions.json from a copy of the tree and running the
        projector: the panel read "No recorded action matches the filter. That is a reading of
        badf/next-actions.json" - false, nothing had been read - then "The 0 recorded action(s) the
        filter did NOT admit" and "The filter excluded no recorded action", exit 0.
        """
        facts = BUILD.gather(records()[0], None, OBSERVED, NOW,
                             {BUILD.NEXT_ACTIONS: "badf/next-actions.json could not be read: "
                                                  "FileNotFoundError"})
        body = body_of(BUILD.render_queue(facts))
        self.assertIn(BUILD.UNKNOWN, body)
        self.assertIn("could not be read: FileNotFoundError", body,
                      "the reason read_json gave never reached the panel")
        for wording in ("No recorded action matches the filter", "recorded action(s) the filter",
                        "excluded no recorded action", "in the record's own priority order"):
            with self.subTest(wording=wording):
                self.assertNotIn(wording, body, "an absent record rendered as an empty queue")
        self.assertNotIn("0 ", body, "a count drawn from a record that was never read")

    def test_a_missing_state_record_is_unknown_in_every_panel_it_feeds(self) -> None:
        """Not special-cased to the queue: the same rule on badf/current-state.json."""
        facts = BUILD.gather(None, records()[1], OBSERVED, NOW,
                             {BUILD.CURRENT_STATE: "badf/current-state.json is not valid JSON: "
                                                   "JSONDecodeError"})
        for name in ("decision", "package", "authority"):
            with self.subTest(panel=name):
                body = body_of(BUILD.BUILDERS[name](facts))
                self.assertIn(BUILD.UNKNOWN, body)
                self.assertIn("is not valid JSON: JSONDecodeError", body)
        # And the panel fed by the OTHER record is untouched, so the guard is scoped.
        self.assertIn("in the record's own priority order", BUILD.render_queue(facts))

    def test_a_record_that_was_read_and_is_empty_is_not_reported_as_unreadable(self) -> None:
        """The distinction the fix exists to draw. An empty queue is a measurement; an absent file
        is not, and the two rendered identically."""
        facts = BUILD.gather(records()[0], {"actions": []}, OBSERVED, NOW)
        body = body_of(BUILD.render_queue(facts))
        self.assertIn("No recorded action matches the filter", body)
        self.assertNotIn("could not be read", body)

    def test_an_actions_document_with_no_actions_array_is_unknown(self) -> None:
        """A file that loaded and carries no `actions` array still says nothing about the queue."""
        for document in ({}, {"actions": "NS-041"}, {"actions": None}):
            with self.subTest(document=document):
                facts = BUILD.gather(records()[0], document, OBSERVED, NOW)
                body = body_of(BUILD.render_queue(facts))
                self.assertIn(BUILD.UNKNOWN, body)
                self.assertIn("carries no `actions` array", body)

    def test_the_decision_panel_does_not_claim_to_have_read_an_absent_ledger(self) -> None:
        """current-state is present, next-actions is not: the panel renders, and its one sentence
        about the ledger must not read as a finding about the ledger's contents."""
        facts = BUILD.gather(records()[0], None, OBSERVED, NOW,
                             {BUILD.NEXT_ACTIONS: "badf/next-actions.json could not be read: "
                                                  "FileNotFoundError"})
        rendered = BUILD.render_decision(facts)
        self.assertIn("could not be read: FileNotFoundError", rendered)
        self.assertNotIn("No matching action is recorded", rendered)

    def test_a_lost_reason_is_said_to_be_lost_rather_than_invented(self) -> None:
        """`unusable` is the one place a reason can be missing, and it must not fill one in."""
        self.assertEqual("", BUILD.unusable({"a": 1}, "", "badf/x.json"))
        self.assertEqual("", BUILD.unusable({}, "some reason", "badf/x.json"),
                         "an empty but PRESENT document is usable")
        self.assertEqual("because", BUILD.unusable(None, "because", "badf/x.json"))
        self.assertIn("no reason was recorded", BUILD.unusable(None, "", "badf/x.json"))

    def test_a_missing_field_is_unknown_rather_than_empty(self) -> None:
        self.assertEqual(BUILD.UNKNOWN, BUILD.field({}, "resume_decision"))
        self.assertEqual(BUILD.UNKNOWN, BUILD.field({"resume_decision": ""}, "resume_decision"))
        self.assertEqual(BUILD.UNKNOWN, BUILD.field({"resume_decision": 4}, "resume_decision"))
        self.assertEqual(BUILD.UNKNOWN, BUILD.field(None, "resume_decision"))

    def test_a_primary_action_the_ledger_does_not_carry_is_said_rather_than_faked(self) -> None:
        current, _ = records()
        facts = BUILD.gather(current, {"actions": []}, OBSERVED, NOW)
        rendered = BUILD.render_decision(facts)
        self.assertIn(current["primary_next_action_id"], rendered)
        self.assertIn("No matching action is recorded", rendered)


class TestTheProjectionRendersTheRecord(unittest.TestCase):
    """What the injected page says, measured against the records it was built from."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.current, cls.actions = records()
        cls.facts = live_facts()
        cls.page = BUILD.render(cls.facts, PAGE.read_text(encoding="utf-8"))
        cls.regions = regions_of(cls.page)

    def test_the_resume_decision_is_the_first_region_and_is_a_heading(self) -> None:
        self.assertEqual("decision", BUILD.regions(self.page)[0],
                         "something is projected above the resume decision")
        self.assertIn(f"<h3>{self.current['resume_decision']}</h3>", self.regions["decision"])

    def test_the_recorded_state_is_rendered_in_the_records_own_word(self) -> None:
        """No new status vocabulary: #302 is open and is an operator's."""
        self.assertIn(self.current["active_work_package"]["state"], self.regions["package"])

    def test_every_authority_value_appears_verbatim(self) -> None:
        for key, value in sorted(self.current["authority"].items()):
            with self.subTest(key=key):
                self.assertIn(value, self.regions["authority"])

    def test_the_unscoped_group_is_named_on_the_page(self) -> None:
        _, unscoped = BUILD.group_authority(self.current["authority"])
        self.assertTrue(unscoped, "the live record has no unscoped key to render")
        self.assertIn("Unscoped", self.regions["authority"])

    def test_the_excluded_actions_are_listed_with_their_authority(self) -> None:
        _, excluded = BUILD.human_queue(self.actions)
        for row in excluded:
            with self.subTest(action=row["id"]):
                self.assertIn(row["id"], self.regions["queue"])
                self.assertIn(row["authority"], self.regions["queue"])

    def test_the_integrity_panel_carries_the_validators_own_checks(self) -> None:
        for name, _ in BUILD.parse_validator(OBSERVED["validator_stdout"])["checks"]:
            with self.subTest(check=name):
                self.assertIn(name, self.regions["integrity"])

    def test_every_panel_says_where_its_numbers_came_from(self) -> None:
        """A derived surface that cannot say where a number came from is a second source of truth.

        Provenance's own panel is the gathering of these facts and states them as its rows.
        """
        for name, body in sorted(self.regions.items()):
            with self.subTest(panel=name):
                if name == "provenance":
                    self.assertIn("Source commit", body)
                    self.assertIn("Projection built", body)
                    continue
                self.assertIn("at source commit", body)
                self.assertIn(self.facts["commit"], body)
                self.assertIn(self.facts["built_at"], body)

    def test_the_projection_offers_no_write_control(self) -> None:
        """No Authorize, no Accept, no Record Gate, no Close - and no form to put one in."""
        for token in ("<form", "<input", "<button", "<select", "<textarea",
                      "onclick", "method=", "action="):
            with self.subTest(token=token):
                self.assertNotIn(token, "".join(self.regions.values()))

    def test_the_projection_requests_no_data(self) -> None:
        """Limit 6: the shared skeleton's font link is not a data request and is not in a region."""
        for token in ("<script", "fetch(", "XMLHttpRequest", "api.github.com", "EventSource"):
            with self.subTest(token=token):
                self.assertNotIn(token, "".join(self.regions.values()))

    def test_the_page_shows_no_completion_percentage(self) -> None:
        """#352 forbids one unless its denominator and metric are both on the page. Neither is
        settled - the completion matrix is #307, which waits on #302.

        WHAT IS ACTUALLY MEASURED: that the page contains no `%` character at all. That is BROADER
        than the prohibition and narrower in a different direction, and both halves are deliberate.
        Broader, because a legitimate `%` in a record value would fail here; narrower, because a
        percentage written in words would pass. It is the cheapest reading that cannot be satisfied
        by relabelling, and if a record ever carries a `%` this is where the decision is made rather
        than where it is silently lost.
        """
        self.assertNotIn("%", self.page)

    def test_the_page_lists_no_map_ticket_run(self) -> None:
        """#301 is open. The page may LINK a map; it may not become a second index of one.

        A run of three or more bare issue references outside a link is what an index looks like.
        The record's own prose quotes such runs, so this is asserted over the page's own writing:
        the static source, with every injected region removed.
        """
        static = BUILD.REGION.sub("", PAGE.read_text(encoding="utf-8"))
        prose = re.sub(r"<a [^>]*>.*?</a>", " ", static, flags=re.S)
        self.assertEqual([], re.findall(r"(?:#\d+[,;]\s*){2,}#\d+", prose))


class TestTheWorkflowWiring(unittest.TestCase):
    """The page is projected into the ARTIFACT, after staging and before verification."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_the_steps_this_one_sits_between_are_present(self) -> None:
        """Anchors asserted, not assumed: a renamed neighbour must fail here rather than silently
        make the ordering assertion below vacuous."""
        for step in (STAGE_STEP, PROJECT_STEP, VERIFY_ASSETS_STEP, VERIFY_PAGES_STEP):
            with self.subTest(step=step):
                self.assertIn(step, self.workflow)

    def test_the_projection_runs_after_staging_and_before_both_verifications(self) -> None:
        stage = self.workflow.index(STAGE_STEP)
        project = self.workflow.index(PROJECT_STEP)
        self.assertLess(stage, project, "the projection runs before the artifact is staged")
        for step in (VERIFY_ASSETS_STEP, VERIFY_PAGES_STEP):
            with self.subTest(step=step):
                self.assertLess(project, self.workflow.index(step),
                                "the artifact is verified before the projection writes into it")

    def test_the_projection_writes_into_the_artifact_and_not_into_the_tree(self) -> None:
        """The tracked page must stay a placeholder on every run, CI included."""
        rest = self.workflow[self.workflow.index(PROJECT_STEP) + len(PROJECT_STEP):]
        step = rest[:rest.index("- name:")] if "- name:" in rest else rest
        self.assertIn("scripts/build_control_page.py --out _site/control/index.html", step)

    def test_the_staging_glob_still_carries_the_page_into_the_artifact(self) -> None:
        """The projection OVERWRITES a staged file; it does not create one the glob missed.

        If the staging step ever stopped copying tracked HTML, the verification step would still
        find `_site/control/index.html` - written by the projection - and pass while every other
        page was missing. The glob is asserted here so that cannot happen quietly.
        """
        self.assertIn("git ls-files '*.html'", self.workflow)
        self.assertTrue(PAGE.is_file())
        self.assertEqual(".html", PAGE.suffix)

    def test_the_workflow_still_verifies_every_tracked_page(self) -> None:
        step = self.workflow[self.workflow.index(VERIFY_PAGES_STEP):]
        self.assertIn("MISSING FROM ARTIFACT", step)


class TestTheProjectorTouchesNoNetwork(unittest.TestCase):
    """#311 keeps this repository's tooling offline, and the projector stays inside that rule."""

    def test_the_projector_imports_no_network_module(self) -> None:
        source = PROJECTOR.read_text(encoding="utf-8")
        for module in ("requests", "urllib", "socket", "http.client", "httpx", "ftplib"):
            with self.subTest(module=module):
                self.assertNotRegex(source, rf"^\s*(?:import|from)\s+{re.escape(module)}\b",
                                    f"the projector imports {module}")

    def test_the_projector_runs_only_git_and_the_validator(self) -> None:
        """Every subprocess argument list in the projector, by its first element."""
        source = PROJECTOR.read_text(encoding="utf-8")
        commands = re.findall(r"subprocess\.run\(\s*\n?\s*\[([^,\]]+)", source)
        self.assertNotEqual([], commands, "no subprocess call found to check")
        for command in commands:
            with self.subTest(command=command.strip()):
                self.assertIn(command.strip().strip('"'), ('git', 'sys.executable'))


if __name__ == "__main__":
    unittest.main(verbosity=2)
