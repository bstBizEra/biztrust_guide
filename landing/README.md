# The showcase: rules for the pages under `landing/`

**Record:** SHOWCASE-001 · `0.1-draft` · decided under WP-064 for ticket [#172](https://github.com/bstBizEra/biztrust_guide/issues/172) on the Guide v2 map ([#153](https://github.com/bstBizEra/biztrust_guide/issues/153)), charting decision 6, and the operator's adoption of the one-record route (comment of 2026-09-06 on #153, transcribed).
**Status:** `PROPOSED` · a draft; nothing here is accepted, and the operator may reverse any rule by a comment on #172 or #153. The operator's adoption comment named `docs/` as the record's home and the ticket named this file; the record lives beside the pages it governs.
**What it governs:** every page under `landing/`. A page that breaks a rule here is a defect; `tests/test_showcase_pages.py` fails on the structural rules.
**What it is not:** a source of truth. Every showcase page projects a record in this repository and says which one; when the record changes, the page is revised to match.

## 1. The pages

Nine pages, one entry and eight projections, in the order the shared navigation shows them. The order is the delivery plan's: what BizTrust is, the roadmap, the architecture, the four phases, what follows, who delivers.

| Navigation label | File | Projects | Ticket |
|---|---|---|---|
| Overview | `index.html` | The architecture contract's positioning, the P0 design brief; the entry page, shipped under WP-047 | #131, #132 |
| Roadmap | `roadmap.html` | PLAN-001 sections 2, 8, 10 and 11 (the streams' entry conditions, which the operations page also projects) | #173 |
| Architecture | `architecture.html` | ARCH-001 sections 1 and 6, the contract family, the invariants, Gate A | #174 |
| P0 Identity and Tenant | `p0.html` | PLAN-001 section 4 and the P0 manual | #175 |
| P1 Insurance | `p1.html` | PLAN-001 section 5 and the P1 manual | #176 |
| P2 Payment and Finance | `p2.html` | PLAN-001 section 6 and the P2 manual | #177 |
| P3 Production | `p3.html` | PLAN-001 section 7 and the P3 manual | #178 |
| Continuous Operations and expansion | `operations.html` | PLAN-001 sections 8 and 11 and the Continuous Operations reference page | #179 |
| Team and doctrine | `team.html` | PLAN-001 sections 12.1, 13 and 13.1; the doctrine sentence once #158 lands | #180 |

A page that has not landed appears in every page's navigation as its label without a link, so the reader sees the whole shape and cannot click into nothing. The Work Package that lands a page replaces that label with a link on every page.

## 2. The shell every page shares

In this order, top to bottom:

1. **The status strip**, above everything, sticky. Its three lines are the overview's on every page, "Architecture design stage", "Contract freeze pending", "Implementation not yet authorised", hand-maintained from `badf/current-state.json`; a record changing them changes this record. It links to the page's "what this means" section where one exists or to the overview's. It is the evidence boundary: nothing above it is a claim, and nothing below it may claim more than it does.
2. **The mast**: the wordmark "BizTrust by BizEra" linking to the page's main content, and the link to the engineering handbook. No tenant mark anywhere under `landing/`; the handbook's header and footer carry UniTrust marks, which is why the showcase shares no chrome with it.
3. **The navigation**: the nine labels of section 1 in that order, the current page marked, unlanded pages unlinked.
4. **The record line**, on every page but the overview, directly under the page's heading: which record and sections the page projects, and the commit and date it was read at. The form is fixed: `Projects <record> <version>, sections <n>; read at <short commit>, <date>.`, where the commit is the seven-character `main` commit at which the projected record was read, not the page's own, and the date is ISO. The overview carries the same facts in its footer.
5. **The body**: sections of class `block`, each with a heading a reader would use to find it and each ending in a source line. The engage block that ends a page carries none, because it says what the reader can do rather than what a record says.
6. **The footer**: the projection sentence ("This page is a projection of the governed architecture in bstBizEra/biztrust_guide. The handbook and its machine-readable records are authoritative; when they change, this page is revised to match."), the repository link and the handbook link.

## 3. The rules for what a page says

- **Design voice.** Everything is what BizTrust is designed to become, is designed to do, or would do. A sentence that says the platform does, has, or is production-anything is a defect, whatever the tense of the record it cites. No page states a gate as passed, a capability as existing, or a decision as accepted; those words belong to the records and the humans who hold the seats.
- **Every section carries a source line**, visible, last, in the form `Source: <record>, <section or passage>.` A source line cites a passage that exists and says what the section says; a reviewer reads the passage. A section with nothing to cite is not written.
- **The five tenant questions** stay on the overview, as WP-047 decided; a phase page may point at them but does not restate them.
- **Numbers are the record's.** A count, a date, a version on a page is copied from the record it cites, never computed on the page.
- **Names are the records'.** Phases, gates, labels, epics and streams are named as PLAN-001 names them: a gate identifier never appears without its executive label, A to E, the first time, and nothing after P3 carries a phase number. Tenant names are used as on the maps and remain withdrawable.
- **Nothing is generated.** Every page is hand-written, revised when its record changes, and says so in the footer.

## 4. The visual system

The showcase's tokens are the handbook's, by DEC-049: the projection reads as the same house. They live once, in `landing/showcase.css`, which every showcase page links; the tokens in that file are a copy of the handbook's `styles.css` root, and a change there is mirrored by hand (recorded as non-coverage on every showcase package until a test compares them).

- **Colour**: navy `#071a2c` for the strip, the hero and the gate slabs; teal `#10a8a0` for links and focus; amber `#f1b84b` for the strip's rule and markers and the current page in the navigation; lime `#bfdc6a` for the strip's second state and the left rule of the definition and principle blocks; red `#c92f2f` for the strip's third state; paper `#f5f8f9` and white surfaces; the dark scheme swaps ink and paper as the handbook does.
- **Type**: Inter alone, at the stylesheet's scale: the overview's hero heading at `clamp(2.4rem, 6vw, 4.6rem)` with tight letter-spacing, section headings at `clamp(1.5rem, 3vw, 2.2rem)`, body at 1rem on a 1.6 line height, source lines at 0.74rem in the muted colour. No monospace labels, no capitals as labels, no eyebrow labels above headings.
- **Layout**: one left-aligned column, 72rem at most; blocks separated by a hairline rule, the block's bottom border; the ledger's two bordered panels are the one card-like element, and they stay the overview's. The overview keeps its hero as the entry's one big moment; the eight projections open with the record line under a plain heading, not a hero.
- **Components**, all in `showcase.css`, none invented per page: the strip; the mast; the navigation; the record line; the block with its source line; the table, one rule for every table a projection renders; the copied list (class `copied`), one rule for a numbered list copied from a record; the ledger of what is decided and what remains open, as the overview renders it; the gate slab that closes each phase page, the gate identifier large in the navy block with its label beside it; the engage block that ends a page with what the reader can do. The navigation, the record line, the table rule, the copied-list rule and the gate slab are this record's additions to the overview's stylesheet; nothing added restyles an element the overview uses.
- **The one bold thing** is the strip. Nothing else moves, glows or fades; no motion that a reader did not cause.

## 5. How a page is built

One Work Package per page, against this record. The package prototypes the page on its `prototype/<name>` branch as its ticket says, ships it under `landing/`, replaces the page's label with a link in every showcase page's navigation, updates the record line's commit and date on that page, and adds nothing to this record without saying so. Review is against this record and the page's own ticket; the test holds the shell.

## 6. What this record does not decide

- The eight projections open with their heading as the first block's heading and the record line beneath it; no hero. Decided by the first page package (#173, WP-065).
- Whether the tokens should be shared with the handbook's `styles.css` by a build step rather than by hand is not decided; the workflow stages `showcase.css` as it stages `styles.css`.
- The doctrine sentence on the team page waits on #158, which waits on the contract map's waiver.
