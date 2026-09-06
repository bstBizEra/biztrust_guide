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
   showcase pages and nowhere else. That test stays where it is, because "no tenant
   mark anywhere under landing/" is a rule SHOWCASE-001 states and that module tests
   SHOWCASE-001. The rule here is the wider one no record had yet written down: no page
   of this site wears a tenant's mark, handbook included.

2. AN ASSET SHIPPED AND NEVER USED. `assets/unitrust-vertical.png` was copied into
   every published artifact by `.github/workflows/pages.yml` and referenced by no page
   on the site. The workflow named its assets by hand in two places and the two lists
   had drifted from each other and from the pages. The workflow now copies what git
   tracks, which removes the drift; this module removes the orphan, by asking of every
   asset which page wants it.

3. NOTHING HELD THE GRADIENT. BizTrust_Brand_Identity_Guide_v1.0 section 8 forbids
   changing the gradient stops and section 5 measures the deepest of them at 2.62:1 on
   white, too low for text. Both rules are invisible to a stylesheet that has only hex
   literals in it, and `styles.css` is minified to 22 lines, where a wrong digit is not
   something a reviewer sees.

WHAT THIS DOES NOT DO. It does not check that a referenced file exists:
`scripts/validate_continuity.py` already resolves every `src` and `href` on every page
and fails on one that resolves to nothing. It does not check contrast, for the reasons
`tests/test_theme_token_pairs.py` sets out at length. It does not read the SVGs' own
contents, so an asset that is the right filename and the wrong artwork passes. It reads
pages and stylesheets only: prose in `docs/` naming an asset that no longer exists is
invisible to it, and `docs/LIVE_PREVIEW.md` held such a line for most of this branch's
life until review found it.

Positive controls, so that no rule below can hold over nothing: pages must be found in
both halves of the site, an asset must be found, and at least two stylesheets must
declare the brand tokens.

The strongest control is not a mutation. Run against this repository at 82892da, the
commit this package branched from, the module reports failures on nineteen pages each
naming a tenant's mark three times, on assets/unitrust-vertical.png referenced by
nothing, and on the gradient tokens absent from both stylesheets. Those first twenty are
real defects that had lived in the tree since the pages were written.

Negative controls (run 2026-09-07 under WP-103, each on a copied tree, each run as
`unittest discover -s tests -p test_brand_marks.py` from that tree's root - the way the
suite runs it). Each fails the test that names it and no other, and the unmutated copy
is green. The four marked * were found by review, after a first version of this module
passed every one of them:
  * A page's favicon points back at assets/unitrust-icon.png  -> test_no_tenant_mark
  * assets/orphan.svg, referenced by nothing                  -> test_every_asset_is_used
  * assets/trust-symbol.svg, whose name is a substring of a * -> test_every_asset_is_used
    referenced asset's name
  * --bt-green changed to #3db38a                             -> test_gradient_stops_are_the_brands
  * --bt-green redefined lower down, in a media query, where * -> test_gradient_stops_are_the_brands
    it is the value that wins at runtime
  * color:var(--bt-green) declared                            -> test_no_brand_colour_as_text
  * color:#3db389 declared, the same colour as a literal     * -> test_no_brand_colour_as_text
  * The stops reversed, all three values correct              -> test_the_gradient_is_the_brands
  * 90deg changed to 270deg, everything else correct         * -> test_the_gradient_is_the_brands

And one false positive it used to raise, now a case in its own right: painting a surface
with `background-color:var(--bt-sky)` is a legitimate use of these tokens and must pass.

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

# Directories that hold no published page. The same set scripts/validate_continuity.py
# skips, for the same reason: _site is a build output and .git holds blobs that are not
# pages. The two lists are kept in step by hand; nothing under tests/ imports that script.
SKIP = {".git", "_site", "node_modules"}

# The signature gradient, from BizTrust_Brand_Identity_Guide_v1.0 section 4. These three
# values are the identity; section 8 lists changing them among the misuses.
BRAND_STOPS = (("--bt-sky", "#a5def3"), ("--bt-mint", "#69c6b5"), ("--bt-green", "#3db389"))

# Section 4 again: "light-to-deep ... continuous rather than radial". The angle carries
# the direction, so the whole declaration is fixed and not only the stops inside it.
BRAND_GRADIENT = "linear-gradient(90deg,var(--bt-sky) 0%,var(--bt-mint) 50%,var(--bt-green) 100%)"

# Tenant A's mark, in any form. The tenant is synthetic and its name appears throughout
# the guide's prose, which is correct; what may not appear is its artwork.
TENANT_MARK = re.compile(r"(?i)assets/[^\"'\s]*unitrust|unitrust[^\"'\s]*\.(?:png|svg|jpe?g|webp|ico)")

# Every reference to a file under assets/, however many levels up the page sits.
ASSET_REFERENCE = re.compile(r"(?:\.\./)*assets/([^\"'\s)>]+)")

# `color:` but not `background-color:`, `border-color:` or `-webkit-text-fill-color:`.
# tests/test_theme_token_pairs.py guards the same boundary for the same reason: without
# it, painting a surface with a brand colour reads as writing text in one.
TEXT_COLOUR = re.compile(r"(?<![-\w])color\s*:\s*([^;}]+)")


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
    """Every stylesheet, found rather than listed: a third one must be guarded too."""
    return sorted(
        sheet
        for sheet in ROOT.rglob("*.css")
        if sheet.is_file() and not SKIP.intersection(sheet.relative_to(ROOT).parts)
    )


