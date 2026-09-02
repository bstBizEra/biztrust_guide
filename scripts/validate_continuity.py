#!/usr/bin/env python3
"""Fail-closed continuity and static-site validation for BizTrust Guide."""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SHA40 = re.compile(r"^[0-9a-f]{40}$")


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.refs: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"] or "")
        for attr in ("href", "src"):
            if values.get(attr):
                self.refs.append((tag, values[attr] or ""))


def load_json(relative: str, errors: list[str]) -> dict:
    path = ROOT / relative
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{relative}: cannot load valid JSON: {exc}")
        return {}


def main() -> int:
    errors: list[str] = []
    checks: list[str] = []
    required = [
        "AGENTS.md",
        "README.md",
        "index.html",
        "styles.css",
        "script.js",
        ".nojekyll",
        ".github/workflows/pages.yml",
        "badf/current-state.json",
        "badf/next-actions.json",
        "badf/decision-log.jsonl",
        "schemas/session-checkpoint.schema.json",
        "schemas/handoff.schema.json",
        "templates/session-checkpoint.json",
        "templates/handoff.json",
        "docs/LIVE_PREVIEW.md",
        "docs/AGENT_CONTINUITY.md",
        "docs/NEXT_STEPS.md",
    ]
    missing = [item for item in required if not (ROOT / item).is_file()]
    if missing:
        errors.append("Missing required files: " + ", ".join(missing))
    else:
        checks.append(f"required-files:{len(required)}")

    current = load_json("badf/current-state.json", errors)
    actions = load_json("badf/next-actions.json", errors)
    checkpoint: dict = {}
    checkpoint_path = current.get("latest_checkpoint")
    if checkpoint_path:
        checkpoint = load_json(checkpoint_path, errors)
    else:
        errors.append("current-state: latest_checkpoint is missing")

    if current and actions:
        wp = current.get("active_work_package", {})
        wp_id = wp.get("id")
        if not wp_id or wp_id != actions.get("work_package_id"):
            errors.append("State/action Work Package IDs do not match")
        if checkpoint and checkpoint.get("work_package_id") != wp_id:
            errors.append("Checkpoint Work Package ID does not match current state")
        if current.get("project_id") != actions.get("project_id"):
            errors.append("State/action project IDs do not match")
        baseline = current.get("source", {}).get("baseline_commit", "")
        if not SHA40.fullmatch(baseline):
            errors.append("Current-state baseline_commit is not a 40-character SHA")
        action_rows = actions.get("actions", [])
        action_ids = [row.get("id") for row in action_rows]
        if len(action_ids) != len(set(action_ids)):
            errors.append("next-actions contains duplicate action IDs")
        primary = [row for row in action_rows if row.get("primary") is True]
        if len(primary) != 1:
            errors.append("next-actions must contain exactly one primary action")
        elif primary[0].get("id") != current.get("primary_next_action_id"):
            errors.append("Primary next action does not match current state")
        priorities = [row.get("priority") for row in action_rows]
        if any(not isinstance(value, int) or value < 1 for value in priorities):
            errors.append("Every next action requires a positive integer priority")
        if priorities != sorted(priorities):
            errors.append("Next actions must be stored in priority order")
        required_action_fields = {
            "id", "primary", "priority", "owner_role", "authority", "action",
            "prerequisites", "evidence_required", "stop_conditions", "fallback"
        }
        for row in action_rows:
            absent = required_action_fields - row.keys()
            if absent:
                errors.append(f"Action {row.get('id', '<unknown>')} missing: {sorted(absent)}")
        checks.append(f"continuity-actions:{len(action_rows)}")

    if checkpoint:
        baseline = checkpoint.get("source", {}).get("baseline_commit", "")
        if not SHA40.fullmatch(baseline):
            errors.append("Checkpoint baseline_commit is not a 40-character SHA")
        if checkpoint.get("next_action_id") != current.get("primary_next_action_id"):
            errors.append("Checkpoint next action does not match current state")
        if not checkpoint.get("declared_non_coverage"):
            errors.append("Checkpoint must declare non-coverage")
        recovery = checkpoint.get("recovery", {})
        if not recovery.get("first_safe_command") or not recovery.get("stop_if"):
            errors.append("Checkpoint recovery contract is incomplete")
        checks.append("checkpoint:linked")

    decision_ids: set[str] = set()
    decision_path = ROOT / "badf/decision-log.jsonl"
    if decision_path.is_file():
        for number, line in enumerate(decision_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"decision-log line {number}: {exc}")
                continue
            decision_id = row.get("id")
            if not decision_id or decision_id in decision_ids:
                errors.append(f"decision-log line {number}: missing or duplicate ID")
            decision_ids.add(decision_id)
        checks.append(f"decisions:{len(decision_ids)}")

    for schema in ("schemas/session-checkpoint.schema.json", "schemas/handoff.schema.json"):
        data = load_json(schema, errors)
        if data and data.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append(f"{schema}: unsupported or missing JSON Schema dialect")
    checks.append("schemas:json-valid")

    skip_parts = {".git", "_site", "node_modules"}
    pages = sorted(
        page
        for page in ROOT.rglob("*.html")
        if not skip_parts.intersection(page.relative_to(ROOT).parts)
    )
    page_ids: dict[Path, set[str]] = {}
    page_refs: dict[Path, list[tuple[str, str]]] = {}
    for page in pages:
        parser = SiteParser()
        parser.feed(page.read_text(encoding="utf-8"))
        page_ids[page.resolve()] = parser.ids
        page_refs[page.resolve()] = parser.refs

    if not (ROOT / "index.html").is_file():
        errors.append("index.html is not present at the publishing root")

    for page in pages:
        key = page.resolve()
        rel = page.relative_to(ROOT).as_posix()
        for tag, ref in page_refs[key]:
            if ref.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                continue
            parts = urlsplit(ref)
            if not parts.path and parts.fragment:
                if parts.fragment not in page_ids[key]:
                    errors.append(f"{rel}: broken fragment #{parts.fragment}")
                continue
            if not parts.path:
                continue
            target = (page.parent / parts.path).resolve()
            if ROOT not in target.parents and target != ROOT:
                errors.append(f"{rel}: {tag} reference escapes the site root: {parts.path}")
                continue
            if not target.exists():
                errors.append(f"{rel}: missing local {tag} reference {parts.path}")
                continue
            if parts.fragment and target.suffix == ".html":
                target_ids = page_ids.get(target)
                if target_ids is None:
                    errors.append(f"{rel}: cross-page fragment target not validated: {parts.path}")
                elif parts.fragment not in target_ids:
                    errors.append(
                        f"{rel}: broken cross-page fragment {parts.path}#{parts.fragment}"
                    )

    checks.append(f"html-pages:{len(pages)}")
    checks.append(f"html-ids:{sum(len(v) for v in page_ids.values())}")
    checks.append(f"html-refs:{sum(len(v) for v in page_refs.values())}")

    workflow_path = ROOT / ".github/workflows/pages.yml"
    if workflow_path.is_file():
        workflow = workflow_path.read_text(encoding="utf-8")
        for token in (
            "actions/checkout@v7",
            "actions/configure-pages@v5",
            "actions/upload-pages-artifact@v4",
            "actions/deploy-pages@v4",
            "pages: write",
            "id-token: write",
            "environment:",
            "github-pages",
        ):
            if token not in workflow:
                errors.append(f"pages workflow missing required token: {token}")
        checks.append("pages-workflow:baseline")

    if errors:
        print("CONTINUITY_VALIDATION=FAIL")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("CONTINUITY_VALIDATION=PASS")
    for check in checks:
        print(f"PASS: {check}")
    print(f"RESUME_DECISION={current.get('resume_decision', 'UNKNOWN')}")
    print(f"PRIMARY_NEXT_ACTION={current.get('primary_next_action_id', 'UNKNOWN')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

