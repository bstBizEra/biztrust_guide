#!/usr/bin/env python3
"""Verify the Markdown-first Delivery Control Room fails closed.

The committed HTML is a deterministic projection.  These tests prove that
ambiguous governance state, unsafe Markdown and source/display drift cannot
silently produce a credible-looking control surface.

Stdlib only::

    python3 -m unittest tests.test_control_room -v
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "scripts" / "build_control_room.py"

SPEC = importlib.util.spec_from_file_location("biztrust_control_room_builder", BUILDER_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import machinery guard
    raise RuntimeError(f"cannot load {BUILDER_PATH}")
BUILDER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BUILDER
SPEC.loader.exec_module(BUILDER)


class LinkParser(HTMLParser):
    """Collect references from generated HTML without executing it."""

    def __init__(self) -> None:
        super().__init__()
        self.references: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for attribute in ("href", "src"):
            value = values.get(attribute)
            if value:
                self.references.append((tag, value))


class SourceHarness(unittest.TestCase):
    """Copy Markdown sources so negative tests cannot mutate the worktree."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.temp_root = Path(self._temp.name)
        self.source = self.temp_root / "control-room"
        shutil.copytree(ROOT / "docs" / "control-room", self.source)
        self.addCleanup(self._temp.cleanup)

    def replace(self, filename: str, old: str, new: str) -> None:
        path = self.source / filename
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"test fixture no longer contains {old!r}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")


