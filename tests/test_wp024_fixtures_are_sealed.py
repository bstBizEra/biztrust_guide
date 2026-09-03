"""The WP-024 fixtures must match what build.py produces, byte for byte.

A hand-edited RESUME.json leaves its manifest describing a file that no longer
exists, which silently turns every fixture into fixture 9. The experiment would
then measure integrity detection nine times and report it as an aggregate.

This guards the seal, not the deriver. build.py contains hand-authored fixture
content and computes only byte counts and digests.
"""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "docs/experiments/fixtures/build.py"


class TestFixturesAreSealed(unittest.TestCase):
    def test_committed_fixtures_match_their_source(self) -> None:
        proc = subprocess.run([sys.executable, "-B", str(BUILD), "--check"],
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("FIXTURES=CURRENT", proc.stdout)

    def test_the_check_can_fail(self) -> None:
        """Without this the check above passes hardest when it stops checking."""
        victim = ROOT / "docs/experiments/fixtures/01-fresh/RESUME.json"
        original = victim.read_bytes()
        try:
            victim.write_bytes(original.replace(b'"CONTINUE"', b'"BLOCKED"', 1))
            proc = subprocess.run([sys.executable, "-B", str(BUILD), "--check"],
                                  capture_output=True, text=True, timeout=60)
            self.assertEqual(proc.returncode, 1, "a mutated fixture must not report CURRENT")
            self.assertIn("FIXTURES=STALE", proc.stdout)
        finally:
            victim.write_bytes(original)

    def test_every_fixture_has_all_four_artifacts(self) -> None:
        base = ROOT / "docs/experiments/fixtures"
        dirs = sorted(p for p in base.iterdir() if p.is_dir())
        self.assertEqual(len(dirs), 9, "the protocol fixes the count at nine")
        for d in dirs:
            for name in ("RESUME.json", "control-room.html.frozen",
                         "manifest.yaml", "oracle.yaml"):
                self.assertTrue((d / name).is_file(), f"{d.name} is missing {name}")

    def test_no_fixture_ships_a_deployable_page(self) -> None:
        """`git ls-files '*.html'` is what the Pages workflow stages. A fixture
        named .html would be published - including the tampered one."""
        stray = list((ROOT / "docs/experiments/fixtures").rglob("*.html"))
        self.assertEqual([], stray, f"fixture HTML must stay .frozen, found {stray}")


if __name__ == "__main__":
    unittest.main()
