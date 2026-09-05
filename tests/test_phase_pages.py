#!/usr/bin/env python3
"""The phase track is a rendering of DELIVERY_PLAN.md, and must stay one.

`phases/` renders the P0-P3 delivery plan for the published site. The plan is the
source; the pages are a second rendering. The risk that shape carries is the one
issue #32 measured: a rendering that nothing checks against its source drifts, and
drifts silently, because the page keeps looking finished. This module is the check.

WHAT IS EXACT HERE
==================

Epic identifiers (`P0.1`, `P1.13`, ...) are a closed vocabulary that the plan
defines in four tables (one plan section per phase; see EPIC_SOURCES) and the pages must
reproduce one-to-one, and each id's
LABEL - the plan's deliverable or capability text - must sit beside it in the
epics table. That makes the parity check mechanically decidable with no
threshold and no calibration data - the property the spine test's docstring
says a check needs before it is worth keeping. The same is true of the eight
capability gate identifiers in PLAN-001 §10.

The first version of this module checked identifier SETS only. A fresh-context
review showed it passed with the entire epics table deleted (the ids survive in
the execution-order list), with two row labels swapped, and with a gate present
only in the page <title>. Each of those is now a failure, below.

Two things are deliberately NOT checked, and why:

  * Whether a page states a current status. That is a review responsibility; a
    lexical detector for "status-shaped sentences" would have the 13% precision
    the theme test's docstring describes and would be switched off within a week.
  * Cross-page similarity against `stages/`. The duplication detector's corpus
    is `stages/` only and its element-level headroom is 0.008; widening it here
    without re-calibrating would fire on legitimate content or on nothing. The
    measurement is run by hand and reported in the pull request instead.

NEGATIVE CONTROLS, run by hand before this shipped
================================================

  * Remove EVERY `P0.7` from p0.html            -> test_epic_ids_match_the_plan FAILS
    (deleting only the table row failed set-parity's first version silently -
    the id survived in the execution-order list. It now fails the LABEL check.)
  * Delete the whole epics <section> on p0.html  -> test_every_phase_page_has_its_spine FAILS
  * Swap the P0.7 and P0.11 labels               -> test_epic_labels_match_the_plan FAILS
  * Leave BT-G5 only in overview's <title>       -> test_overview_carries_every_gate FAILS
  * Remove BT-G7 from overview.html              -> test_overview_carries_every_gate FAILS (run 2026-09-06 under WP-051)
  * Add a `P1.14` that the plan does not have    -> test_epic_ids_match_the_plan FAILS
  * Put `P2.4` on p3.html                        -> test_epic_ids_match_the_plan FAILS
  * Remove BT-G5 from overview.html              -> test_overview_carries_every_gate FAILS
  * Rename the "Halt" eyebrow on p1.html         -> test_every_phase_page_has_its_spine FAILS

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHASES = ROOT / "phases"
PLAN = ROOT / "docs/architecture/DELIVERY_PLAN.md"
# Epics still come from the previous plan, which the phase pages render row by row
# until each page moves (Guide v2 map, issue #153). Gates come from PLAN-001 section 10,
# the record since WP-049; the overview renders that table, so it is held to it.
GATE_PLAN = ROOT / "docs/architecture/BIZTRUST-PLAN-001.md"
# Each phase page renders one section of one plan. P0 moved to PLAN-001 section 4 under
# WP-052 (its thirteen rows are identical in both plans); P1 to P3 still render the previous
# plan's sections 4 to 6 and move one ticket at a time. A manual ticket moves the page, this
# row, and the page's exit-gate expectation together.
EPIC_SOURCES: dict[int, tuple[Path, str, str]] = {
    0: (GATE_PLAN, "\n## 4. P0", "\n## 5. P1"),
    1: (PLAN, "\n## 4. P1", "\n## 5. P2"),
    2: (PLAN, "\n## 5. P2", "\n## 6. P3"),
    3: (PLAN, "\n## 6. P3", "\n## 7. "),
}

PHASE_PAGES = {0: "p0.html", 1: "p1.html", 2: "p2.html", 3: "p3.html"}
OVERVIEW = "overview.html"

EPIC = re.compile(r"\bP([0-3])\.(\d{1,2})\b")
GATE = re.compile(r"\bBT-G[0-7]\b")

# Eyebrow text (the small <p> above the <h2>) that locates each spine element.
# Keyed on the eyebrow, not the id, for the reason test_stage_page_spine records.
SPINE: tuple[tuple[str, str], ...] = (
    ("preconditions", "entry criteria"),
    ("epic to work package", "epics table"),
    ("execution order", "execution order"),
    ("what the human monitors", "monitoring section"),
    ("transition", "exit gate"),
    ("halt", "stop conditions"),
)
MIN_ITEMS = 2

_SECTION = re.compile(r"<section\b([^>]*)>(.*?)</section>", re.S)
_HEADING = re.compile(
    r'<div class="section-heading">.*?<div>\s*<p>(.*?)</p>\s*<h2>(.*?)</h2>', re.S
)
_SHAPES = (
    re.compile(r"<label>\s*<input type=\"checkbox\""),
    re.compile(r"<article\b"),
    re.compile(r"<div><span>"),
    re.compile(r"<tr\b"),
    re.compile(r"<li\b"),
)


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment)).strip()


def _phase_section(phase: int) -> str:
    """The plan section that holds this phase's epics table, and nothing outside it."""
    path, start, end = EPIC_SOURCES[phase]
    text = path.read_text(encoding="utf-8")
    return text.split(start, 1)[1].split(end, 1)[0]


