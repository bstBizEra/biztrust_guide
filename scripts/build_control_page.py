#!/usr/bin/env python3
"""Project `badf/` into `control/index.html`, at build time, committing nothing (#352).

WHAT THIS IS. The guide is read; it is not operated. An agent resuming, or a human asking "what is
waiting on me", opens `AGENTS.md`, then `badf/current-state.json`, then `badf/next-actions.json`,
then the tracker, and assembles the answer by hand. This script assembles it once, into a page.

WHAT IT IS NOT. It is a PROJECTION. It grants nothing, records nothing and decides nothing. Every
value it renders is a value one of the source files already spells, rendered in the source's own
words: `state`, `authority` and `resume_decision` are copied, never re-worded. Whether the guide
should adopt separate status axes is #302, which is open and an operator's.

NOTHING GENERATED IS COMMITTED. The tracked `control/index.html` carries an empty, clearly-marked
placeholder that says it has not been generated and names this command. Committing generated state
would create a file that is true when written and false thereafter, which is the defect class
#343, #345, #346 and #347 all describe and `tests/test_stale_records.py` guards against. The Pages
workflow runs this against the STAGED artifact, so `_site/control/index.html` carries the data and
the tracked file stays a placeholder.

    python scripts/build_control_page.py                      # in place, to look at locally
    python scripts/build_control_page.py --out _site/control/index.html   # what the workflow runs

RUNNING THE FIRST FORM TURNS THE TEST SUITE RED, ON PURPOSE, AND THE NINTH FAILURE IS A TRAP.
`python -m unittest discover -s tests` reports NINE failures against a regenerated
`control/index.html`, measured. Eight are the placeholder ratchet doing its job: seven subtests of
`test_every_committed_region_says_it_is_not_generated`, one per region, and
`test_no_committed_region_carries_a_value_read_from_a_record`. They exist to stop a generated page
being committed and they are supposed to fire.

THE NINTH IS `tests/test_html_adr_citations.py::test_the_same_pages_cite_adrs`, and it is the one
that will mislead you. NS-041 and NS-042's recorded prose names ADR-001 to ADR-020, the projector
renders that prose verbatim, and the generated page therefore joins the set of pages citing an ADR -
a set that module asserts BY NAME against `CITING_PAGES`.

**THE FIX IS `git checkout -- control/index.html`.** Restore the placeholder and all nine go green.

**ADDING `control/index.html` TO `CITING_PAGES` IS THE WRONG REPAIR.** That registry is an exact set
equality, so a page listed in it must cite an ADR on EVERY run - and the committed page is a
placeholder that cites none. The moment the placeholder is restored, or CI checks out a fresh tree,
the same test fails in the opposite direction, and the second failure looks unrelated to the first.
The page's ADR citations are a property of the RECORDS at the moment of generation, not of the page;
nothing that is true of the tracked file can be registered about them.

THE RECONCILIATION IS NOT REIMPLEMENTED HERE. `scripts/validate_continuity.py` performs the resume
protocol's step 8 and prints STATE_RECONCILIATION and its reason (WP-112). This script INVOKES that
validator and reads its output. Two facts follow and both are deliberate: the integrity panel is
the validator's own check list rather than a second one, and a reconciliation defect is fixed in
one place. Reimplementing either here would make this page a second source of truth about the
first, which is the thing #352 says a derived surface must never become.

UNKNOWN IS A VALUE, NOT A FAILURE. `.github/workflows/pages.yml` checks out with
`actions/checkout@v7` and no `fetch-depth`, so every CI run is shallow and the history the
reconciliation needs is simply absent there. Every fact this script cannot establish renders as the
literal string UNKNOWN with the reason beside it, and the page says in its own prose that an
UNKNOWN on the published copy is the expected reading rather than a defect. A convenient guess
would be worse than an honest UNKNOWN, because the point of the page is that a reader does not
re-derive it.

NO NETWORK, ANYWHERE. This script runs `git` against the local checkout and `sys.executable`
against the validator, and calls nothing else. It reads no tracker: #311, whether anything should,
is an open decision.

FAIL CLOSED ON THE TEMPLATE. Every marked region in the template must have a builder here and every
builder must find its region. A projector that silently skipped a panel would publish a page with a
hole in it and no line anywhere saying so.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TEMPLATE = ROOT / "control" / "index.html"
CURRENT_STATE = "badf/current-state.json"
NEXT_ACTIONS = "badf/next-actions.json"
VALIDATOR = "scripts/validate_continuity.py"

# The literal every absent fact becomes. One spelling, so that a reader who has learned what it
# means on one panel has learned it on all of them.
UNKNOWN = "UNKNOWN"

# A subprocess that hangs must not hang a workflow that runs on every push.
GIT_TIMEOUT_SECONDS = 10
VALIDATOR_TIMEOUT_SECONDS = 600

# `<!--BTG-CONTROL:name-->` ... `<!--/BTG-CONTROL:name-->`. The markers SURVIVE injection, so
# running this against its own output re-projects rather than appending.
REGION = re.compile(
    r"<!--BTG-CONTROL:(?P<name>[a-z-]+)-->(?P<body>.*?)<!--/BTG-CONTROL:(?P=name)-->",
    re.S,
)


# --- reading, with every failure mode collapsing to a value rather than an exception ------------


def read_json(root: Path, relative: str) -> tuple[dict | None, str]:
    """(document, reason it is absent). A dict or None; never a partial document."""
    path = root / relative
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, f"{relative} could not be read: {exc.__class__.__name__}"
    except ValueError as exc:
        return None, f"{relative} is not valid JSON: {exc.__class__.__name__}"
    if not isinstance(loaded, dict):
        return None, f"{relative} is a {type(loaded).__name__} at the top level, not an object"
    return loaded, ""


def git(root: Path, *args: str) -> str | None:
    """One read-only git command, or None when git could not be run or did not succeed."""
    try:
        done = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    return done.stdout.strip()


def run_validator(root: Path) -> tuple[int | None, str]:
    """Run `scripts/validate_continuity.py` and return (exit code, stdout).

    A None exit code means it could not be run at all, which the panels render as UNKNOWN. The
    validator's own contract is that it prints exactly one CONTINUITY_VALIDATION line whatever
    happens, so a non-zero code here is still readable output and is rendered rather than raised.
    """
    try:
        done = subprocess.run(
            [sys.executable, "-B", str(root / VALIDATOR)],
            cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=VALIDATOR_TIMEOUT_SECONDS,
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        return None, ""
    return done.returncode, done.stdout


# --- pure derivations: everything below takes data and returns data ------------------------------


def parse_validator(stdout: str) -> dict:
    """The validator's output as fields. Parsing only - it decides nothing.

    `checks` is the ordered list of (name, value) from the `PASS: name:value` lines, which IS the
    validator's own check list. `errors` is the `ERROR: ...` lines. The four single-value lines are
    read by name rather than by position, because their order is the validator's to change.
    """
    verdict = ""
    checks: list[tuple[str, str]] = []
    errors: list[str] = []
    fields: dict[str, str] = {}
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("CONTINUITY_VALIDATION="):
            verdict = line.split("=", 1)[1]
        elif line.startswith("PASS: "):
            token = line[len("PASS: "):]
            name, _, value = token.partition(":")
            checks.append((name, value or ""))
        elif line.startswith("ERROR: "):
            errors.append(line[len("ERROR: "):])
        else:
            for key in ("RESUME_DECISION", "PRIMARY_NEXT_ACTION",
                        "STATE_RECONCILIATION", "STATE_RECONCILIATION_REASON"):
                if line.startswith(key + "="):
                    fields[key] = line.split("=", 1)[1]
    return {
        "verdict": verdict or UNKNOWN,
        "checks": checks,
        "errors": errors,
        "resume_decision": fields.get("RESUME_DECISION", UNKNOWN),
        "primary_next_action": fields.get("PRIMARY_NEXT_ACTION", UNKNOWN),
        "reconciliation": fields.get("STATE_RECONCILIATION", UNKNOWN),
        "reconciliation_reason": fields.get("STATE_RECONCILIATION_REASON", ""),
    }


def domain_of(key: str) -> str | None:
    """The domain an authority key NAMES, or None when it names none.

    THE RULE, and it is stated on the page in these words: the key's first underscore-separated
    segment is the domain it names; a key that is a single segment names no domain at all and
    renders under `Unscoped`.

    WHY IT IS THE RULE AND NOT A LOOKUP TABLE. `implementation: GRANTED_BY_USER_REQUEST_2026_09_03`
    sits beside `production_platform_implementation: NOT_GRANTED` in the live record. In a flat
    list a reader can take one for the other, and that defect is #346, open today. A table mapping
    each key to a domain would place `implementation` somewhere - which is guessing, and guessing
    is the whole of #346. A derived rule cannot place it, so it does not, and the page says why.

    The rule is not a status vocabulary: it groups keys by their own spelling and copies every
    value verbatim. It renames nothing.
    """
    head, sep, _ = key.partition("_")
    if not sep or not head:
        return None
    return head


Entries = list[tuple[str, str]]


def group_authority(authority: object) -> tuple[list[tuple[str, Entries]], Entries]:
    """(groups, unscoped). Groups are (domain, [(key, recorded value)]), domain-sorted.

    A non-object `authority`, or a value that is not a string, is not guessed at either: the key is
    rendered with UNKNOWN as its value rather than dropped, because a key silently missing from a
    panel about authority is the worst failure this page has.
    """
    if not isinstance(authority, dict):
        return [], []
    grouped: dict[str, list[tuple[str, str]]] = {}
    unscoped: list[tuple[str, str]] = []
    for key in sorted(authority):
        raw = authority[key]
        value = raw if isinstance(raw, str) else UNKNOWN
        domain = domain_of(key)
        if domain is None:
            unscoped.append((key, value))
        else:
            grouped.setdefault(domain, []).append((key, value))
    return sorted(grouped.items()), unscoped


# The filter the human queue is built with, stated here and printed verbatim on the page. It reads
# the record's OWN strings and adds no word to them: `HUMAN` and `WAIT` are substrings of authority
# values the record already spells, and `human` of an owner_role it already spells.
#
# A COUNT IS ONLY AS GOOD AS ITS FILTER, so the page also lists the actions this filter EXCLUDED
# with their authority strings. Measured against the live record: it admits NS-033, whose authority
# is WAIT_FOR_AUTHORITY_ON_ASSERTED_KEYS_ISSUE_52 and whose owner_role names no human, and it
# excludes NS-043 to NS-045, whose authority is an operator instruction to PROCEED. A filter on
# `owner_role` alone would have dropped NS-024, whose owner_role is `architecture-owner` and whose
# authority is HUMAN_DECISION_REQUIRED.
AUTHORITY_TOKENS = ("HUMAN", "WAIT")
OWNER_TOKEN = "human"


def waits_on_a_human(action: object) -> bool:
    if not isinstance(action, dict):
        return False
    authority = action.get("authority")
    owner = action.get("owner_role")
    if isinstance(authority, str) and any(token in authority for token in AUTHORITY_TOKENS):
        return True
    return isinstance(owner, str) and OWNER_TOKEN in owner


def human_queue(actions: object) -> tuple[list[dict], list[dict]]:
    """(queue, excluded), both in the record's own priority order.

    An action with no numeric `priority` sorts last rather than being dropped, and keeps whatever
    the record spells; ordering is the only thing derived here.
    """
    if not isinstance(actions, dict):
        return [], []
    rows = actions.get("actions")
    if not isinstance(rows, list):
        return [], []
    kept = [row for row in rows if isinstance(row, dict)]

    def order(row: dict) -> tuple[int, object]:
        priority = row.get("priority")
        if isinstance(priority, bool) or not isinstance(priority, int):
            return (1, 0)
        return (0, priority)

    ordered = sorted(kept, key=order)
    return ([row for row in ordered if waits_on_a_human(row)],
            [row for row in ordered if not waits_on_a_human(row)])


def field(document: object, *path: str) -> str:
    """A string field, or UNKNOWN. Never a stand-in that could be read as a real value."""
    node: object = document
    for step in path:
        if not isinstance(node, dict) or step not in node:
            return UNKNOWN
        node = node[step]
    if isinstance(node, str) and node:
        return node
    return UNKNOWN


# --- rendering -----------------------------------------------------------------------------------


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def provenance_line(source: str, commit: str, written_of: str, written: str, built: str) -> str:
    """The one sentence every panel but Provenance ends with; that panel states the same facts
    as its own rows. A panel that cannot say where its numbers came from is a second source of
    truth, so this is not optional on any of them.

    `written_of` is named rather than implied. The reconciliation and integrity panels are sourced
    from the validator, and the timestamp beside them belongs to the RECORD the validator read, not
    to the validator; a sentence that said "the record" without saying which one would be a
    sentence that does not match its measurement.
    """
    return (
        f'<p class="section-intro">Source <code>{esc(source)}</code> at source commit '
        f'<code>{esc(commit)}</code>; <code>{esc(written_of)}</code> was written {esc(written)}; '
        f'this projection was built {esc(built)}.</p>'
    )


def render_unknown(facts: dict, source: str, reason: str, written: str) -> str:
    """A panel whose source record could not be read. UNKNOWN, with the reason, and nothing else.

    #352: "The projector emits UNKNOWN where a fact is absent, never a convenient value." An EMPTY
    RENDERING IS A CONVENIENT VALUE. Measured before this existed: deleting `badf/next-actions.json`
    from a copy of the tree and running the projector produced a queue panel reading "No recorded
    action matches the filter. That is a reading of badf/next-actions.json" - a sentence that was
    false, because nothing had been read - followed by "The 0 recorded action(s) the filter did NOT
    admit" and "The filter excluded no recorded action". Exit 0, page built, and a reader could not
    tell an empty queue from an absent file.

    So the count, the excluded list and every explanatory sentence are SUPPRESSED here rather than
    drawn with zeroes. A zero is a measurement; there was no measurement.

    THE REASON IS THE VALIDATOR OF THIS PANEL. It comes from `read_json`, which has always returned
    one and whose callers discarded it, so the docstring's promise of "UNKNOWN with the reason
    beside it" was unkept. It is threaded through `build` -> `gather` -> here.
    """
    return (
        '<div class="callout">'
        f'<strong>{UNKNOWN}</strong>'
        f'<p>{esc(reason)}. Nothing else is shown in this panel. A count, a list or an empty '
        f'table drawn from a record that was never read would report a measurement this projection '
        f'does not have, and {UNKNOWN} is the honest answer rather than a convenient one.</p>'
        '</div>'
        + provenance_line(source, facts["commit"], source, written, facts["built_at"])
    )


def render_decision(facts: dict) -> str:
    """RESUME_DECISION, first on the page and in the loudest component the guide has.

    The value is the record's own word. The reader is told which action it is about and where that
    action is recorded; nothing here says what to do about it.
    """
    if facts["current_absent"]:
        return render_unknown(facts, CURRENT_STATE, facts["current_absent"], facts["recorded_at"])
    decision = facts["resume_decision"]
    primary_id = facts["primary_next_action"]
    primary = facts["primary_action"]
    detail = (
        f'Primary next action <b>{esc(primary_id)}</b> &middot; owner role '
        f'<b>{esc(field(primary, "owner_role"))}</b> &middot; recorded authority '
        f'<b>{esc(field(primary, "authority"))}</b>. '
        f'{esc(field(primary, "action"))}'
        if primary is not None else
        f'Primary next action <b>{esc(primary_id)}</b>. {esc(facts["actions_absent"])}, so nothing '
        f'more about it is shown here.'
        if facts["actions_absent"] else
        f'Primary next action <b>{esc(primary_id)}</b>. '
        f'No matching action is recorded in <code>{esc(NEXT_ACTIONS)}</code>, so nothing more '
        f'about it is shown here.'
    )
    return (
        '<div class="next-action">'
        '<span>RESUME DECISION</span>'
        f'<div><h3>{esc(decision)}</h3><p>{detail}</p></div>'
        f'<b>{esc(primary_id)}</b>'
        '</div>'
        + provenance_line(CURRENT_STATE, facts["commit"], CURRENT_STATE,
                          facts["recorded_at"], facts["built_at"])
    )


def render_package(facts: dict) -> str:
    if facts["current_absent"]:
        return render_unknown(facts, CURRENT_STATE, facts["current_absent"], facts["recorded_at"])
    work_package = facts["work_package"]
    source = facts["source"]
    rows = [
        ("Identifier", field(work_package, "id")),
        ("Title", field(work_package, "title")),
        ("Recorded state", field(work_package, "state")),
        ("Owner role", field(work_package, "owner_role")),
        ("Issue", field(work_package, "issue_url")),
        ("Branch", field(source, "branch")),
        ("Baseline commit", field(source, "baseline_commit")),
        ("Baseline kind", field(source, "baseline_kind")),
    ]
    body = "".join(
        f'<div><span>{esc(label)}</span><p>{esc(value)}</p></div>' for label, value in rows
    )
    return (
        f'<div class="definition-list">{body}</div>'
        + provenance_line(CURRENT_STATE, facts["commit"], CURRENT_STATE,
                          facts["recorded_at"], facts["built_at"])
    )


def render_reconciliation(facts: dict) -> str:
    reason = facts["reconciliation_reason"] or "the validator printed no reason line"
    rows = [
        ("Verdict", facts["reconciliation"]),
        ("Reason", reason),
        ("Clone", facts["clone_depth"]),
        ("Printed by", f"{VALIDATOR}, invoked by this projector; not recomputed here"),
    ]
    body = "".join(
        f'<div><span>{esc(label)}</span><p>{esc(value)}</p></div>' for label, value in rows
    )
    return (
        f'<div class="definition-list">{body}</div>'
        + provenance_line(VALIDATOR, facts["commit"], CURRENT_STATE,
                          facts["recorded_at"], facts["built_at"])
    )


def render_queue(facts: dict) -> str:
    if facts["actions_absent"]:
        return render_unknown(facts, NEXT_ACTIONS, facts["actions_absent"],
                              facts["actions_recorded_at"])
    queue, excluded = facts["queue"], facts["excluded"]
    if queue:
        rows = "".join(
            "<tr>"
            f'<td><strong>{esc(field(row, "id"))}</strong></td>'
            f'<td>{esc(row.get("priority", UNKNOWN))}</td>'
            f'<td>{esc(field(row, "owner_role"))}</td>'
            f'<td><code>{esc(field(row, "authority"))}</code></td>'
            f'<td>{esc(field(row, "action"))}</td>'
            "</tr>"
            for row in queue
        )
        table = (
            '<div class="table-wrap"><table>'
            f'<caption>{len(queue)} of the {len(queue) + len(excluded)} recorded actions, in the '
            f"record's own priority order &mdash; {NEXT_ACTIONS}</caption>"
            "<thead><tr><th>Action</th><th>Priority</th><th>Owner role</th>"
            "<th>Recorded authority</th><th>What is asked</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div>"
        )
    else:
        table = (
            '<p class="section-intro">No recorded action matches the filter. That is a reading of '
            f'<code>{esc(NEXT_ACTIONS)}</code>, not a statement that nothing is waiting.</p>'
        )
    residue = "".join(
        f'<div><span>{esc(field(row, "id"))}</span><p><code>{esc(field(row, "authority"))}</code> '
        f'&middot; owner role {esc(field(row, "owner_role"))}</p></div>'
        for row in excluded
    ) or '<div><span>None</span><p>The filter excluded no recorded action.</p></div>'
    return (
        table
        + f'<p class="section-intro">The {len(excluded)} recorded action(s) the filter did NOT '
          "admit, with the authority string each one carries, so that the count above can be "
          "checked rather than trusted:</p>"
        + f'<div class="definition-list">{residue}</div>'
        + provenance_line(NEXT_ACTIONS, facts["commit"], NEXT_ACTIONS, facts["actions_recorded_at"],
                          facts["built_at"])
    )


def render_authority(facts: dict) -> str:
    if facts["current_absent"]:
        return render_unknown(facts, CURRENT_STATE, facts["current_absent"], facts["recorded_at"])
    groups, unscoped = facts["authority_groups"], facts["authority_unscoped"]
    rows = "".join(
        "<tr>"
        f"<td>{esc(domain)}</td>"
        f"<td><code>{esc(key)}</code></td>"
        f"<td><code>{esc(value)}</code></td>"
        "</tr>"
        for domain, entries in groups
        for key, value in entries
    )
    rows += "".join(
        "<tr>"
        "<td><strong>Unscoped</strong></td>"
        f"<td><code>{esc(key)}</code></td>"
        f"<td><code>{esc(value)}</code></td>"
        "</tr>"
        for key, value in unscoped
    )
    if not rows:
        return (
            f'<p class="section-intro">No authority block is recorded in '
            f'<code>{esc(CURRENT_STATE)}</code>, so this panel shows {UNKNOWN} rather than an '
            "empty grant list.</p>"
            + provenance_line(CURRENT_STATE, facts["commit"], CURRENT_STATE, facts["recorded_at"],
                              facts["built_at"])
        )
    counted = sum(len(entries) for _, entries in groups) + len(unscoped)
    return (
        '<div class="table-wrap"><table>'
        f"<caption>{counted} recorded authority key(s) across {len(groups)} named domain(s) and "
        f"{len(unscoped)} unscoped &mdash; values verbatim from {CURRENT_STATE}</caption>"
        "<thead><tr><th>Domain the key names</th><th>Key</th><th>Recorded value</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
        + provenance_line(CURRENT_STATE, facts["commit"], CURRENT_STATE,
                          facts["recorded_at"], facts["built_at"])
    )


def render_integrity(facts: dict) -> str:
    checks, errors = facts["checks"], facts["validator_errors"]
    rows = "".join(
        f"<tr><td><code>{esc(name)}</code></td><td>PASS</td>"
        f"<td>{esc(value) if value else '&mdash;'}</td></tr>"
        for name, value in checks
    )
    rows += "".join(
        f'<tr><td><code>error</code></td><td>FAIL</td><td>{esc(message)}</td></tr>'
        for message in errors
    )
    if not rows:
        rows = (
            f"<tr><td><code>{UNKNOWN}</code></td><td>{UNKNOWN}</td>"
            "<td>the validator printed no check line this projector could read</td></tr>"
        )
    return (
        '<div class="table-wrap"><table>'
        f'<caption>CONTINUITY_VALIDATION={esc(facts["validator_verdict"])} &mdash; '
        f'exit {esc(facts["validator_exit"])} &mdash; every check and error line the validator '
        "printed, in the order it printed them</caption>"
        "<thead><tr><th>Check</th><th>Result</th><th>What it counted</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
        + provenance_line(VALIDATOR, facts["commit"], CURRENT_STATE,
                          facts["recorded_at"], facts["built_at"])
    )


def render_provenance(facts: dict) -> str:
    rows = [
        ("Source files", f"{CURRENT_STATE}, {NEXT_ACTIONS}, {VALIDATOR}"),
        ("Source commit", facts["commit"]),
        ("Source commit subject", facts["commit_subject"]),
        ("Source commit written", facts["commit_at"]),
        ("Clone", facts["clone_depth"]),
        ("Record written", f"{CURRENT_STATE}: {facts['recorded_at']}"),
        ("Actions written", f"{NEXT_ACTIONS}: {facts['actions_recorded_at']}"),
        ("Projection built", facts["built_at"]),
        ("Built by", "scripts/build_control_page.py"),
    ]
    body = "".join(
        f'<div><span>{esc(label)}</span><p>{esc(value)}</p></div>' for label, value in rows
    )
    return f'<div class="definition-list">{body}</div>'


BUILDERS = {
    "decision": render_decision,
    "package": render_package,
    "reconciliation": render_reconciliation,
    "queue": render_queue,
    "authority": render_authority,
    "integrity": render_integrity,
    "provenance": render_provenance,
}


# --- gathering and injection ---------------------------------------------------------------------


def observe(root: Path) -> dict:
    """The IMPURE half: what git and the validator say about this checkout, right now.

    Kept apart from `gather` so that everything a panel derives is a pure function of data. The
    suite in `tests/` runs no subprocess - that is a property of `tests/` worth keeping - and it
    exercises the derivations against real records and a synthetic observation instead.
    """
    exit_code, stdout = run_validator(root)
    commit = git(root, "rev-parse", "HEAD") or UNKNOWN
    subject = git(root, "log", "-1", "--format=%s") or UNKNOWN
    commit_at = git(root, "log", "-1", "--format=%cI") or UNKNOWN
    shallow = git(root, "rev-parse", "--is-shallow-repository")
    if shallow == "true":
        clone_depth = (
            "shallow - the history before HEAD is absent, so any fact needing it reads UNKNOWN"
        )
    elif shallow == "false":
        clone_depth = "full history"
    else:
        clone_depth = f"{UNKNOWN} - git could not report whether this clone is shallow"
    return {
        "validator_exit": UNKNOWN if exit_code is None else exit_code,
        "validator_stdout": stdout,
        "commit": commit,
        "commit_subject": subject,
        "commit_at": commit_at,
        "clone_depth": clone_depth,
    }


def unusable(document: dict | None, why: str, relative: str) -> str:
    """Why `relative` cannot be projected, or "" when it can.

    An empty string means USABLE, and every panel guard reads it that way. The fallback exists so
    that a caller which loses the reason still cannot produce a confident-looking panel: it says
    the reason was not recorded rather than inventing one.
    """
    if document is not None:
        return ""
    return why or f"{relative} is not available and no reason was recorded"


def gather(current: dict | None, actions: dict | None, observed: dict, now: datetime,
           absent: dict[str, str] | None = None) -> dict:
    """Every fact the panels render, with each absent one already turned into UNKNOWN.

    PURE. It reads no file, runs no process and asks the clock nothing; `now`, `observed` and
    `absent` are handed in. A fact that is absent becomes UNKNOWN here rather than at the point of
    rendering, so that every panel spells it the one way.

    `absent` maps a source path to the reason `read_json` gave for not returning a document. It is
    threaded rather than discarded because the panels must say WHY, and because an unreadable
    record and an empty one are different facts that looked identical on the page until they were
    told apart here.
    """
    absent = absent or {}
    printed = parse_validator(observed.get("validator_stdout", ""))
    current_absent = unusable(current, absent.get(CURRENT_STATE, ""), CURRENT_STATE)
    actions_absent = unusable(actions, absent.get(NEXT_ACTIONS, ""), NEXT_ACTIONS)
    # A document that loaded but carries no `actions` array is a THIRD case, and rendering it as an
    # empty queue would repeat the defect one level down: the file was read, and it still says
    # nothing about what is waiting.
    if not actions_absent and not isinstance((actions or {}).get("actions"), list):
        actions_absent = (
            f"{NEXT_ACTIONS} loaded, but it carries no `actions` array, so there is no queue in it "
            f"to project"
        )
    groups, unscoped = group_authority(current.get("authority") if current else None)
    queue, excluded = human_queue(actions)
    primary_id = field(current, "primary_next_action_id")
    primary = None
    if isinstance(actions, dict) and isinstance(actions.get("actions"), list):
        for row in actions["actions"]:
            if isinstance(row, dict) and row.get("id") == primary_id:
                primary = row
                break

    return {
        "current_absent": current_absent,
        "actions_absent": actions_absent,
        # The record is the authority on its own resume decision; the validator ECHOES it. Read
        # from the record, so that a validator that could not run leaves this panel UNKNOWN rather
        # than silently reporting the echo of a file this projector never opened.
        "resume_decision": field(current, "resume_decision"),
        "primary_next_action": primary_id,
        "primary_action": primary,
        "work_package": current.get("active_work_package") if current else None,
        "source": current.get("source") if current else None,
        "authority_groups": groups,
        "authority_unscoped": unscoped,
        "queue": queue,
        "excluded": excluded,
        "reconciliation": printed["reconciliation"],
        "reconciliation_reason": printed["reconciliation_reason"],
        "checks": printed["checks"],
        "validator_errors": printed["errors"],
        "validator_verdict": printed["verdict"],
        "validator_exit": observed.get("validator_exit", UNKNOWN),
        "commit": observed.get("commit", UNKNOWN),
        "commit_subject": observed.get("commit_subject", UNKNOWN),
        "commit_at": observed.get("commit_at", UNKNOWN),
        "clone_depth": observed.get("clone_depth", UNKNOWN),
        "recorded_at": field(current, "updated_at"),
        "actions_recorded_at": field(actions, "updated_at"),
        "built_at": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


class ProjectionError(Exception):
    """The template and this projector do not agree about which panels exist.

    An ORDINARY exception, deliberately, and it was a `SystemExit` first. `unittest` treats
    `SystemExit` as a BaseException and lets it out of the runner, so a copy of the tree with one
    builder removed aborted the whole suite with no summary at all - exit 1 and not one named
    failure - and `scripts/wp113_controls.py` could not say which test had caught it. Measured on
    three controls at once. `main()` turns this into the exit code; nothing else may.
    """


def regions(template: str) -> list[str]:
    """Every marked region name in the template, in order, duplicates included."""
    return [match.group("name") for match in REGION.finditer(template)]


def inject(template: str, blocks: dict[str, str]) -> str:
    """Replace each region's body with its block. Fail closed on any mismatch.

    A region with no builder, or a builder with no region, is an error and not a warning: the
    failure mode being prevented is a published page with a panel silently missing from it.
    """
    found = regions(template)
    if len(found) != len(set(found)):
        repeated = sorted({name for name in found if found.count(name) > 1})
        raise ProjectionError(
            f"the template repeats region(s) {repeated}; each must appear once")
    missing = sorted(set(found) - set(blocks))
    unused = sorted(set(blocks) - set(found))
    if missing or unused:
        raise ProjectionError(
            f"template and projector disagree: regions with no builder {missing}, "
            f"builders with no region {unused}"
        )
    return REGION.sub(
        lambda m: f"<!--BTG-CONTROL:{m.group('name')}-->"
                  f"{blocks[m.group('name')]}"
                  f"<!--/BTG-CONTROL:{m.group('name')}-->",
        template,
    )


def render(facts: dict, template: str) -> str:
    return inject(template, {name: builder(facts) for name, builder in BUILDERS.items()})


def build(root: Path, template: str, now: datetime) -> str:
    current, current_why = read_json(root, CURRENT_STATE)
    actions, actions_why = read_json(root, NEXT_ACTIONS)
    # BOTH reasons are kept. They were discarded here - `current, _ = read_json(...)` - while the
    # module docstring promised "UNKNOWN with the reason beside it", which nothing rendered.
    absent = {CURRENT_STATE: current_why, NEXT_ACTIONS: actions_why}
    return render(gather(current, actions, observe(root), now, absent), template)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out", default=None,
        help="where to write the projected page; defaults to the template itself, "
             "control/index.html, so a person can regenerate it and look at it",
    )
    parser.add_argument(
        "--template", default=None,
        help="the page to read the marked regions from; defaults to control/index.html",
    )
    args = parser.parse_args(argv)

    template_path = Path(args.template).resolve() if args.template else TEMPLATE
    out_path = Path(args.out).resolve() if args.out else template_path
    try:
        template = template_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"cannot read the template {template_path}: {exc}")

    try:
        page = build(ROOT, template, datetime.now(timezone.utc))
    except ProjectionError as exc:
        raise SystemExit(f"cannot project {template_path}: {exc}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8", newline="\n")
    print(f"CONTROL_PAGE_WRITTEN={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
