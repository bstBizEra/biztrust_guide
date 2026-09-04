# badf Schemas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the three unschematised continuity records — `badf/current-state.json`, `badf/next-actions.json`, and each line of `badf/decision-log.jsonl` — versioned JSON Schemas that every existing record passes, and a stdlib test that enforces them.

**Architecture:** Three new schema files under `schemas/` in the same 2020-12 style as the two that exist. One new test module that loads the WP-035 checker from `tests/test_checkpoints_match_schema.py` by path (one checker, not two), validates the three records, adds the new schemas to the keyword-coverage guard, and carries one negative control per schema plus the cross-record checks JSON Schema cannot express. The validator script only gains the three files in its existing parse-and-dialect list.

**Tech Stack:** Python 3 standard library only (`json`, `re`, `unittest`, `importlib`, `pathlib`). JSON Schema draft 2020-12. No new dependencies; `jsonschema` is used by hand for calibration and is not imported by any test.

**Spec:** The design agreed in chat on 2026-09-05 (this plan restates it in full): descriptive schemas derived from the records as they are; closed enums only where the charter already declares the set (`AGENTS.md` §8 states, §3 resume decisions); `decision.type` and `authority` stay open strings; no record is repaired.

## Global Constraints

- Stdlib only. No `import jsonschema` anywhere under `tests/` or `scripts/`.
- Every schema declares `"$schema": "https://json-schema.org/draft/2020-12/schema"` — the validator refuses any other dialect.
- Every schema uses only keywords the checker implements: `type`, `properties`, `required`, `additionalProperties`, `items`, `enum`, `const`, `pattern`, `format` (`date-time` only), `minLength`, `minItems`, `minProperties`, `uniqueItems`, plus the annotations `$schema`, `$id`, `title`, `description`, `$comment`, `examples`, `default`, `deprecated`. Anything else fails the coverage guard.
- No existing record is edited to fit a schema. If a record fails, the schema is wrong or the failure is a finding to register — never a repair of history.
- Commit messages end with `[BIZTRUST-GUIDE-WP-044]` and the `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` trailer.
- Work in the worktree for branch `feat/biztrust-guide-wp-044-badf-schemas`; run `python -m unittest discover -s tests` and `python scripts/validate_continuity.py` before every commit.
- Ticket: issue #89. Nothing here touches page content.

---

## File Structure

| File | Responsibility |
|---|---|
| `schemas/current-state.schema.json` | Create. Shape of `badf/current-state.json`. |
| `schemas/next-actions.schema.json` | Create. Shape of `badf/next-actions.json`, including each action. |
| `schemas/decision-record.schema.json` | Create. Shape of one line of `badf/decision-log.jsonl`. |
| `tests/test_badf_match_schemas.py` | Create. Loads the checker, validates the three records, coverage guard, negative controls, cross-record checks. |
| `scripts/validate_continuity.py` | Modify lines 107-108 and 267: add the three schema paths to the required-files list and the dialect loop. |
| `docs/NEXT_STEPS.md` | Modify NS-006: dated coverage line. |
| `AGENTS.md` | Modify §4: one sentence under the sources-of-truth table. |
| `README.md` | Modify the *What the checks actually enforce* table: one row. |
| `badf/current-state.json`, `badf/next-actions.json`, `badf/decision-log.jsonl`, `sessions/checkpoints/BIZTRUST-GUIDE-WP-044-engineering-ready.json` | Modify/create in the final task: the package's own state, which the new test then validates. |

The checker's public surface, from `tests/test_checkpoints_match_schema.py` (read it before Task 2):

- `errors(instance, schema: dict, path: str = "$") -> list[str]` — every violation as `"json-path: reason"`; raises `NotImplementedError` on an unknown keyword or format.
- `_keywords(node, acc: set[str], in_properties: bool = False) -> set[str]` — keyword positions in a schema tree, `format:<value>` included.
- `IMPLEMENTED: set[str]`, `ANNOTATIONS: set[str]` — the keyword sets the coverage guard compares against.
- `load(path: Path)` — `json.loads` of a UTF-8 file.

---

### Task 1: The three schemas, calibrated against today's records