def plan_epics() -> dict[int, set[str]]:
    """Epic ids per phase, read from that phase's plan section: `| P0.7 | ... |`.
    A row is counted only inside its own section, so PLAN-001's mapping table
    (section 9, which repeats every old id) can never feed a phase."""
    found: dict[int, set[str]] = {n: set() for n in PHASE_PAGES}
    for phase in PHASE_PAGES:
        for line in _phase_section(phase).splitlines():
            m = re.match(r"^\|\s*(P([0-3])\.\d{1,2})\s*\|", line)
            if m and int(m.group(2)) == phase:
                found[phase].add(m.group(1))
    return found


def plan_gates() -> set[str]:
    """Gate ids from PLAN-001 §10, the table whose rows start with a backticked gate."""
    text = GATE_PLAN.read_text(encoding="utf-8")
    section = text.split("## 10. Gates", 1)[1].split("\n## 11.", 1)[0]
    return {m for line in section.splitlines() if line.startswith("| `BT-G") for m in GATE.findall(line)}


def page_body(name: str) -> str:
    """<main> only. The <title> and meta description also name gates and epics;
    a gate surviving only there is exactly the false pass this must not give."""
    html = (PHASES / name).read_text(encoding="utf-8")
    m = re.search(r"<main\b[^>]*>(.*?)</main>", html, re.S)
    return m.group(1) if m else ""


def page_text(name: str) -> str:
    return _text(page_body(name))


def _norm(label: str) -> str:
    return re.sub(r"\s+", " ", label.replace("`", "")).strip().lower()


def plan_labels() -> dict[str, str]:
    """Epic id -> the plan's deliverable/capability cell, from the same four sections."""
    out: dict[str, str] = {}
    for phase in PHASE_PAGES:
        for line in _phase_section(phase).splitlines():
            m = re.match(r"^\|\s*(P([0-3])\.\d{1,2})\s*\|\s*(.*?)\s*\|", line)
            if m and int(m.group(2)) == phase:
                out[m.group(1)] = _norm(m.group(3))
    return out


def page_labels(name: str) -> dict[str, str]:
    """Epic id -> the <small> label beside it in the page's epics table rows."""
    out: dict[str, str] = {}
    for sec in sections(name):
        if sec["eyebrow"] != "epic to work package":
            continue
        for m in re.finditer(r"<strong>(P[0-3]\.\d{1,2})</strong>\s*<small>(.*?)</small>", sec["body"], re.S):
            out[m.group(1)] = _norm(_text(m.group(2)))
    return out


def page_epics(name: str) -> dict[int, set[str]]:
    found: dict[int, set[str]] = {n: set() for n in PHASE_PAGES}
    for phase, minor in EPIC.findall(page_text(name)):
        found[int(phase)].add(f"P{phase}.{minor}")
    return found


def sections(name: str) -> list[dict]:
    html = (PHASES / name).read_text(encoding="utf-8")
    out = []
    for m in _SECTION.finditer(html):
        heading = _HEADING.search(m.group(2))
        out.append({
            "id": (re.search(r'id="([^"]*)"', m.group(1)) or [None, ""])[1],
            "eyebrow": _text(heading.group(1)).lower() if heading else "",
            "body": m.group(2),
        })
    return out


def item_count(body: str) -> int:
    return max(len(shape.findall(body)) for shape in _SHAPES)


class TestCorpusIsPresent(unittest.TestCase):
    """Positive controls. Without these every assertion below can pass over nothing."""

    def test_plan_yields_epics_for_every_phase(self) -> None:
        epics = plan_epics()
        for phase, ids in epics.items():
            with self.subTest(phase=phase):
                self.assertGreaterEqual(
                    len(ids), 8,
                    f"plan parser found only {sorted(ids)} for P{phase}; the table "
                    f"shape changed or the parser is wrong - fix that before the pages",
                )

    def test_plan_yields_eight_gates(self) -> None:
        self.assertEqual(
            {f"BT-G{n}" for n in range(8)}, plan_gates(),
            "PLAN-001 §10 no longer lists exactly BT-G0..BT-G7; re-derive this test",
        )

    def test_every_page_exists_and_parses(self) -> None:
        for name in list(PHASE_PAGES.values()) + [OVERVIEW]:
            with self.subTest(page=name):
                self.assertTrue((PHASES / name).is_file(), f"phases/{name} is missing")
                self.assertGreaterEqual(len(sections(name)), 3, f"{name}: too few sections parsed")


