"""One seam for the showcase parity tests: a record's tables and lists, and a page's, read the same way everywhere.

Every page under landing/ copies tables and lists from a record (PLAN-001, ARCH-001, FLOWS.md, the
roadmap) and a test holds the copy to the record cell for cell. Until WP-074 each of those tests
carried its own copy of the readers below, and the copies had drifted: one stripped markdown links,
two dropped arrow-only fence lines, one dropped "+" joiners, and one kept every fence line. This module is the one reader; a test
imports what it needs and keeps only the record-specific functions that say where its tables are.

Two sides, one normalisation:

  * the record side reads Markdown: a section between two markers, a table's rows keyed by first
    cell, a table located by its header row, a ```text fence's lines, a section's bullets;
  * the page side reads HTML: a table's tbody by class, its rows keyed by first cell, its row count,
    and a copied list (<ol class="copied <name>">) by name.

Normalisation is the same on both sides: tags dropped, a markdown link reduced to its text (as the
page's <a> is), entities unescaped, backticks and bold markers removed, whitespace collapsed, case
folded. A test that needs a different reading writes it beside its record functions, not here.

Stdlib only.
"""

from __future__ import annotations

import html as html_mod
import re
from collections.abc import Iterator
from pathlib import Path

JOINERS = ("↓", "↕", "│", "▼", "+", "=")


def norm(fragment: str) -> str:
    """Tags out, markdown links to their text, entities unescaped, backticks and bold out, whitespace one space, lower case.

    A TAG BECOMES NOTHING, NOT A SPACE, and that is decided rather than assumed. Four modules
    carried a private copy of this function and one of them replaced a tag with " " instead
    (WP-110, #341). The suite settles which is right: make that module drop tags and everything
    passes; make the other three space them and test_work_package_loop_page fails, because the
    page writes a citation as "(<a>Discover 03</a>)" and the record it is compared against writes
    "(Discover 03)". Spacing gives "( discover 03 )" on one side only. So dropping is required by
    a live case and spacing is required by nothing.
    """
    s = re.sub(r"<[^>]+>", "", fragment)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = html_mod.unescape(s).replace("`", "").replace("**", "")
    return re.sub(r"\s+", " ", s).strip().lower()


def norm_markup(fragment: str) -> str:
    """Markup out, and Markdown emphasis left ALONE. The strict sibling of norm().

    norm() also resolves `[text](url)` to its text and strips `**`, which it must: dropping
    either fails test_epics_match_the_plan and norm()'s own self-tests, because the records those
    readers compare do use Markdown emphasis and links.

    The four modules that compare a record's cell to a page's cell do NOT want that leniency, and
    WP-110 first gave it to them by mistake. Review measured the cost: eight record-side
    mutations - a cell gaining `**bold**`, or becoming `[text](url)` where the page says something
    else - were caught before and passed after. Those are real copy divergences, and under norm()
    the link's TARGET becomes invisible to the comparison entirely. It bought nothing: no cell in
    any region those four compare contains a link or a bold marker.

    So the difference is not a preference and not a parameter. norm() tolerates Markdown because
    its records carry it; norm_markup() refuses to, because a record that emphasises or links text
    the page does not is exactly the divergence its callers exist to catch.
    """
    s = re.sub(r"<[^>]+>", "", fragment)
    s = html_mod.unescape(s).replace("`", "")
    return re.sub(r"\s+", " ", s).strip().lower()


def section(path: Path, start: str, end: str) -> str:
    """The text of `path` between the first `start` and the next `end`; raises if either is missing."""
    return path.read_text(encoding="utf-8").split(start, 1)[1].split(end, 1)[0]


def md_matching_rows(section_text: str, first_cell_pattern: str) -> Iterator[list[str]]:
    """Each row of any table in the section whose first cell fully matches the pattern, cell by cell.

    The header row is excluded by the pattern; the |---| separator row is excluded by its second cell.
    """
    for line in section_text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and re.fullmatch(first_cell_pattern, cells[0]) and not re.fullmatch(r"-+", cells[1]):
            yield cells


def md_rows(section_text: str, first_cell_pattern: str) -> dict[str, tuple[str, ...]]:
    """Those rows keyed by first cell -> {first: (rest...)}. Two rows with one first cell keep the later."""
    return {norm(cells[0]): tuple(norm(c) for c in cells[1:])
            for cells in md_matching_rows(section_text, first_cell_pattern)}


def md_row_count(section_text: str, first_cell_pattern: str) -> int:
    """How many such rows there are, duplicates included; what a keyed comparison cannot see.

    The record-side counterpart of `page_row_count`.
    """
    return sum(1 for _ in md_matching_rows(section_text, first_cell_pattern))


def headed_table(section_text: str, header: str) -> dict[str, tuple[str, ...]]:
    """The rows of the table headed exactly `header`, read to the next blank line -> {first: (rest...)}."""
    assert header in section_text, f"no table headed {header!r} in the section"
    body = section_text.split(header, 1)[1].split("\n\n", 1)[0]
    out: dict[str, tuple[str, ...]] = {}
    for line in body.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and not re.fullmatch(r"-+", cells[0]):
            out[norm(cells[0])] = tuple(norm(c) for c in cells[1:])
    return out


def fenced_lines(section_text: str, joiners: tuple[str, ...] = JOINERS) -> list[str]:
    """The lines of the first ```text fence in the section: a leading arrow stripped, joiner-only lines dropped."""
    fence = section_text.split("```text", 1)[1].split("```", 1)[0]
    lines = [line.strip().lstrip("→ ").strip() for line in fence.splitlines()]
    return [norm(line) for line in lines if line and line not in joiners]


def bullets(section_text: str) -> list[str]:
    """The section's top-level '* ' bullets, normalised, in order."""
    return [norm(line[2:]) for line in section_text.splitlines() if line.startswith("* ")]


def page_tbody(page: Path, table_class: str) -> str:
    """The inner HTML of the <tbody> of the page's <table class="..."> ; raises if the table is absent."""
    m = re.search(rf'<table class="{table_class}">.*?<tbody>(.*?)</tbody>', page.read_text(encoding="utf-8"), re.S)
    assert m, f"no table of class {table_class} on the page"
    return m.group(1)


def page_table(page: Path, table_class: str) -> dict[str, tuple[str, ...]]:
    """The page table's rows keyed by first cell -> {first: (rest...)}; a row with no cells is a defect."""
    out: dict[str, tuple[str, ...]] = {}
    for row in re.finditer(r"<tr>(.*?)</tr>", page_tbody(page, table_class), re.S):
        cells = [norm(c) for c in re.findall(r"<td>(.*?)</td>", row.group(1), re.S)]
        assert cells, f"a row of the {table_class} table has no cells"
        out[cells[0]] = tuple(cells[1:])
    return out


def page_row_count(page: Path, table_class: str) -> int:
    """How many <tr> the page table's tbody holds, duplicates included; what a keyed comparison cannot see."""
    return len(re.findall(r"<tr>", page_tbody(page, table_class)))


def page_list(page: Path, list_class: str) -> list[str]:
    """The items of the page's <ol class="copied <list_class>">, normalised, in order."""
    m = re.search(rf'<ol class="copied {list_class}">(.*?)</ol>', page.read_text(encoding="utf-8"), re.S)
    assert m, f"no list of class copied {list_class} on the page"
    return [norm(item) for item in re.findall(r"<li>(.*?)</li>", m.group(1), re.S)]
