#!/usr/bin/env python3
"""tests/showcase_parity.py reads records and pages the one way every showcase parity test relies on.

The eight showcase tests hold copied tables and lists to their records through this module. These
are its unit tests, on small synthetic fixtures, so that a change to a reader is caught here before
it shows up as eight parity failures with no obvious cause. Each test names the behaviour a copy had
drifted on before WP-074: markdown links, separator rows, joiner lines, the "copied" class prefix.

Negative controls (run 2026-09-06 under WP-074, on in-memory copies):
  * Make norm keep markdown link syntax      -> test_norm_reads_a_markdown_link_as_its_text FAILS
  * Let md_rows keep the separator row       -> test_md_rows_skips_header_and_separator FAILS
  * Let fenced_lines keep "+" joiners        -> test_fenced_lines_drops_arrows_and_joiners FAILS
  * Let page_list match any <ol> class       -> test_page_list_requires_the_copied_prefix FAILS

Stdlib only:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

try:
    from showcase_parity import bullets, fenced_lines, headed_table, md_rows, norm, page_list, page_row_count, page_table, section
except ModuleNotFoundError:  # invoked by module name from the repository root rather than by discovery
    from tests.showcase_parity import bullets, fenced_lines, headed_table, md_rows, norm, page_list, page_row_count, page_table, section

RECORD = """# Synthetic record

## 1. Rows

| Epic | Capability | Was |
|---|---|---|
| X1.1 | Party and **client** account | `P1.1` |
| X1.2 | A [linked](https://example.invalid/x) capability | — |

## 2. Headed

| Seat | Records |
|---|---|
| Business authority | Grants |
| SRE | Co-records |

Text after the blank line, with a stray | pipe.

## 3. Fence

```text
Risk
→ Market
↓
+
Bind
```

* first bullet
* second bullet
  * nested bullet is not top level

## 4. End
"""

PAGE = """<table class="epics"><thead><tr><th>Epic</th></tr></thead><tbody>
<tr><td>X1.1</td><td>Party and client account</td><td>P1.1</td></tr>
<tr><td>X1.2</td><td>A <a href="https://example.invalid/x">linked</a> capability</td><td>—</td></tr>
<tr><td>X1.2</td><td>duplicate key</td><td>—</td></tr>
</tbody></table>
<ol class="copied chain"><li>Risk</li><li>Market</li><li>Bind</li></ol>
<ol class="chain"><li>not the copied list</li></ol>
"""


class TestNorm(unittest.TestCase):
    def test_norm_reads_a_markdown_link_as_its_text(self) -> None:
        self.assertEqual("a linked capability", norm("A [linked](https://example.invalid/x) capability"))

    def test_norm_drops_tags_backticks_bold_and_case(self) -> None:
        self.assertEqual("party and client account p1.1", norm("Party  and <b>**client**</b>\naccount `P1.1`"))
        self.assertEqual("a & b", norm("A &amp; B"))


class TestRecordReaders(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.record = Path(self.tmp.name) / "record.md"
        self.record.write_text(RECORD, encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_section_is_between_markers(self) -> None:
        self.assertIn("| X1.1 |", section(self.record, "\n## 1. Rows", "\n## 2. "))
        self.assertNotIn("Headed", section(self.record, "\n## 1. Rows", "\n## 2. "))

    def test_md_rows_skips_header_and_separator(self) -> None:
        # a permissive first-cell pattern: the header is excluded by the pattern, the |---| row only by the second-cell guard
        rows = md_rows(section(self.record, "\n## 1. Rows", "\n## 2. "), r"(?!Epic$).+")
        self.assertEqual({"x1.1": ("party and client account", "p1.1"), "x1.2": ("a linked capability", "—")}, rows)

    def test_md_rows_first_cell_pattern_selects_rows(self) -> None:
        self.assertEqual(["x1.2"], list(md_rows(section(self.record, "\n## 1. Rows", "\n## 2. "), r"X1\.2")))

    def test_headed_table_reads_to_the_blank_line(self) -> None:
        rows = headed_table(section(self.record, "\n## 2. Headed", "\n## 3. "), "| Seat | Records |")
        self.assertEqual({"business authority": ("grants",), "sre": ("co-records",)}, rows)

    def test_fenced_lines_drops_arrows_and_joiners(self) -> None:
        self.assertEqual(["risk", "market", "bind"], fenced_lines(section(self.record, "\n## 3. Fence", "\n## 4. ")))

    def test_bullets_are_top_level_only(self) -> None:
        self.assertEqual(["first bullet", "second bullet"], bullets(section(self.record, "\n## 3. Fence", "\n## 4. ")))


class TestPageReaders(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.page = Path(self.tmp.name) / "page.html"
        self.page.write_text(PAGE, encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_page_table_keys_rows_by_first_cell(self) -> None:
        self.assertEqual({"x1.1": ("party and client account", "p1.1"), "x1.2": ("duplicate key", "—")}, page_table(self.page, "epics"))

    def test_page_row_count_sees_the_duplicate_a_keyed_table_hides(self) -> None:
        self.assertEqual(3, page_row_count(self.page, "epics"))
        self.assertEqual(2, len(page_table(self.page, "epics")))

    def test_page_list_requires_the_copied_prefix(self) -> None:
        self.assertEqual(["risk", "market", "bind"], page_list(self.page, "chain"))

    def test_missing_table_is_a_defect(self) -> None:
        with self.assertRaises(AssertionError):
            page_table(self.page, "absent")


if __name__ == "__main__":
    unittest.main()