class TestParityWithThePlan(unittest.TestCase):
    def test_epic_ids_match_the_plan(self) -> None:
        """Each phase page carries exactly its phase's epics, and none of another's."""
        plan = plan_epics()
        problems = []
        for phase, name in PHASE_PAGES.items():
            on_page = page_epics(name)
            missing = plan[phase] - on_page[phase]
            invented = on_page[phase] - plan[phase]
            foreign = {e for p, ids in on_page.items() if p != phase for e in ids}
            if missing:
                problems.append(f"  {name} lacks {sorted(missing)} - the plan has them")
            if invented:
                problems.append(f"  {name} names {sorted(invented)} - the plan does not")
            if foreign:
                problems.append(f"  {name} names another phase's epics {sorted(foreign)}")
        self.assertEqual([], problems, "phase pages disagree with DELIVERY_PLAN.md:\n" + "\n".join(problems))

    def test_overview_names_no_epic(self) -> None:
        """The overview is the map. An epic id on it is a second place to keep in step."""
        found = {e for ids in page_epics(OVERVIEW).values() for e in ids}
        self.assertEqual(set(), found, f"overview.html names epics {sorted(found)}; link the phase page instead")

    def test_overview_carries_every_gate(self) -> None:
        on_page = set(GATE.findall(page_text(OVERVIEW)))
        self.assertEqual(plan_gates(), on_page, "overview.html and PLAN-001 §10 disagree on the gate set")

    def test_each_phase_page_names_its_exit_gate(self) -> None:
        expected = {"p0.html": {"BT-G1"}, "p1.html": {"BT-G2"}, "p2.html": {"BT-G3"},
                    "p3.html": {"BT-G4", "BT-G5", "BT-G6"}}
        for name, gates in expected.items():
            with self.subTest(page=name):
                gate_sections = [s for s in sections(name) if s["eyebrow"] == "transition"]
                self.assertEqual(1, len(gate_sections), f"{name}: expected one exit-gate section")
                present = set(GATE.findall(_text(gate_sections[0]["body"])))
                self.assertEqual(gates, present, f"{name}: exit gate names {sorted(present)}, expected exactly {sorted(gates)}")

    def test_epic_labels_match_the_plan(self) -> None:
        """Every plan epic has a row in the page's epics table whose label is the plan's text.

        Set-parity alone let a page keep its ids in prose after the table was gone,
        and let two rows trade labels. This binds the id to the deliverable beside it.
        """
        plan = plan_labels()
        problems = []
        for phase, name in PHASE_PAGES.items():
            rows = page_labels(name)
            for epic in sorted(plan_epics()[phase], key=lambda e: int(e.split(".")[1])):
                if epic not in rows:
                    problems.append(f"  {name}: no epics-table row for {epic}")
                elif rows[epic] != plan[epic]:
                    problems.append(f"  {name}: {epic} label {rows[epic]!r} != plan {plan[epic]!r}")
            for epic in rows:
                if epic not in plan:
                    problems.append(f"  {name}: epics-table row {epic} is not in the plan")
        self.assertEqual([], problems, "epic labels disagree with DELIVERY_PLAN.md:\n" + "\n".join(problems))


class TestSpine(unittest.TestCase):
    def test_every_phase_page_has_its_spine(self) -> None:
        missing = []
        for name in PHASE_PAGES.values():
            secs = sections(name)
            for eyebrow, human in SPINE:
                hits = [s for s in secs if s["eyebrow"] == eyebrow]
                if len(hits) != 1:
                    missing.append(f"  {name}: {len(hits)} section(s) with eyebrow {eyebrow!r} ({human}); expected exactly 1")
                    continue
                n = item_count(hits[0]["body"])
                if n < MIN_ITEMS:
                    missing.append(f"  {name} #{hits[0]['id']} ({human}): {n} item(s), below {MIN_ITEMS}")
        self.assertEqual([], missing, "phase spine defects:\n" + "\n".join(missing))

    def test_exit_gate_items_are_checkboxes(self) -> None:
        for name in PHASE_PAGES.values():
            with self.subTest(page=name):
                gate = next(s for s in sections(name) if s["eyebrow"] == "transition")
                boxes = _SHAPES[0].findall(gate["body"])
                self.assertGreaterEqual(len(boxes), MIN_ITEMS, f"{name}: gate must be ticked conditions, not prose")

    def test_pages_link_the_track_and_the_hub(self) -> None:
        for name in PHASE_PAGES.values():
            html = (PHASES / name).read_text(encoding="utf-8")
            with self.subTest(page=name):
                self.assertIn('href="overview.html"', html, f"{name} does not link the phase track")
                self.assertIn('href="../index.html"', html, f"{name} does not link the hub")
        self.assertIn('href="../index.html"', (PHASES / OVERVIEW).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
