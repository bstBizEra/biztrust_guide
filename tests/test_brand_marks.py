#!/usr/bin/env python3
"""The site wears BizTrust's mark, ships no asset it does not use, and leaves the gradient alone.

Three defects were found by reading, not by any check, and this module is what would
have found them.

1. A TENANT'S MARK ON THE PLATFORM'S OWN HANDBOOK. All nineteen handbook pages carried
   `assets/unitrust-*.png` in the topbar, the footer, the closing directive and the
   favicon: fifty-seven references. UniTrust is Tenant A, the synthetic broker this
   guide uses for worked examples, so `index.html` announced `alt="UniTrust Broker
   Insurance"` in its header above a footer reading "BizTrust Agentic Engineer Team".
   `tests/test_showcase_pages.py::test_no_tenant_mark` forbade this on the nine
   showcase pages and nowhere else, and the showcase record cited the handbook's marks
   as the reason the showcase shared no chrome with it. That test stays where it is,
   because "no tenant mark anywhere under landing/" is a rule SHOWCASE-001 states and
   that module tests SHOWCASE-001. The rule here is the wider one no record had yet
   written down: no page of this site wears a tenant's mark, handbook included.

2. AN ASSET SHIPPED AND NEVER USED. `assets/unitrust-vertical.png` was copied into
   every published artifact by `.github/workflows/pages.yml` and referenced by no page
   on the site. The workflow named its assets by hand in two places and the two lists
   had drifted from each other and from the pages. The workflow now copies what git
   tracks, which removes the drift; this module removes the orphan, by asking of every
   asset which page wants it.

3. NOTHING HELD THE GRADIENT. BizTrust_Brand_Identity_Guide_v1.0 section 8 forbids
   changing the gradient stops and section 5 measures the deepest of them at 2.62:1 on
   white, too low for text. Both rules are invisible to a stylesheet that has only
   hex literals in it, and `styles.css` is minified to 22 lines, where a wrong digit
   is not something a reviewer sees.

WHAT THIS DOES NOT DO. It does not check that a referenced file exists:
`scripts/validate_continuity.py` already resolves every `src` and `href` on every page
and fails on one that resolves to nothing. It does not check contrast, for the reasons
`tests/test_theme_token_pairs.py` sets out at length. It does not read the SVGs' own
contents, so an asset that is the right filename and the wrong artwork passes.

Positive controls: pages must be found, assets must be found, and every brand token
must be found in every stylesheet, or all three rules would hold over nothing.

The strongest control is not a mutation. Run against this repository at 82892da, the
commit this package branched from, the module reports 28 failures: nineteen pages each
naming a tenant's mark three times, assets/unitrust-vertical.png referenced by nothing,
and the gradient tokens absent from both stylesheets. Those first twenty are real
defects that had lived in the tree since the pages were written.

Negative controls (run 2026-09-07 under WP-103, each on a copied tree, each run as
`unittest discover -s tests -p test_brand_marks.py` from that tree's root - the way the
suite runs it). Each fails the test that names it and no other, and the unmutated copy
is green:
  * Point one page's favicon back at assets/unitrust-icon.png -> test_no_tenant_mark
  * Add assets/orphan.svg, referenced by nothing              -> test_every_asset_is_used
  * Change --bt-green to #3db38a                              -> test_gradient_stops_are_the_brands
  * Declare color:var(--bt-green) in showcase.css             -> test_no_brand_colour_as_text
  * Reverse the stops, leaving all three values correct       -> test_the_gradient_runs_light_to_deep

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
STYLESHEETS = ("styles.css", "landing/showcase.css")

# Directories that hold no published page. The same set the validator skips, for the
# same reason: _site is a build output and .git holds blobs that are not pages.
SKIP = {".git", "_site", "node_modules"}

# The signature gradient, from BizTrust_Brand_Identity_Guide_v1.0 section 4. These three
# values are the identity; section 8 lists changing them among the misuses.
BRAND_STOPS = (("--bt-sky", "#a5def3"), ("--bt-mint", "#69c6b5"), ("--bt-green", "#3db389"))

# Tenant A's mark, in any form. The tenant is synthetic and its name appears throughout
# the guide's prose, which is correct; what may not appear is its artwork.
TENANT_MARK = re.compile(r"(?i)assets/[^\"'\s]*unitrust|unitrust[^\"'\s]*\.(?:png|svg|jpe?g|webp|ico)")


def pages() -> list[Path]:
    """Every published page. is_file() matters: rglob matches a DIRECTORY named *.html."""
    return sorted(
        page
        for page in ROOT.rglob("*.html")
        if page.is_file() and not SKIP.intersection(page.relative_to(ROOT).parts)
    )


def assets() -> list[Path]:
    return sorted(path for path in ASSETS.rglob("*") if path.is_file())


def stylesheets() -> list[Path]:
    return [ROOT / name for name in STYLESHEETS]


def token_value(css: str, token: str) -> str | None:
    found = re.search(rf"{re.escape(token)}\s*:\s*([^;}}]+)", css)
    return found.group(1).strip().lower() if found else None


class TestNoTenantMark(unittest.TestCase):
    def test_pages_are_found(self) -> None:
        """Positive control: the rule below holds over nothing if no page is read."""
        self.assertGreaterEqual(len(pages()), 19, "fewer pages than the handbook alone has")

    def test_no_tenant_mark(self) -> None:
        for page in pages():
            with self.subTest(page=page.relative_to(ROOT).as_posix()):
                found = TENANT_MARK.findall(page.read_text(encoding="utf-8"))
                self.assertEqual([], found, "a tenant's mark on a BizTrust page")

    def test_no_tenant_mark_in_a_stylesheet(self) -> None:
        for sheet in stylesheets():
            with self.subTest(sheet=sheet.name):
                found = TENANT_MARK.findall(sheet.read_text(encoding="utf-8"))
                self.assertEqual([], found, "a tenant's mark in a stylesheet")


class TestAssetsAreUsed(unittest.TestCase):
    def corpus(self) -> str:
        parts = [page.read_text(encoding="utf-8") for page in pages()]
        parts += [sheet.read_text(encoding="utf-8") for sheet in stylesheets()]
        return "\n".join(parts)

    def test_assets_are_found(self) -> None:
        """Positive control: an empty assets/ would make the rule below vacuous."""
        self.assertGreater(len(assets()), 0, "no asset found to check")

    def test_every_asset_is_used(self) -> None:
        """An asset no page names is shipped to every visitor and seen by none.

        Matched by filename rather than by path, because a page one directory down
        writes the same asset as ../assets/<name>.
        """
        corpus = self.corpus()
        orphans = [
            asset.relative_to(ROOT).as_posix()
            for asset in assets()
            if asset.name not in corpus
        ]
        self.assertEqual([], orphans, f"assets referenced by no page or stylesheet: {orphans}")


class TestSignatureGradient(unittest.TestCase):
    def test_gradient_stops_are_the_brands(self) -> None:
        """Section 8: never change the gradient stops. Both stylesheets, same values."""
        for sheet in stylesheets():
            css = sheet.read_text(encoding="utf-8")
            for token, expected in BRAND_STOPS:
                with self.subTest(sheet=sheet.name, token=token):
                    value = token_value(css, token)
                    self.assertIsNotNone(value, f"{token} is not defined")
                    self.assertEqual(expected, value, f"{token} is not the brand's value")

    def test_the_gradient_runs_light_to_deep(self) -> None:
        """Section 4: light-to-deep and continuous. The order of the stops carries that."""
        for sheet in stylesheets():
            css = sheet.read_text(encoding="utf-8")
            with self.subTest(sheet=sheet.name):
                gradient = token_value(css, "--bt-gradient")
                self.assertIsNotNone(gradient, "--bt-gradient is not defined")
                order = [token for token, _ in BRAND_STOPS]
                found = [t for t in re.findall(r"--bt-(?:sky|mint|green)", gradient)]
                self.assertEqual(order, found, "the stops are not in light-to-deep order")
                for token, percent in zip(order, ("0%", "50%", "100%")):
                    self.assertIn(f"var({token}) {percent}", gradient, f"{token} is not at {percent}")

    def test_no_brand_colour_as_text(self) -> None:
        """Section 5: the deepest stop is 2.62:1 on white. These tokens paint, never write.

        tests/test_theme_token_pairs.py would catch this in styles.css, by a different
        rule and for a different reason; nothing watches landing/showcase.css.
        """
        for sheet in stylesheets():
            css = sheet.read_text(encoding="utf-8")
            with self.subTest(sheet=sheet.name):
                found = re.findall(r"color\s*:\s*var\(\s*(--bt-[a-z-]+)\s*\)", css)
                self.assertEqual([], found, f"brand colours used as text: {found}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