def token_values(css: str, token: str) -> list[str]:
    """EVERY definition of a token, not the first.

    A second definition lower down - in a media query, or a theme block - is the value
    that wins at runtime, so a check that reads only the first can be satisfied while
    the colour on the screen is something else.
    """
    return [
        value.strip().lower()
        for value in re.findall(rf"{re.escape(token)}\s*:\s*([^;}}]+)", css)
    ]


def sheets_declaring_brand_tokens() -> list[Path]:
    return [sheet for sheet in stylesheets() if "--bt-" in sheet.read_text(encoding="utf-8")]


class TestNoTenantMark(unittest.TestCase):
    def test_pages_are_found_in_both_halves_of_the_site(self) -> None:
        """Positive control: the rules below hold over nothing if no page is read.

        Counted in two parts because the site is in two parts, and a walk that silently
        lost one of them would still find plenty of pages.
        """
        found = pages()
        handbook = [p for p in found if "landing" not in p.relative_to(ROOT).parts]
        showcase = [p for p in found if "landing" in p.relative_to(ROOT).parts]
        self.assertGreaterEqual(len(handbook), 19, "fewer pages than the handbook has")
        self.assertGreaterEqual(len(showcase), 9, "fewer pages than the showcase has")

    def test_no_tenant_mark(self) -> None:
        for page in pages():
            with self.subTest(page=page.relative_to(ROOT).as_posix()):
                found = TENANT_MARK.findall(page.read_text(encoding="utf-8"))
                self.assertEqual([], found, "a tenant's mark on a BizTrust page")

    def test_no_tenant_mark_in_a_stylesheet(self) -> None:
        for sheet in stylesheets():
            with self.subTest(sheet=sheet.relative_to(ROOT).as_posix()):
                found = TENANT_MARK.findall(sheet.read_text(encoding="utf-8"))
                self.assertEqual([], found, "a tenant's mark in a stylesheet")


class TestAssetsAreUsed(unittest.TestCase):
    def referenced(self) -> set[str]:
        """The basenames actually referenced as assets/<name>, not merely present as text.

        Matching a bare filename anywhere in the corpus would let assets/trust-symbol.svg
        pass on the strength of a reference to assets/biztrust-symbol.svg, because one
        name is a substring of the other.
        """
        names: set[str] = set()
        for path in pages() + stylesheets():
            for target in ASSET_REFERENCE.findall(path.read_text(encoding="utf-8")):
                names.add(target.rsplit("/", 1)[-1])
        return names

    def test_assets_are_found(self) -> None:
        """Positive control: an empty assets/ would make the rule below vacuous."""
        self.assertGreater(len(assets()), 0, "no asset found to check")

    def test_every_asset_is_used(self) -> None:
        """An asset no page names is shipped to every visitor and seen by none."""
        referenced = self.referenced()
        orphans = [
            asset.relative_to(ROOT).as_posix()
            for asset in assets()
            if asset.name not in referenced
        ]
        self.assertEqual([], orphans, f"assets referenced by no page or stylesheet: {orphans}")


class TestSignatureGradient(unittest.TestCase):
    def test_the_tokens_are_declared(self) -> None:
        """Positive control: the rules below say nothing about a stylesheet without them."""
        self.assertGreaterEqual(
            len(sheets_declaring_brand_tokens()), 2,
            "fewer stylesheets declare the brand tokens than the record requires; "
            "landing/README.md section 4 makes showcase.css's root a copy of styles.css's",
        )

    def test_gradient_stops_are_the_brands(self) -> None:
        """Section 8: never change the gradient stops. Every definition, in every sheet."""
        for sheet in sheets_declaring_brand_tokens():
            css = sheet.read_text(encoding="utf-8")
            for token, expected in BRAND_STOPS:
                with self.subTest(sheet=sheet.relative_to(ROOT).as_posix(), token=token):
                    values = token_values(css, token)
                    self.assertNotEqual([], values, f"{token} is not defined")
                    self.assertEqual(
                        [expected] * len(values), values,
                        f"{token} is defined {len(values)} time(s), not always as the brand's value",
                    )

    def test_the_gradient_is_the_brands(self) -> None:
        """Section 4: light-to-deep and continuous. The angle carries that, as the stops do."""
        for sheet in sheets_declaring_brand_tokens():
            css = sheet.read_text(encoding="utf-8")
            with self.subTest(sheet=sheet.relative_to(ROOT).as_posix()):
                values = [re.sub(r"\s+", " ", v) for v in token_values(css, "--bt-gradient")]
                self.assertNotEqual([], values, "--bt-gradient is not defined")
                self.assertEqual([BRAND_GRADIENT] * len(values), values)

    def test_no_brand_colour_as_text(self) -> None:
        """Section 5: the deepest stop is 2.62:1 on white. These colours paint, never write.

        As a token and as a literal both, because writing the hex directly is the way
        past a check that knows only token names - the escape
        tests/test_theme_token_pairs.py declares it cannot see.
        """
        literals = {value for _, value in BRAND_STOPS}
        for sheet in stylesheets():
            css = sheet.read_text(encoding="utf-8")
            with self.subTest(sheet=sheet.relative_to(ROOT).as_posix()):
                found = []
                for declaration in TEXT_COLOUR.findall(css):
                    value = declaration.strip().lower()
                    token = re.fullmatch(r"var\(\s*(--bt-[a-z-]+)\s*\)", value)
                    if token:
                        found.append(token.group(1))
                    elif value in literals:
                        found.append(value)
                self.assertEqual([], found, f"brand colours used as text: {found}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