**Files:**
- Create: `schemas/current-state.schema.json`
- Create: `schemas/next-actions.schema.json`
- Create: `schemas/decision-record.schema.json`

**Interfaces:**
- Produces: the three files above, each with `"$schema"` 2020-12 and a `"$comment"` naming its version `1.0.0`. Task 2's test reads them by these exact paths.

- [ ] **Step 1: Write `schemas/current-state.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://bstbizera.github.io/biztrust_guide/schemas/current-state.schema.json",
  "title": "badf/current-state.json",
  "$comment": "Schema version 1.0.0. Derived from the record as it stood at main 6ba41e5 (WP-043) under BIZTRUST-GUIDE-WP-044; describes, does not prescribe. Closed enums only where AGENTS.md already closes them: state (section 8) and resume_decision (section 3).",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version", "project_id", "repository", "updated_at", "active_work_package", "source",
    "gates", "authority", "latest_checkpoint", "latest_handoff", "primary_next_action_id",
    "resume_decision", "stop_reason", "known_divergence"
  ],
  "properties": {
    "schema_version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" },
    "project_id": { "type": "string", "minLength": 1 },
    "repository": { "type": "string", "pattern": "^[A-Za-z0-9-]+/[A-Za-z0-9._-]+$" },
    "updated_at": { "type": "string", "format": "date-time" },
    "active_work_package": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "title", "state", "objective", "issue_url", "owner_role", "scope"],
      "properties": {
        "id": { "type": "string", "pattern": "^BIZTRUST-GUIDE-WP-[0-9]{3}$" },
        "title": { "type": "string", "minLength": 1 },
        "state": { "enum": ["DRAFT", "READY", "AUTHORIZED", "IN_PROGRESS", "VALIDATING", "ENGINEERING_READY", "ACCEPTED", "CLOSED", "BLOCKED", "WAIT_FOR_AUTHORITY", "RECOVERY_REQUIRED", "REJECTED", "CANCELLED"] },
        "objective": { "type": "string", "minLength": 1 },
        "issue_url": { "type": "string", "pattern": "^https://github\\.com/[^/\\s]+/[^/\\s]+/(issues|pull)/[0-9]+$" },
        "owner_role": { "type": "string", "minLength": 1 },
        "scope": { "type": "array", "minItems": 1, "items": { "type": "string", "minLength": 1 } }
      }
    },
    "source": {
      "type": "object",
      "additionalProperties": false,
      "required": ["branch", "baseline_commit", "baseline_kind", "expected_remote"],
      "properties": {
        "branch": { "type": "string", "minLength": 1 },
        "baseline_commit": { "type": "string", "pattern": "^[0-9a-f]{40}$" },
        "baseline_kind": { "type": "string", "minLength": 1 },
        "expected_remote": { "type": "string", "pattern": "^https://[^\\s]+$" }
      }
    },
    "gates": { "type": "object", "minProperties": 1, "additionalProperties": { "type": "string", "minLength": 1 } },
    "authority": { "type": "object", "minProperties": 1, "additionalProperties": { "type": "string", "minLength": 1 } },
    "latest_checkpoint": { "type": "string", "pattern": "^sessions/checkpoints/[^/\\s]+\\.json$" },
    "latest_handoff": { "type": ["string", "null"] },
    "primary_next_action_id": { "type": "string", "pattern": "^NS-[0-9]{3}$" },
    "resume_decision": { "enum": ["CONTINUE", "BLOCKED", "WAIT_FOR_AUTHORITY", "RECOVERY_REQUIRED", "COMPLETE"] },
    "stop_reason": { "type": "string", "minLength": 1 },
    "known_divergence": { "type": "string" }
  }
}
```

