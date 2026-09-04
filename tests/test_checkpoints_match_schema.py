#!/usr/bin/env python3
"""Every committed checkpoint conforms to schemas/session-checkpoint.schema.json.

AGENTS.md section 6 says every checkpoint must conform to the schema, and until
BIZTRUST-GUIDE-WP-035 (issue #68) nothing checked it: the validator confirmed
only that the schema file parsed and declared the right dialect. Measured
before this file existed, three of sixteen committed checkpoints failed the
schema - WP-017, WP-024 and WP-026 record `validation` entries as strings
where the schema requires objects, and WP-017's one blocker is a string too -
and nothing would have noticed a seventeenth.

WHY A HAND-ROLLED CHECKER
=========================

The repository is stdlib-only by policy, and `jsonschema` is not in the
stdlib. So this file implements the SUBSET of JSON Schema 2020-12 the two
schemas in `schemas/` actually use - and no more. The subset is not a guess:
`test_every_schema_keyword_is_implemented` walks both schema files and fails
on any keyword the checker does not know, so a schema edit that reaches for
`oneOf`, `$ref`, `dependentRequired` or anything else is refused here rather
than silently unenforced. A checker that ignores keywords it does not
recognise would report PASS on a schema it had not read, which is the defect
this file exists to close.

The three legacy checkpoints are REGISTERED, not repaired. Rewriting a
record's shape means choosing a `status` and an `exit_code` the author never
wrote down - "41 tests" says nothing about whether they passed - and the
package's stop condition forbids altering recorded facts. The registry is a
ratchet in the shape of test_stage_page_spine.KNOWN_GAPS: an entry must still
fail, and the moment a registered checkpoint conforms the entry has to go.
Nothing written after this file may be added to it; the registry test asserts
the members are exactly the three that predate enforcement.

`templates/session-checkpoint.json` is NOT validated: it is a template, its
placeholders (`<40-CHARACTER-COMMIT-SHA>`) fail the patterns by design.
Handoffs: no `sessions/handoffs/` directory exists; if one appears, every file
in it is validated against the handoff schema by the same checker.

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import re
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINTS = ROOT / "sessions" / "checkpoints"
HANDOFFS = ROOT / "sessions" / "handoffs"
CHECKPOINT_SCHEMA = ROOT / "schemas" / "session-checkpoint.schema.json"
HANDOFF_SCHEMA = ROOT / "schemas" / "handoff.schema.json"

# Keywords the checker implements. Anything else found in a schema fails
# test_every_schema_keyword_is_implemented. Annotation keywords that carry no
# constraint are listed so they are recognised, not enforced.
IMPLEMENTED = {
    "type", "properties", "required", "additionalProperties", "items",
    "enum", "const", "pattern", "format", "minLength", "minItems",
    "minProperties", "uniqueItems",
}
ANNOTATIONS = {"$schema", "$id", "title", "description"}

# Checkpoints that predate enforcement and fail the schema on shape. Each
# entry: the file, the JSON paths that fail, and why it is not repaired.
# test_registered_legacy_checkpoints_still_fail insists each still fails at
# exactly these paths; delete the entry when the record is re-issued.
LEGACY: dict[str, tuple[tuple[str, ...], str]] = {
    "BIZTRUST-GUIDE-WP-017-engineering-ready.json": (
        ("$.validation[0]", "$.validation[1]", "$.validation[2]", "$.blockers[0]"),
        "validation entries and the blocker are strings; the strings record no "
        "status or exit code to lift into the object shape without inventing one",
    ),
    "BIZTRUST-GUIDE-WP-024-engineering-ready.json": (
        ("$.validation[0]", "$.validation[1]"),
        "validation entries are strings ('47 tests', 'exit 0'); a status would be inferred",
    ),
    "BIZTRUST-GUIDE-WP-026-engineering-ready.json": (
        ("$.validation[0]", "$.validation[1]"),
        "validation entries are strings ('53 tests', 'exit 0'); a status would be inferred",
    ),
}

_TYPES = {
    "object": dict, "array": list, "string": str, "integer": int,
    "number": (int, float), "boolean": bool, "null": type(None),
}


def _is_type(value, name: str) -> bool:
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "boolean":
        return isinstance(value, bool)
    return isinstance(value, _TYPES[name])


def _date_time(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return bool(re.search(r"(Z|[+-]\d\d:\d\d)$", value))


def errors(instance, schema: dict, path: str = "$") -> list[str]:
    """Every way `instance` fails `schema`, as 'json-path: reason' strings.

    Unknown keywords are NOT skipped silently: they raise, so a schema this
    checker cannot enforce cannot produce a PASS.
    """
    out: list[str] = []
    for key in schema:
        if key not in IMPLEMENTED and key not in ANNOTATIONS:
            raise NotImplementedError(f"{path}: schema keyword {key!r} is not implemented")

    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is_type(instance, n) for n in names):
            out.append(f"{path}: expected {' or '.join(names)}, got {type(instance).__name__}")
            return out  # further keywords assume the type
    if "enum" in schema and instance not in schema["enum"]:
        out.append(f"{path}: {instance!r} is not one of {schema['enum']}")
    if "const" in schema and instance != schema["const"]:
        out.append(f"{path}: {instance!r} is not the constant {schema['const']!r}")

    if isinstance(instance, str):
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            out.append(f"{path}: {instance!r} does not match {schema['pattern']!r}")
        if "minLength" in schema and len(instance) < schema["minLength"]:
            out.append(f"{path}: shorter than minLength {schema['minLength']}")
        if schema.get("format") == "date-time" and not _date_time(instance):
            out.append(f"{path}: {instance!r} is not an RFC 3339 date-time with offset")
        elif "format" in schema and schema["format"] != "date-time":
            raise NotImplementedError(f"{path}: format {schema['format']!r} is not implemented")

    if isinstance(instance, dict):
        props = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in instance:
                out.append(f"{path}: required property {name!r} is missing")
        if schema.get("additionalProperties") is False:
            for name in instance:
                if name not in props:
                    out.append(f"{path}: property {name!r} is not declared")
        elif isinstance(schema.get("additionalProperties"), dict):
            for name, value in instance.items():
                if name not in props:
                    out.extend(errors(value, schema["additionalProperties"], f"{path}.{name}"))
        if "minProperties" in schema and len(instance) < schema["minProperties"]:
            out.append(f"{path}: fewer than minProperties {schema['minProperties']}")
        for name, sub in props.items():
            if name in instance:
                out.extend(errors(instance[name], sub, f"{path}.{name}"))

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            out.append(f"{path}: fewer than minItems {schema['minItems']}")
        if schema.get("uniqueItems"):
            seen = [json.dumps(v, sort_keys=True) for v in instance]
            if len(seen) != len(set(seen)):
                out.append(f"{path}: items are not unique")
        if "items" in schema:
            for i, value in enumerate(instance):
                out.extend(errors(value, schema["items"], f"{path}[{i}]"))
    return out


def _keywords(node, acc: set[str], in_properties: bool = False) -> set[str]:
    """Every keyword position in a schema tree. Keys directly under
    `properties` are property NAMES, not keywords, and are skipped."""
    if isinstance(node, dict):
        for key, value in node.items():
            if in_properties:
                _keywords(value, acc)
            else:
                acc.add(key)
                _keywords(value, acc, in_properties=(key == "properties"))
    elif isinstance(node, list):
        for value in node:
            _keywords(value, acc)
    return acc


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class TestCheckerCoversTheSchemas(unittest.TestCase):
    def test_every_schema_keyword_is_implemented(self) -> None:
        """A keyword the checker does not know must fail here, loudly, rather
        than pass every instance by being ignored."""
        for schema_path in (CHECKPOINT_SCHEMA, HANDOFF_SCHEMA):
            with self.subTest(schema=schema_path.name):
                found = _keywords(load(schema_path), set())
                unknown = sorted(found - IMPLEMENTED - ANNOTATIONS)
                self.assertEqual(
                    unknown, [],
                    f"{schema_path.name} uses keywords this checker does not implement: "
                    f"{unknown}. Implement them in errors() and add them to IMPLEMENTED; "
                    f"do not remove them from the schema to make this pass.",
                )

    def test_checker_can_fail(self) -> None:
        """Negative controls: the same defects the three legacy records carry,
        plus the ones a careless author is most likely to produce next."""
        schema = load(CHECKPOINT_SCHEMA)
        good = load(CHECKPOINTS / "BIZTRUST-GUIDE-WP-033-engineering-ready.json")
        self.assertEqual(errors(good, schema), [], "the positive control must validate")

        def broken(mutate):
            doc = json.loads(json.dumps(good))
            mutate(doc)
            return errors(doc, schema)

        cases = {
            "validation entry is a string": lambda d: d["validation"].__setitem__(0, "python3 -m unittest - OK"),
            "blocker is a string": lambda d: d["blockers"].__setitem__(0, "needs a human"),
            "required key missing": lambda d: d.pop("declared_non_coverage"),
            "undeclared key": lambda d: d.__setitem__("notes", []),
            "short baseline sha": lambda d: d["source"].__setitem__("baseline_commit", "abc123"),
            "unknown state": lambda d: d.__setitem__("state", "DONE"),
            "created_at without offset": lambda d: d.__setitem__("created_at", "2026-09-04T16:00:00"),
            "exit_code is a string": lambda d: d["validation"][0].__setitem__("exit_code", "0"),
            "files_changed repeats": lambda d: d["files_changed"].append(d["files_changed"][0]),
            "empty stop_if": lambda d: d["recovery"].__setitem__("stop_if", []),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                self.assertTrue(broken(mutate), f"{name}: the checker reported no error")

    def test_unknown_keyword_raises_rather_than_passes(self) -> None:
        with self.assertRaises(NotImplementedError):
            errors({"a": 1}, {"type": "object", "dependentRequired": {"a": ["b"]}})


class TestCommittedCheckpoints(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = load(CHECKPOINT_SCHEMA)
        self.files = sorted(CHECKPOINTS.glob("*.json"))

    def test_corpus_is_present(self) -> None:
        """Without this, an emptied directory passes every assertion below."""
        self.assertGreaterEqual(len(self.files), 16, [p.name for p in self.files])

    def test_every_unregistered_checkpoint_conforms(self) -> None:
        failing = []
        for path in self.files:
            if path.name in LEGACY:
                continue
            found = errors(load(path), self.schema)
            if found:
                failing.append(f"  {path.name}:\n    " + "\n    ".join(found))
        if failing:
            self.fail(
                f"{len(failing)} checkpoint(s) do not conform to "
                f"schemas/session-checkpoint.schema.json. Fix the record, not the "
                f"schema; LEGACY admits only the three that predate enforcement:\n"
                + "\n".join(failing)
            )

    def test_registered_legacy_checkpoints_still_fail(self) -> None:
        """The registry is a ratchet: an entry must still fail, at exactly the
        paths it is registered for. A repaired record must leave the list."""
        for name, (paths, reason) in LEGACY.items():
            with self.subTest(checkpoint=name):
                self.assertGreater(len(reason.split()), 8, f"{name}: registry needs a reason")
                found = errors(load(CHECKPOINTS / name), self.schema)
                got = tuple(sorted({e.split(":")[0] for e in found}))
                self.assertEqual(
                    got, tuple(sorted(paths)),
                    f"{name} no longer fails at the registered paths - it now fails at "
                    f"{got}. If it conforms, delete LEGACY[{name!r}]; if it fails "
                    f"elsewhere, the record changed and that needs a reason.",
                )

    def test_registry_admits_only_the_three_that_predate_enforcement(self) -> None:
        self.assertEqual(
            sorted(LEGACY),
            ["BIZTRUST-GUIDE-WP-017-engineering-ready.json",
             "BIZTRUST-GUIDE-WP-024-engineering-ready.json",
             "BIZTRUST-GUIDE-WP-026-engineering-ready.json"],
            "LEGACY may only shrink. A checkpoint written after WP-035 that fails "
            "the schema is a defect in the checkpoint, not a candidate for this list.",
        )


class TestHandoffs(unittest.TestCase):
    def test_handoffs_conform_if_any_exist(self) -> None:
        if not HANDOFFS.is_dir():
            self.skipTest("sessions/handoffs/ does not exist; no handoff has been recorded")
        schema = load(HANDOFF_SCHEMA)
        for path in sorted(HANDOFFS.glob("*.json")):
            with self.subTest(handoff=path.name):
                self.assertEqual(errors(load(path), schema), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
