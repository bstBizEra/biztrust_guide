#!/usr/bin/env python3
"""Every committed checkpoint conforms to schemas/session-checkpoint.schema.json.

AGENTS.md section 6 says every checkpoint must conform to the schema, and until
BIZTRUST-GUIDE-WP-035 (issue #68) nothing checked it: the validator confirmed
only that the schema file parsed and declared the right dialect. Measured
before this file existed, three of seventeen committed checkpoints failed the
schema - WP-017, WP-024 and WP-026 record `validation` entries as strings
where the schema requires objects, and WP-017's one blocker is a string too -
and nothing would have noticed a seventeenth.

WHY A HAND-ROLLED CHECKER
=========================

The repository is stdlib-only by policy, and `jsonschema` is not in the
stdlib. So this file implements the SUBSET of JSON Schema 2020-12 the two
schemas in `schemas/` actually use - and no more. The subset is not a guess:
`test_every_schema_keyword_is_implemented` walks both schema files and fails
on any keyword - or any `format` value - the checker does not know, so a
schema edit that reaches for `oneOf`, `$ref`, `dependentRequired`,
`format: uri` or anything else is refused here rather than silently
unenforced.

WHERE IT IS STRICTER THAN THE SPECIFICATION, ON PURPOSE
`integer` rejects `1.0` (the specification accepts it); `date-time` is the
RFC 3339 grammar with a calendar day check, so `2026-09-04T16:00Z` (no
seconds) and `2026-13-01T00:00:00Z` are refused. Both directions fail closed.
The first review of this file found that `datetime.fromisoformat` accepted six
forms RFC 3339 does not, on `created_at`, a field every checkpoint carries -
and that the `jsonschema` install on the authoring machine had no `date-time`
checker at all, so a calibration against it could not have caught that. The
calibration that WAS run is structural: over every committed checkpoint the
checker reports the same failing files and JSON paths as jsonschema 4.26.0. A checker that ignores keywords it does not
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

import calendar
import json
import re
import unittest
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
    # format VALUES are keywords too, for coverage purposes: an unimplemented
    # format on an optional property would otherwise never be noticed.
    "format:date-time",
}
ANNOTATIONS = {"$schema", "$id", "title", "description", "$comment", "examples", "default", "deprecated"}

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


_RFC3339 = re.compile(
    r"^(\d{4})-(0[1-9]|1[0-2])-(\d{2})[Tt]([01]\d|2[0-3]):[0-5]\d:([0-5]\d|60)"
    r"(\.\d+)?([Zz]|[+-]([01]\d|2[0-3]):[0-5]\d)$"
)


def _date_time(value: str) -> bool:
    """RFC 3339 date-time: full date, 'T', full time with seconds, offset or Z,
    and a day that exists in that month."""
    m = _RFC3339.match(value)
    if not m:
        return False
    year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return 1 <= day <= calendar.monthrange(year, month)[1]


def _canon(value):
    """JSON-Schema equality: booleans are not numbers, 1 == 1.0, key order
    is irrelevant. Used by enum, const and uniqueItems."""
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, (int, float)):
        return ("num", float(value))
    if isinstance(value, dict):
        return ("obj", tuple(sorted((k, _canon(v)) for k, v in value.items())))
    if isinstance(value, list):
        return ("arr", tuple(_canon(v) for v in value))
    return (type(value).__name__, value)


def errors(instance, schema: dict, path: str = "$") -> list[str]:
    """Every way `instance` fails `schema`, as 'json-path: reason' strings.

    Unknown keywords are NOT skipped silently: they raise, so a schema this
    checker cannot enforce cannot produce a PASS.
    """
    out: list[str] = []
    if schema is True:
        return out
    if schema is False:
        return [f"{path}: schema is false; no instance is valid"]
    for key in schema:
        if key not in IMPLEMENTED and key not in ANNOTATIONS:
            raise NotImplementedError(f"{path}: schema keyword {key!r} is not implemented")
    if "format" in schema and f"format:{schema['format']}" not in IMPLEMENTED:
        raise NotImplementedError(f"{path}: format {schema['format']!r} is not implemented")

    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is_type(instance, n) for n in names):
            out.append(f"{path}: expected {' or '.join(names)}, got {type(instance).__name__}")
            return out  # further keywords assume the type
    if "enum" in schema and _canon(instance) not in [_canon(v) for v in schema["enum"]]:
        out.append(f"{path}: {instance!r} is not one of {schema['enum']}")
    if "const" in schema and _canon(instance) != _canon(schema["const"]):
        out.append(f"{path}: {instance!r} is not the constant {schema['const']!r}")

    if isinstance(instance, str):
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            out.append(f"{path}: {instance!r} does not match {schema['pattern']!r}")
        if "minLength" in schema and len(instance) < schema["minLength"]:
            out.append(f"{path}: shorter than minLength {schema['minLength']}")
        if schema.get("format") == "date-time" and not _date_time(instance):
            out.append(f"{path}: {instance!r} is not an RFC 3339 date-time")

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
            seen = [_canon(v) for v in instance]
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
                if key == "format" and isinstance(value, str):
                    acc.add(f"format:{value}")
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
            "created_at without seconds": lambda d: d.__setitem__("created_at", "2026-09-04T16:00Z"),
            "created_at with a space separator": lambda d: d.__setitem__("created_at", "2026-09-04 16:00:00Z"),
            "created_at with a comma fraction": lambda d: d.__setitem__("created_at", "2026-09-04T16:00:00,123Z"),
            "created_at basic format": lambda d: d.__setitem__("created_at", "20260904T160000Z"),
            "created_at week date": lambda d: d.__setitem__("created_at", "2026-W36-5T16:00:00Z"),
            "created_at month 13": lambda d: d.__setitem__("created_at", "2026-13-01T00:00:00Z"),
            "created_at 31 February": lambda d: d.__setitem__("created_at", "2026-02-31T00:00:00Z"),
            "exit_code is a boolean": lambda d: d["validation"][0].__setitem__("exit_code", False),
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
        # An unimplemented FORMAT raises before any instance is inspected, and
        # the coverage walk reports it, so it cannot hide on an optional field.
        with self.assertRaises(NotImplementedError):
            errors(None, {"type": ["string", "null"], "format": "uri"})
        self.assertIn("format:uri", _keywords({"properties": {"u": {"type": "string", "format": "uri"}}}, set()))

    def test_date_time_is_rfc3339(self) -> None:
        for good in ("2026-09-04T16:00:00Z", "2026-09-04t16:00:00z", "2026-09-04T16:00:00.123+07:00",
                     "2026-02-28T23:59:60-00:30", "2024-02-29T00:00:00Z"):
            self.assertTrue(_date_time(good), good)
        for bad in ("2026-09-04", "2026-09-04T16:00:00", "2026-09-04T16:00Z", "2026-09-04 16:00:00Z",
                    "2026-09-04T16:00:00,123Z", "20260904T160000Z", "2026-W36-5T16:00:00Z",
                    "2026-09-04T16:00:00.Z", "2026-13-01T00:00:00Z", "2026-02-31T00:00:00Z",
                    "2023-02-29T00:00:00Z", "2026-09-04T24:00:00Z", "2026-09-04T16:00:00+24:00"):
            self.assertFalse(_date_time(bad), bad)

    def test_equality_follows_json_schema(self) -> None:
        """Booleans are not numbers; 1 and 1.0 are equal; key order is not identity."""
        self.assertTrue(errors(1, {"const": True}))
        self.assertTrue(errors(True, {"enum": [1]}))
        self.assertFalse(errors(1.0, {"enum": [1]}))
        self.assertTrue(errors([1, 1.0], {"type": "array", "uniqueItems": True}))
        self.assertTrue(errors([{"a": 1, "b": 2}, {"b": 2, "a": 1}], {"type": "array", "uniqueItems": True}))
        self.assertFalse(errors([1, True], {"type": "array", "uniqueItems": True}))


class TestCommittedCheckpoints(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = load(CHECKPOINT_SCHEMA)
        self.files = sorted(CHECKPOINTS.glob("*.json"))

    def test_corpus_is_present(self) -> None:
        """Without this, an emptied directory passes every assertion below."""
        self.assertGreaterEqual(len(self.files), 18, [p.name for p in self.files])

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
        # Structural: nothing numbered at or after the package that added
        # enforcement can be registered, whatever the literal below says.
        for name in LEGACY:
            number = int(re.search(r"WP-(\d+)", name).group(1))
            self.assertLess(number, 35, f"{name} postdates enforcement (WP-035) and cannot be legacy")
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