- [ ] **Step 2: Write `schemas/next-actions.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://bstbizera.github.io/biztrust_guide/schemas/next-actions.schema.json",
  "title": "badf/next-actions.json",
  "$comment": "Schema version 1.0.0. Derived from the record at main 6ba41e5 under BIZTRUST-GUIDE-WP-044. Exactly-one-primary and primary-names-an-existing-action are cross-record rules enforced by tests/test_badf_match_schemas.py, not here.",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "project_id", "work_package_id", "updated_at", "actions"],
  "properties": {
    "schema_version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" },
    "project_id": { "type": "string", "minLength": 1 },
    "work_package_id": { "type": "string", "pattern": "^BIZTRUST-GUIDE-WP-[0-9]{3}$" },
    "updated_at": { "type": "string", "format": "date-time" },
    "actions": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "primary", "priority", "owner_role", "authority", "action", "prerequisites", "evidence_required", "stop_conditions", "fallback"],
        "properties": {
          "id": { "type": "string", "pattern": "^NS-[0-9]{3}$" },
          "primary": { "type": "boolean" },
          "priority": { "type": "integer" },
          "owner_role": { "type": "string", "minLength": 1 },
          "authority": { "type": "string", "minLength": 1 },
          "action": { "type": "string", "minLength": 1 },
          "prerequisites": { "type": "array", "items": { "type": "string", "minLength": 1 } },
          "evidence_required": { "type": "array", "items": { "type": "string", "minLength": 1 } },
          "stop_conditions": { "type": "array", "items": { "type": "string", "minLength": 1 } },
          "fallback": { "type": "string", "minLength": 1 }
        }
      }
    }
  }
}
```

- [ ] **Step 3: Write `schemas/decision-record.schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://bstbizera.github.io/biztrust_guide/schemas/decision-record.schema.json",
  "title": "One line of badf/decision-log.jsonl",
  "$comment": "Schema version 1.0.0. Derived from all 44 entries at main 6ba41e5 under BIZTRUST-GUIDE-WP-044. type and authority are open strings: nothing in the repository declares their vocabulary, and closing them here would invent one. Uniqueness and ordering of ids are cross-record rules in tests/test_badf_match_schemas.py and scripts/validate_continuity.py.",
  "type": "object",
  "additionalProperties": false,
  "required": ["id", "timestamp", "work_package_id", "type", "decision", "rationale", "authority", "supersedes"],
  "properties": {
    "id": { "type": "string", "pattern": "^DEC-[0-9]{3}$" },
    "timestamp": { "type": "string", "format": "date-time" },
    "work_package_id": { "type": "string", "pattern": "^BIZTRUST-GUIDE-WP-[0-9]{3}$" },
    "type": { "type": "string", "pattern": "^[A-Z][A-Z_]*$" },
    "decision": { "type": "string", "minLength": 1 },
    "rationale": { "type": "string", "minLength": 1 },
    "authority": { "type": "string", "minLength": 1 },
    "supersedes": { "type": ["string", "null"], "pattern": "^DEC-[0-9]{3}$" }
  }
}
```

- [ ] **Step 4: Calibrate by hand against `jsonschema` (not a test; evidence for the checkpoint)**

Run, from the worktree root:

```bash
python - <<'EOF'
import json, jsonschema
from jsonschema import Draft202012Validator as V
def run(schema, doc):
    return [e.json_path for e in V(json.load(open(schema, encoding="utf-8"))).iter_errors(doc)]
print("current-state", run("schemas/current-state.schema.json", json.load(open("badf/current-state.json", encoding="utf-8"))))
print("next-actions", run("schemas/next-actions.schema.json", json.load(open("badf/next-actions.json", encoding="utf-8"))))
bad = [(i, run("schemas/decision-record.schema.json", json.loads(l))) for i, l in enumerate(open("badf/decision-log.jsonl", encoding="utf-8"), 1) if l.strip()]
print("decisions failing:", [(i, e) for i, e in bad if e])
EOF
```

Expected: `current-state []`, `next-actions []`, `decisions failing: []`. If any path is reported, the schema is wrong for a record that exists: loosen that property to what the record has and note it in the `$comment`. Do not edit the record.

- [ ] **Step 5: Commit**

```bash
git add schemas/current-state.schema.json schemas/next-actions.schema.json schemas/decision-record.schema.json
git commit -m "feat(schemas): current-state, next-actions and decision-record schemas, derived from today's records [BIZTRUST-GUIDE-WP-044]

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: The test — one checker, three records, negative controls, cross-record rules

**Files:**
- Create: `tests/test_badf_match_schemas.py`
- Read first: `tests/test_checkpoints_match_schema.py` (the checker), `tests/test_resume_schema_identity.py:44-60` (the by-path loader pattern this copies)

**Interfaces:**
- Consumes: the three schema files from Task 1 at their exact paths; `errors`, `_keywords`, `IMPLEMENTED`, `ANNOTATIONS`, `load` from the checker module, loaded by path.
- Produces: the module-level names `SCHEMAS: dict[str, Path]`, `RECORDS: dict[str, Path]`, `load_checker()`, `decision_lines() -> list[tuple[int, dict]]`, used by nothing else but documented so Task 3's validator edit does not duplicate them.

- [ ] **Step 1: Write the test module**

```python
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