class TestGeneratedControlRoom(unittest.TestCase):
    def test_committed_html_matches_markdown(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(BUILDER_PATH), "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), "CONTROL_ROOM_BUILD=PASS")

    def test_registered_views_have_one_session_and_one_primary_action(self) -> None:
        sections = BUILDER.load_sections(ROOT / "docs" / "control-room")
        self.assertEqual(len(sections), 10)
        self.assertEqual([section.id for section in sections][0:3], ["session", "today", "plan"])
        self.assertEqual(sum(section.id == "session" for section in sections), 1)
        self.assertEqual(sum(section.metadata.get("primary") is True for section in sections), 1)

    def test_generated_page_has_operational_and_accessibility_spine(self) -> None:
        page = (ROOT / "stages" / "control-room.html").read_text(encoding="utf-8")
        self.assertEqual(page.count("<h1"), 1)
        self.assertEqual(page.count('<section class="cr-panel"'), 10)
        self.assertIn('class="cr-skip" href="#control-room-main"', page)
        self.assertIn('<main class="cr-main" id="control-room-main">', page)
        self.assertIn('<label for="controlRoomSearch">', page)
        self.assertIn('aria-live="polite"', page)
        self.assertIn('name="source-digest"', page)
        self.assertIn("default-src 'self'", page)
        self.assertNotRegex(page, r"@@[A-Z_]+@@")
        self.assertIn(
            'href="stages/control-room.html"',
            (ROOT / "index.html").read_text(encoding="utf-8"),
        )

    def test_every_generated_local_reference_exists(self) -> None:
        page_path = ROOT / "stages" / "control-room.html"
        parser = LinkParser()
        parser.feed(page_path.read_text(encoding="utf-8"))
        checked = 0
        for tag, reference in parser.references:
            parts = urlsplit(reference)
            if parts.scheme in {"http", "https", "mailto", "tel", "data"}:
                continue
            if not parts.path:
                continue
            target = (page_path.parent / parts.path).resolve()
            self.assertTrue(target.exists(), f"missing local {tag} reference: {reference}")
            checked += 1
        self.assertGreaterEqual(checked, 2, "expected local navigation and brand assets")

    def test_source_digest_changes_when_markdown_changes(self) -> None:
        sections = BUILDER.load_sections(ROOT / "docs" / "control-room")
        digest = BUILDER.source_digest(sections)
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        page = (ROOT / "stages" / "control-room.html").read_text(encoding="utf-8")
        self.assertGreaterEqual(page.count(digest), 2)

    def test_checkpoint_matches_the_repository_schema_contract(self) -> None:
        schema = json.loads(
            (ROOT / "schemas" / "session-checkpoint.schema.json").read_text(encoding="utf-8")
        )
        checkpoint = json.loads(
            (
                ROOT
                / "sessions"
                / "checkpoints"
                / "BIZTRUST-GUIDE-WP-018-engineering-ready.json"
            ).read_text(encoding="utf-8")
        )
        required = set(schema["required"])
        properties = set(schema["properties"])
        self.assertEqual(set(checkpoint), required)
        self.assertFalse(set(checkpoint) - properties)
        self.assertIn(checkpoint["state"], schema["properties"]["state"]["enum"])
        self.assertRegex(checkpoint["source"]["baseline_commit"], r"^[0-9a-f]{40}$")
        BUILDER.validate_datetime(checkpoint["created_at"], "checkpoint.created_at")
        self.assertEqual(len(checkpoint["files_changed"]), len(set(checkpoint["files_changed"])))
        self.assertTrue(checkpoint["declared_non_coverage"])
        for result in checkpoint["validation"]:
            self.assertEqual(set(result), {"command", "status", "exit_code"})
            self.assertIn(
                result["status"],
                schema["properties"]["validation"]["items"]["properties"]["status"]["enum"],
            )
        for blocker in checkpoint["blockers"]:
            self.assertTrue({"code", "owner_role", "resolution"}.issubset(blocker))


class TestSourceContractFailsClosed(SourceHarness):
    def test_missing_required_field_is_rejected(self) -> None:
        self.replace("30-plan.md", "owner: chief-orchestrator\n", "")
        with self.assertRaisesRegex(BUILDER.ControlRoomError, "missing required frontmatter: owner"):
            BUILDER.load_sections(self.source)

    def test_duplicate_section_id_is_rejected(self) -> None:
        shutil.copy2(self.source / "30-plan.md", self.source / "31-duplicate-plan.md")
        with self.assertRaisesRegex(BUILDER.ControlRoomError, "duplicate section id"):
            BUILDER.load_sections(self.source)

    def test_second_primary_action_is_rejected(self) -> None:
        self.replace(
            "30-plan.md",
            "\n---\n\n## Now",
            "\nprimary: true\nprimary_action: Competing action\n---\n\n## Now",
        )
        with self.assertRaisesRegex(BUILDER.ControlRoomError, "exactly one primary section; found 2"):
            BUILDER.load_sections(self.source)

    def test_primary_without_action_is_rejected(self) -> None:
        self.replace(
            "20-today.md",
            "primary_action: NS-001 — Enable GitHub Pages using GitHub Actions and retain the successful deployment evidence.\n",
            "",
        )
        with self.assertRaisesRegex(BUILDER.ControlRoomError, "requires primary_action"):
            BUILDER.load_sections(self.source)

    def test_timezone_less_expiry_is_rejected(self) -> None:
        self.replace(
            "10-session.md",
            "refresh_by: 2026-09-04T00:00:00+07:00",
            "refresh_by: 2026-09-04T00:00:00",
        )
        with self.assertRaisesRegex(BUILDER.ControlRoomError, "must include a timezone offset"):
            BUILDER.load_sections(self.source)


class TestMarkdownSafety(unittest.TestCase):
    def test_unsafe_link_scheme_is_rejected(self) -> None:
        with self.assertRaisesRegex(BUILDER.ControlRoomError, "unsafe link scheme"):
            BUILDER.markdown_to_html("[do not run](javascript:alert(1))")

    def test_raw_html_is_rendered_as_text(self) -> None:
        rendered = BUILDER.markdown_to_html("<script>alert('unsafe')</script>")
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_unclosed_code_fence_is_rejected(self) -> None:
        with self.assertRaisesRegex(BUILDER.ControlRoomError, "unclosed fenced code block"):
            BUILDER.markdown_to_html("```text\nnot closed")

    def test_malformed_table_is_rejected(self) -> None:
        malformed = "| A | B |\n|---|---|\n| only one |"
        with self.assertRaisesRegex(BUILDER.ControlRoomError, "different column count"):
            BUILDER.markdown_to_html(malformed)


class TestDriftDetection(SourceHarness):
    def test_check_mode_rejects_hand_edited_output(self) -> None:
        stale = self.temp_root / "control-room.html"
        stale.write_text("<!doctype html><title>hand edited</title>\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(BUILDER_PATH),
                "--source-dir",
                str(self.source),
                "--template",
                str(ROOT / "templates" / "control-room-shell.tpl"),
                "--output",
                str(stale),
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("CONTROL_ROOM_BUILD=FAIL", result.stdout)
        self.assertIn("generated HTML is stale", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
