"""A token used as text must have a dark-theme counterpart, or an entry saying why not.

Five instances of one defect class were found one at a time, each by a person
looking: the `.github-link` chip at 1.03:1 on the dark topbar, `--teal-dark` text at
3.19:1, the hero CTA at 2.95:1, thirteen `--navy` panels at 1.03:1, and `--red` at
3.81:1 on white. A person looking is not a control.

THE MECHANISM. `body.dark` redefines the surface tokens (`--paper`, `--surface`,
`--line`) and the text tokens (`--ink`, `--muted`). Any OTHER token used as `color:`
keeps its `:root` value while the ground moves out from under it. That is the whole
class, and it is structural: it does not depend on any particular contrast ratio.

WHY THIS TESTS THE STRUCTURE AND NOT THE RATIO. A contrast-measuring version of this
test was built first and discarded, because measuring the consequence requires
knowing which surface each element sits on, and that needs the cascade. Approximating
it by walking selector ancestors produced 39 findings of which 5 were real - `--line`
is a border token being read as a background, `.hero`'s ground does not resolve
through a `var()`, and `<i>`/`:before` markers are not text under WCAG 1.4.3 at all.
A check with 13% precision gets switched off within a week, so it is not shipped.

The narrower exact alternative - compare only a `color:` and `background:` declared in
the same rule - was also measured: three rules in the whole stylesheet do that. It
would watch almost nothing.

So this test asserts the invariant instead of estimating its effect. It would have
caught `--teal-dark` and `--red`. It fires on any new token used as text without a
dark counterpart, which is the shape all five instances shared.

SCOPE. Only `color:var(--token)` is seen. A hardcoded literal is invisible: the hero
CTA inherited `#fff` onto `var(--teal)` at 2.95:1, and no token-based check can see
that. It was caught by review, and it stays a review responsibility.
"""

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CSS = ROOT / "styles.css"

# Tokens used as text that deliberately have no dark counterpart, with the reason.
# An entry here is a claim that the token's text never lands on a themed surface.
# Adding one is a design decision; leaving one undocumented is the defect this
# module exists to catch.
FIXED_SURFACE_TEXT = {
    "--teal": "hero and section headings sit on the fixed navy hero ground, which "
              "body.dark does not repaint",
    "--lime": "eyebrow and state-card labels sit on var(--navy) panels, fixed in "
              "both themes",
    "--amber": "wp-state labels sit on the fixed navy work-package banner",
}

# Redefining the surface under text is what moves the ground; these are the tokens
# whose change makes an un-redefined foreground unsafe.
THEMED_SURFACES = {"--paper", "--surface", "--line"}

HEX = re.compile(r"#[0-9a-fA-F]{3,8}\Z")


def token_block(css: str, selector: str) -> dict:
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    if not match:
        return {}
    return {
        name: value.strip()
        for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;}]+)", match.group(1))
    }


class ThemeTokens(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.css = CSS.read_text(encoding="utf-8")
        cls.light = {k: v for k, v in token_block(cls.css, ":root").items() if HEX.match(v)}
        cls.dark = {k: v for k, v in token_block(cls.css, "body.dark").items() if HEX.match(v)}
        cls.as_text = set(re.findall(r"(?<!-)color\s*:\s*var\(\s*(--[\w-]+)\s*\)", cls.css))


class TestControlsCanFire(ThemeTokens):
    """A refactor that returns empty dicts would make every check below vacuous."""

    def test_parsers_are_alive(self) -> None:
        self.assertGreaterEqual(len(self.light), 8, ":root palette looks unparsed")
        self.assertGreaterEqual(len(self.dark), 4, "body.dark looks unparsed")
        self.assertGreaterEqual(len(self.as_text), 5, "no color:var() parsed at all")

    def test_the_theme_actually_repaints_its_surfaces(self) -> None:
        """The premise. If body.dark stopped moving the ground, the class evaporates
        and this whole module should be deleted rather than left passing."""
        moved = THEMED_SURFACES & self.dark.keys()
        self.assertEqual(
            THEMED_SURFACES, moved,
            "body.dark no longer redefines every themed surface; re-derive this test",
        )

    def test_a_known_instance_is_recognised(self) -> None:
        """--teal-dark is the instance this module was written from. It must be
        seen as text, and it must be one of the tokens body.dark now repaints."""
        self.assertIn("--teal-dark", self.as_text)
        self.assertIn("--teal-dark", self.dark, "the --teal-dark fix was reverted")


class TestEveryTextTokenIsThemedOrDeclared(ThemeTokens):
    def test_no_undocumented_unthemed_text_token(self) -> None:
        undocumented = sorted(
            t for t in self.as_text
            if t not in self.dark and t in self.light and t not in FIXED_SURFACE_TEXT
        )
        self.assertEqual(
            [], undocumented,
            "used as color: but body.dark does not redefine them, and no entry in "
            "FIXED_SURFACE_TEXT explains why:\n  "
            + "\n  ".join(f"{t} = {self.light[t]}" for t in undocumented)
            + "\n\nEither add a body.dark value, or add an entry naming the fixed "
              "surface its text sits on.",
        )

    def test_the_allowlist_has_no_dead_entries(self) -> None:
        """An entry for a token no longer used as text is stale documentation
        asserting a constraint nothing tests."""
        dead = sorted(t for t in FIXED_SURFACE_TEXT if t not in self.as_text)
        self.assertEqual([], dead, f"FIXED_SURFACE_TEXT entries no longer used as text: {dead}")

    def test_the_allowlist_gives_a_reason(self) -> None:
        for token, reason in FIXED_SURFACE_TEXT.items():
            self.assertGreater(
                len(reason), 25,
                f"{token}'s allowlist entry does not name the surface it relies on",
            )


if __name__ == "__main__":
    unittest.main()
