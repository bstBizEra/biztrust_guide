#!/usr/bin/env python3
"""The three badf/ records conform to their schemas, and to the rules the schemas cannot say.

Before BIZTRUST-GUIDE-WP-044 (issue #89), badf/current-state.json, badf/next-actions.json
and the decision log had no schema at all: scripts/validate_continuity.py hand-checked a
few fields, and a new key, a mistyped priority, or a timestamp without an offset would have
passed. The schemas in schemas/ are DESCRIPTIVE - derived from the records as they stood -
with enums closed only where AGENTS.md already closes them (states, resume decisions).

ONE CHECKER. This module loads errors() and the keyword-coverage guard from
tests/test_checkpoints_match_schema.py by path, exactly as that module's docstring
demands: a second hand-rolled validator would be a second thing to calibrate.

CROSS-RECORD RULES the schemas cannot express, live in cross_record_problems():
  * exactly one action is primary, and current-state's primary_next_action_id names it;
  * priorities run 1 to n, with no gap and no repeat;
  * next-actions' work_package_id equals current-state's active package id;
  * current-state's latest_checkpoint names a file that exists;
  * decision ids are unique and ascend line by line (the validator checks uniqueness;
    ascent is new here).

Negative controls mutate in-memory copies against cross_record_problems; nothing here writes to the tree.

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "tests" / "test_checkpoints_match_schema.py"
SCHEMAS = {
    "current-state": ROOT / "schemas" / "current-state.schema.json",
    "next-actions": ROOT / "schemas" / "next-actions.schema.json",
    "decision-record": ROOT / "schemas" / "decision-record.schema.json",
}
RECORDS = {
    "current-state": ROOT / "badf" / "current-state.json",
    "next-actions": ROOT / "badf" / "next-actions.json",
    "decision-log": ROOT / "badf" / "decision-log.jsonl",
}


def load_checker():
    """The WP-035 checker, loaded by path so this works under `unittest discover -s tests`
    (module name test_checkpoints_match_schema) and under `python -m unittest tests.x`
    (module name tests.test_checkpoints_match_schema) alike."""
    spec = importlib.util.spec_from_file_location("badf_checker", CHECKER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def decision_lines() -> list[tuple[int, dict]]:
    out = []
    for number, line in enumerate(RECORDS["decision-log"].read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            out.append((number, json.loads(line)))
    return out


def cross_record_problems(state: dict, actions: dict, decisions: list[tuple[int, dict]]) -> list[str]:
    """The rules JSON Schema cannot express, as 'reason' strings. Empty means consistent."""
    out: list[str] = []
    primaries = [a["id"] for a in actions["actions"] if a["primary"]]
    if len(primaries) != 1:
        out.append(f"expected exactly one primary action, found {primaries}")
    elif primaries[0] != state["primary_next_action_id"]:
        out.append(f"primary_next_action_id {state['primary_next_action_id']!r} is not the primary action {primaries[0]!r}")
    priorities = [a["priority"] for a in actions["actions"]]
    if priorities != list(range(1, len(priorities) + 1)):
        out.append(f"priorities are not 1..n: {priorities}")
    if state["active_work_package"]["id"] != actions["work_package_id"]:
        out.append(f"current-state names {state['active_work_package']['id']}, next-actions names {actions['work_package_id']}")
    if not (ROOT / state["latest_checkpoint"]).is_file():
        out.append(f"latest_checkpoint {state['latest_checkpoint']!r} does not exist")
    ids = [entry["id"] for _, entry in decisions]
    if len(ids) != len(set(ids)):
        out.append("duplicate decision id")
    numbers = [int(i.split("-")[1]) for i in ids]
    if numbers != sorted(numbers):
        out.append("decision ids do not ascend line by line")
    return out


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.c = load_checker()
        self.schemas = {k: self.c.load(v) for k, v in SCHEMAS.items()}
        self.state = self.c.load(RECORDS["current-state"])
        self.actions = self.c.load(RECORDS["next-actions"])
        self.decisions = decision_lines()


class TestSchemasAreEnforceable(Base):
    def test_every_keyword_is_implemented(self) -> None:
        """The coverage guard from WP-035, extended to the three new schemas."""
        for name, schema in self.schemas.items():
            with self.subTest(schema=name):
                found = self.c._keywords(schema, set())
                unknown = sorted(found - self.c.IMPLEMENTED - self.c.ANNOTATIONS)
                self.assertEqual(unknown, [], f"{name} uses keywords the checker cannot enforce: {unknown}")

    def test_every_schema_declares_the_dialect(self) -> None:
        for name, schema in self.schemas.items():
            with self.subTest(schema=name):
                self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
                self.assertIn("Schema version 1.0.0", schema["$comment"])


class TestRecordsConform(Base):
    def test_current_state_conforms(self) -> None:
        self.assertEqual([], self.c.errors(self.state, self.schemas["current-state"]))

    def test_next_actions_conform(self) -> None:
        self.assertEqual([], self.c.errors(self.actions, self.schemas["next-actions"]))

    def test_every_decision_conforms(self) -> None:
        self.assertGreaterEqual(len(self.decisions), 44, "the log had 44 entries when this was written; fewer means a parse problem")
        failing = []
        for number, entry in self.decisions:
            found = self.c.errors(entry, self.schemas["decision-record"])
            if found:
                failing.append(f"  line {number} ({entry.get('id')}):\n    " + "\n    ".join(found))
        self.assertEqual([], failing, "decision-log entries that fail the schema - fix the schema or register a finding, never the entry:\n" + "\n".join(failing))


class TestChecksCanFail(Base):
    """One control per schema, each the defect a careless edit is most likely to make."""

    def _mutated(self, doc, mutate):
        copy = json.loads(json.dumps(doc))
        mutate(copy)
        return copy

    def test_current_state_controls(self) -> None:
        s = self.schemas["current-state"]
        cases = {
            "unknown top-level key": lambda d: d.__setitem__("notes", "x"),
            "state outside the charter's enum": lambda d: d["active_work_package"].__setitem__("state", "DONE"),
            "resume decision outside the enum": lambda d: d.__setitem__("resume_decision", "GO"),
            "short baseline commit": lambda d: d["source"].__setitem__("baseline_commit", "6ba41e5"),
            "updated_at without offset": lambda d: d.__setitem__("updated_at", "2026-09-05T03:00:00"),
            "primary id malformed": lambda d: d.__setitem__("primary_next_action_id", "NS-40"),
            "empty scope": lambda d: d["active_work_package"].__setitem__("scope", []),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                self.assertTrue(self.c.errors(self._mutated(self.state, mutate), s), name)

    def test_next_actions_controls(self) -> None:
        s = self.schemas["next-actions"]
        cases = {
            "priority as a string": lambda d: d["actions"][0].__setitem__("priority", "1"),
            "primary as a string": lambda d: d["actions"][0].__setitem__("primary", "true"),
            "action missing fallback": lambda d: d["actions"][0].pop("fallback"),
            "no actions": lambda d: d.__setitem__("actions", []),
            "unknown action key": lambda d: d["actions"][0].__setitem__("owner", "x"),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                self.assertTrue(self.c.errors(self._mutated(self.actions, mutate), s), name)

    def test_decision_record_controls(self) -> None:
        s = self.schemas["decision-record"]
        good = self.decisions[-1][1]
        cases = {
            "id malformed": lambda d: d.__setitem__("id", "DEC-45"),
            "timestamp without offset": lambda d: d.__setitem__("timestamp", "2026-09-05T03:00:00"),
            "lowercase type": lambda d: d.__setitem__("type", "correctness"),
            "supersedes malformed": lambda d: d.__setitem__("supersedes", "45"),
            "missing rationale": lambda d: d.pop("rationale"),
            "unknown key": lambda d: d.__setitem__("note", "x"),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                self.assertTrue(self.c.errors(self._mutated(good, mutate), s), name)


class TestCrossRecordRules(Base):
    def test_records_are_consistent(self) -> None:
        """All cross-record rules pass on real data."""
        self.assertEqual([], cross_record_problems(self.state, self.actions, self.decisions))

    def test_cross_record_rules_can_fail(self) -> None:
        """Each rule is exercised by a mutation that violates it.

        The two actions-list cases build a synthetic three-element actions list
        (deep copies of the ledger's own actions[0], ids NS-001..NS-003, priorities
        1..3, primary True/False/False) rather than indexing into the live ledger's
        actions[1] and actions[2] - the live ledger's length is not this test's to
        assume, and a legitimately shorter ledger would raise IndexError here.
        """

        def synthetic_actions(actions: dict) -> list[dict]:
            template = actions["actions"][0]
            out = []
            for aid, priority, primary in (("NS-001", 1, True), ("NS-002", 2, False), ("NS-003", 3, False)):
                item = json.loads(json.dumps(template))
                item["id"] = aid
                item["priority"] = priority
                item["primary"] = primary
                out.append(item)
            return out

        def two_primaries(state: dict, actions: dict, decisions: list) -> None:
            actions["actions"] = synthetic_actions(actions)
            actions["actions"][1] = {**actions["actions"][1], "primary": True}

        def primary_id_mismatch(state: dict, actions: dict, decisions: list) -> None:
            state["primary_next_action_id"] = "NS-999"

        def priorities_out_of_order(state: dict, actions: dict, decisions: list) -> None:
            actions["actions"] = synthetic_actions(actions)
            actions["actions"][1] = {**actions["actions"][1], "priority": 3}
            actions["actions"][2] = {**actions["actions"][2], "priority": 2}

        def work_package_id_mismatch(state: dict, actions: dict, decisions: list) -> None:
            actions["work_package_id"] = "WP-999"

        def latest_checkpoint_missing(state: dict, actions: dict, decisions: list) -> None:
            state["latest_checkpoint"] = "sessions/checkpoints/MISSING.json"

        def duplicate_decision_id(state: dict, actions: dict, decisions: list) -> None:
            if len(decisions) > 1:
                decisions[-1] = (decisions[-1][0], {**decisions[-1][1], "id": decisions[-2][1]["id"]})

        def decision_ids_reordered(state: dict, actions: dict, decisions: list) -> None:
            if len(decisions) > 1:
                last_id = decisions[-1][1]["id"]
                second_last_id = decisions[-2][1]["id"]
                decisions[-1] = (decisions[-1][0], {**decisions[-1][1], "id": second_last_id})
                decisions[-2] = (decisions[-2][0], {**decisions[-2][1], "id": last_id})

        cases = {
            "two primaries": (two_primaries, "expected exactly one primary action"),
            "primary id mismatch": (primary_id_mismatch, "is not the primary action"),
            "priorities [1, 3, 2]": (priorities_out_of_order, "priorities are not 1..n"),
            "work_package_id mismatch": (work_package_id_mismatch, "current-state names"),
            "latest_checkpoint missing": (latest_checkpoint_missing, "does not exist"),
            "duplicate decision id": (duplicate_decision_id, "duplicate decision id"),
            "decision ids reordered": (decision_ids_reordered, "do not ascend line by line"),
        }
        for name, (mutate, key_phrase) in cases.items():
            with self.subTest(case=name):
                state_copy = json.loads(json.dumps(self.state))
                actions_copy = json.loads(json.dumps(self.actions))
                decisions_copy = [(n, e) for n, e in self.decisions]

                mutate(state_copy, actions_copy, decisions_copy)

                problems = cross_record_problems(state_copy, actions_copy, decisions_copy)
                self.assertTrue(
                    any(key_phrase in p for p in problems),
                    f"{name}: expected '{key_phrase}' in {problems}"
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