CROSS-RECORD RULES the schemas cannot express, enforced here:
  * exactly one action is primary, and current-state's primary_next_action_id names it;
  * next-actions' work_package_id equals current-state's active package id;
  * current-state's latest_checkpoint names a file that exists;
  * decision ids are unique and ascend line by line (the validator checks uniqueness;
    ascent is new here).

Negative controls mutate in-memory copies; nothing here writes to the tree.

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import importlib.util
import json
import re
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
    def test_exactly_one_primary_and_state_names_it(self) -> None:
        primaries = [a["id"] for a in self.actions["actions"] if a["primary"]]
        self.assertEqual(1, len(primaries), f"primary actions: {primaries}")
        self.assertEqual(primaries[0], self.state["primary_next_action_id"])

    def test_priorities_are_one_to_n(self) -> None:
        self.assertEqual(list(range(1, len(self.actions["actions"]) + 1)), [a["priority"] for a in self.actions["actions"]])

    def test_state_and_actions_name_the_same_package(self) -> None:
        self.assertEqual(self.state["active_work_package"]["id"], self.actions["work_package_id"])

    def test_latest_checkpoint_exists(self) -> None:
        self.assertTrue((ROOT / self.state["latest_checkpoint"]).is_file(), self.state["latest_checkpoint"])

    def test_decision_ids_are_unique_and_ascend(self) -> None:
        ids = [entry["id"] for _, entry in self.decisions]
        self.assertEqual(len(ids), len(set(ids)), "duplicate decision id")
        numbers = [int(i.split("-")[1]) for i in ids]
        self.assertEqual(numbers, sorted(numbers), "decision ids must ascend line by line; append, never insert")

    def test_cross_record_rules_can_fail(self) -> None:
        actions = json.loads(json.dumps(self.actions))
        actions["actions"][0]["primary"] = not actions["actions"][0]["primary"]
        primaries = [a["id"] for a in actions["actions"] if a["primary"]]
        self.assertNotEqual(1, len(primaries))
        numbers = [45, 44]
        self.assertNotEqual(numbers, sorted(numbers))


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run the new module and watch the expected shape of failure before the schemas exist**

If Task 1 is not merged yet in your worktree, run:

```bash
python -m unittest tests.test_badf_match_schemas -v 2>&1 | tail -5
```

Expected without Task 1's files: `FileNotFoundError` in `setUp` on `schemas/current-state.schema.json` — the test fails closed. With Task 1's files present, proceed to Step 3.

- [ ] **Step 3: Run it against the real records**

```bash
python -m unittest tests.test_badf_match_schemas -v 2>&1 | tail -15
```

Expected: every test `ok`. If `test_every_decision_conforms` lists lines, read each: a line whose `type` has a hyphen or lowercase letter, or whose `timestamp` lacks `Z`, means the schema's pattern is tighter than history — loosen the schema in Task 1's file and note it in its `$comment`. Do not edit the log.

- [ ] **Step 4: Prove the controls bite on a broken checker**

Temporarily, in a scratch copy of the checker, make `errors()` return `[]`; point `CHECKER` at the copy by editing the constant in a copy of this test module in your scratch directory; run it; expect the three `TestChecksCanFail` tests to fail. Then delete both copies. Record the outcome in the checkpoint (Task 4) as a negative control with `"status": "FAIL", "exit_code": 1`.

- [ ] **Step 5: Run the whole suite and the validator**

```bash
python -m unittest discover -s tests 2>&1 | tail -1
python scripts/validate_continuity.py | tail -2
```

Expected: `OK (skipped=1)` and `CONTINUITY_VALIDATION=PASS`.

- [ ] **Step 6: Commit**

```bash
git add tests/test_badf_match_schemas.py
git commit -m "test(badf): the three records conform to their schemas; controls; cross-record rules [BIZTRUST-GUIDE-WP-044]

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: The validator lists the new schemas; the docs say what is checked

**Files:**
- Modify: `scripts/validate_continuity.py:96-113` (the `required` list) and `:266-275` (the dialect loop)
- Modify: `docs/NEXT_STEPS.md` under `### NS-006`
- Modify: `AGENTS.md` §4, directly after the sources-of-truth table
- Modify: `README.md`, the *What the checks actually enforce* table, before the `.gitattributes` row

**Interfaces:**
- Consumes: the three schema paths from Task 1 as literal strings.
- Produces: `validate_continuity.py` output line `schemas:json-valid` now covers five files; the check name is unchanged.

- [ ] **Step 1: Add the three schemas to the validator's required files and dialect loop**

In `scripts/validate_continuity.py`, in the `required` list after `"schemas/handoff.schema.json",` add:

```python
        "schemas/current-state.schema.json",
        "schemas/next-actions.schema.json",
        "schemas/decision-record.schema.json",
```

and change the dialect loop header from

```python
    for schema in ("schemas/session-checkpoint.schema.json", "schemas/handoff.schema.json"):
```

to

```python
    for schema in ("schemas/session-checkpoint.schema.json", "schemas/handoff.schema.json",
                   "schemas/current-state.schema.json", "schemas/next-actions.schema.json",
                   "schemas/decision-record.schema.json"):
```

- [ ] **Step 2: Run the validator's own fail-closed suite, which copies the repo and mutates it**

```bash
python -m unittest tests.test_validator_fails_closed -v 2>&1 | tail -3
python scripts/validate_continuity.py | grep -E 'schemas|required-files|CONTINUITY'
```

Expected: the suite `OK`; output shows `required-files:20` (was 17) and `schemas:json-valid`, and `CONTINUITY_VALIDATION=PASS`.

- [ ] **Step 3: Add the NS-006 line in `docs/NEXT_STEPS.md`**

Directly after the NS-006 paragraph ("The included validator covers…"), add:

```markdown

- **Covered, dated 2026-09-05:** five record types now have a versioned 2020-12 schema and a stdlib check — session checkpoints and handoffs (`tests/test_checkpoints_match_schema.py`, WP-035), and `badf/current-state.json`, `badf/next-actions.json` and every decision-log entry (`tests/test_badf_match_schemas.py`, WP-044). The schemas describe the records as they stood; enums are closed only where `AGENTS.md` closes them. **Not covered:** evidence *manifests* (NS-008), and Work Package issues, which live on GitHub and not in this tree.
```

- [ ] **Step 4: Add one sentence to `AGENTS.md` §4**

After the sources-of-truth table's last row and before `If sources disagree, the agent records the conflict…`, add:

```markdown
Since WP-044, `badf/current-state.json`, `badf/next-actions.json` and every entry of `badf/decision-log.jsonl` are validated against `schemas/*.schema.json` by `tests/test_badf_match_schemas.py`, and the one-primary, same-package and ascending-id rules the schemas cannot express are checked there too.

```

- [ ] **Step 5: Add one row to the README enforcement table**

Before the line beginning `| \`.gitattributes\` |`, insert:

```markdown
| `tests/test_badf_match_schemas.py` | Validates `badf/current-state.json`, `badf/next-actions.json` and every decision-log entry against `schemas/*.schema.json` with the same stdlib checker as the checkpoints, and enforces the cross-record rules a schema cannot: exactly one primary action named by the state file, one package across both files, decision ids unique and ascending. Schemas describe the records; enums are closed only where the charter closes them. |
```

- [ ] **Step 6: Run everything and commit**

```bash
python -m unittest discover -s tests 2>&1 | tail -1
python scripts/validate_continuity.py | tail -1
git add scripts/validate_continuity.py docs/NEXT_STEPS.md AGENTS.md README.md
git commit -m "docs,validator: the three new schemas registered; NS-006 coverage recorded [BIZTRUST-GUIDE-WP-044]

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: The package's own state, validated by the test it adds

**Files:**
- Modify: `badf/current-state.json`, `badf/next-actions.json`
- Append: `badf/decision-log.jsonl` (DEC-046 — DEC-045 is main's last entry; check with `tail -1`)
- Create: `sessions/checkpoints/BIZTRUST-GUIDE-WP-044-engineering-ready.json`

**Interfaces:**
- Consumes: nothing new. The new test from Task 2 must pass on the files this task writes; that is the point of doing it last.

- [ ] **Step 1: Write the state with a script, not by hand** (the pattern every package since WP-032 has used; keep it in your scratch directory, never in the tree)

The script must: set `active_work_package` to WP-044 (`issue_url` `https://github.com/bstBizEra/biztrust_guide/issues/89`, scope the nine files above, state `ENGINEERING_READY`); set `source` to the branch and the full `main` baseline sha; set `latest_checkpoint` to the new file; keep `primary_next_action_id` `NS-040` and `resume_decision` `WAIT_FOR_AUTHORITY`; write a `stop_reason` that names NS-006 as covered and the next unticketed item (NS-007) as next; append to `known_divergence` the sentence `WP-043 merged as PR #88 at 6ba41e5.`; set `next-actions.json`'s `work_package_id` and `updated_at`; append DEC-046 typed `CORRECTNESS` recording the descriptive-schema decision, the enum choice, and the calibration result; write the checkpoint with the validations from Tasks 1 to 3, including the negative control from Task 2 Step 4 as `FAIL`/`1`, and `declared_non_coverage` naming evidence manifests and Work Package issues.

- [ ] **Step 2: Run the whole suite; the new test now validates the files just written**

```bash
python -m unittest discover -s tests 2>&1 | tail -1
python scripts/validate_continuity.py | tail -2
```

Expected: `OK (skipped=1)`; `RESUME_DECISION=WAIT_FOR_AUTHORITY`; `PRIMARY_NEXT_ACTION=NS-040`.

- [ ] **Step 3: Commit, push, open the pull request**

```bash
git add badf sessions/checkpoints/BIZTRUST-GUIDE-WP-044-engineering-ready.json
git commit -m "docs(badf): WP-044 state, DEC-046 and checkpoint [BIZTRUST-GUIDE-WP-044]

Closes #89.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
git push -u origin feat/biztrust-guide-wp-044-badf-schemas
gh pr create --base main --head feat/biztrust-guide-wp-044-badf-schemas --title "[BIZTRUST-GUIDE-WP-044] Schemas and a check for the three badf records (#89)" --body-file <scratch>/pr44.md
```

- [ ] **Step 4: Fresh-context adversarial review before merge**, as every package since WP-029: spawn a reviewer with the head sha, the issue, and these questions — do all 44 decisions pass under `jsonschema` too; can any control be satisfied by a broken checker; is any schema tighter than a record it claims to describe; is the AGENTS.md sentence true. Fix every finding on the branch, re-verify, merge only the fixed head with `--match-head-commit`.

---

## Self-Review

**Spec coverage.** Descriptive schemas → Task 1 (with the calibration step that forces loosening rather than repair). Charter-closed enums only → Task 1 (`state`, `resume_decision`); open `type`/`authority` → Task 1 `$comment`. One checker → Task 2 `load_checker`. Coverage guard on the new schemas → Task 2. Negative control per schema → Task 2. Cross-record rules → Task 2. Validator lists the schemas → Task 3. NS-006 line, AGENTS §4, README row → Task 3. No record repaired → Task 1 Step 4 and Task 2 Step 3 both say so. Reviewed before merge → Task 4 Step 4.

**Placeholder scan.** No TBD/TODO. Task 4 Step 1 describes the state script's required content rather than pasting it, because its values (baseline sha, timestamps) are only known at execution; every field it must set is named.

**Type consistency.** `errors(instance, schema, path)` returns `list[str]` and is used that way in Tasks 2 and 4. `SCHEMAS`/`RECORDS` are `dict[str, Path]` throughout. The `$comment` phrase `Schema version 1.0.0` is asserted verbatim in Task 2 `test_every_schema_declares_the_dialect` and written verbatim in all three Task 1 files. Pattern `^NS-[0-9]{3}$` appears identically in both schemas that use it.
