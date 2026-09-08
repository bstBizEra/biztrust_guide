#!/usr/bin/env python3
"""Continuity and static-site validation for BizTrust Guide.

Fail-closed on MALFORMED input: a wrong-typed field, an unreadable file or an
unforeseen exception always produces exactly one CONTINUITY_VALIDATION line
and a non-zero exit. Content is checked for PRESENCE and shape, not for
substance - a file that exists and parses satisfies its check.

Exit codes:
    0    PASS - every check ran and none recorded an error
    1    FAIL - a data defect: the artifacts under validation are wrong
    2    FAIL - a validator defect: an unforeseen exception in this script
    130  FAIL - interrupted
A consumer that treats any non-zero as failure is correct; 1 and 2 differ so
that a reader knows which artifact to debug.

On PASS the run also prints STATE_RECONCILIATION and its reason: the resume
protocol's step 8, performed rather than asked for. It is ADVISORY - it reads
git, reports one of four words about the record, and cannot fail the run. See
`reconcile_recorded_state`.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import traceback
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SHA40 = re.compile(r"^[0-9a-f]{40}$")


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.refs: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"] or "")
        for attr in ("href", "src"):
            if values.get(attr):
                self.refs.append((tag, values[attr] or ""))


def load_json(relative: str, errors: list[str]) -> dict:
    path = ROOT / relative
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        # ValueError covers json.JSONDecodeError AND UnicodeDecodeError; a
        # single bad byte previously aborted the whole run.
        errors.append(f"{relative}: cannot load valid JSON: {exc}")
        return {}
    if not isinstance(document, dict):
        errors.append(
            f"{relative}: expected a JSON object at the top level, "
            f"found {type(document).__name__}"
        )
        return {}
    return document


def as_object(value: object, label: str, errors: list[str]) -> dict:
    """Return value as a mapping, or record why it is not one.

    A wrong-typed field must become a recorded error, never an exception:
    an uncaught AttributeError prints a traceback and no
    CONTINUITY_VALIDATION line at all, so a caller checking for FAIL sees
    neither PASS nor FAIL and may read the silence as success.
    """
    if value is None:
        errors.append(f"{label}: expected an object, found nothing (key absent or null)")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label}: expected an object, found {type(value).__name__}")
        return {}
    return value


def as_array(value: object, label: str, errors: list[str]) -> list:
    """Return value as a list, or record why it is not one."""
    if value is None:
        errors.append(f"{label}: expected an array, found nothing (key absent or null)")
        return []
    if not isinstance(value, list):
        errors.append(f"{label}: expected an array, found {type(value).__name__}")
        return []
    return value


def heading_slug(title: str) -> str:
    """A Markdown heading's anchor, by the rule GitHub uses.

    Link text replaces its link, backticks and emphasis markers go, what is left is lowercased,
    everything but a letter, digit, space, hyphen or underscore is dropped, and spaces become
    hyphens. GitHub also disambiguates a repeated heading with `-1`, `-2`; that is not implemented,
    because no link in this repository points at a Markdown heading at all. The rule is held by its
    own tests rather than by the corpus, and this comment is here so the next reader knows which.
    """
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", title)
    text = text.replace("`", "").replace("**", "").replace("*", "")
    text = re.sub(r"[^\w\- ]", "", text.strip().lower())
    return text.replace(" ", "-")


def markdown_headings(source: str) -> set[str]:
    """Every anchor a Markdown document offers, from its ATX headings."""
    return {heading_slug(m.group(1)) for m in re.finditer(r"^#{1,6}\s+(.+?)\s*$", source, re.M)}


# --- step 8: the recorded active Work Package against observed git ------------------------------
#
# AGENTS.md section 3 step 7 hands an agent this script; step 8 says "Reconcile observed state with
# recorded state" and nothing performed it. Before WP-112 this file made no git call at all, so a
# record naming BIZTRUST-GUIDE-WP-111 as the active package in a pre-merge state printed PASS while
# that package's merge commit WAS main's HEAD.
#
# THE VERDICT IS ADVISORY AND MUST STAY SO. It never appends to `errors`, never changes the exit
# code and never changes what this script validates. `.github/workflows/pages.yml` checks out with
# `actions/checkout@v7` and no `fetch-depth`, so CI runs on a SHALLOW clone in which the recorded
# baseline is simply not in the object database. A check that failed there would fail for a reason
# that has nothing to do with the repository - the flakiness #311 keeps out of this suite. Where
# the history needed to judge is absent the answer is UNKNOWN with the reason, never a convenient
# guess: a wrong CONSISTENT is worse than an honest UNKNOWN, because the point of the line is that
# a reader can trust step 8 without re-deriving it.
RECONCILIATION_VOCABULARY = ("CONSISTENT", "LAG_EXPECTED", "DIVERGED", "UNKNOWN")

# Read in this order. `origin/main` is the published main line; a clone that has it but no local
# `main` is still judgeable. HEAD is deliberately NOT a fallback: on a Work Package branch HEAD
# carries that package's own unmerged commits, and reading those as landings would report the
# ordinary case - an agent working on a branch - as a reconciliation result about main.
MAIN_REFS = ("refs/remotes/origin/main", "refs/heads/main")

# A hung git must not hold up a workflow that runs on every push and every pull request. Six calls
# at worst, each read-only, each bounded.
GIT_TIMEOUT_SECONDS = 10


def git(root: Path, *args: str) -> tuple[int, str] | None:
    """Run one read-only git command rooted at `root`.

    Returns (exit code, stripped stdout), or None when git could not be run at all - not
    installed, not executable, or over time. Every failure mode collapses to a value the caller
    turns into UNKNOWN; none of them may raise, because this runs inside a validator whose
    contract is that it prints exactly one verdict line.
    """
    try:
        done = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return done.returncode, done.stdout.strip()


def reconcile_recorded_state(root: Path, current: dict) -> tuple[str, str]:
    """Compare the RECORDED active Work Package against the OBSERVED main line.

    Returns one member of RECONCILIATION_VOCABULARY and a single-line reason.

    The four answers, in the order they are decided:

    UNKNOWN       the history needed to judge is unavailable - no git, no repository, a shallow
                  clone, no main ref, or a baseline commit this clone does not hold.
    DIVERGED      the recorded baseline commit is NOT an ancestor of the observed main line. The
                  record was branched from a history this repository does not have; no ordering
                  of merges explains that.
    LAG_EXPECTED  the recorded package has already LANDED on the main line since that baseline.
                  `badf/current-state.json` is written on a package's branch BEFORE its merge, so
                  it cannot record its own merge; every merge leaves this window until the next
                  package opens it. Normal, not a defect - and explicitly NOT work in progress,
                  because the branch may still exist and an agent resuming from the record alone
                  would reopen finished work.
    CONSISTENT    the baseline is an ancestor and the recorded package has not landed.

    CONSISTENT does not require the main line to be still AT the baseline. Another package
    merging while this one is in flight is ordinary; what the record claims is that ITS package is
    active, and that claim is true until that package lands. Reading any movement as lag would
    make every normal merge look like a fault, which is the reason this vocabulary has four words
    rather than two.
    """
    work_package = current.get("active_work_package")
    source = current.get("source")
    wp_id = work_package.get("id") if isinstance(work_package, dict) else None
    baseline = source.get("baseline_commit") if isinstance(source, dict) else None
    if not isinstance(wp_id, str) or not wp_id:
        return "UNKNOWN", "the record carries no active Work Package id to reconcile"
    if not isinstance(baseline, str) or not SHA40.fullmatch(baseline):
        return "UNKNOWN", f"{wp_id}: the record carries no 40-character baseline commit"

    top = git(root, "rev-parse", "--show-toplevel")
    if top is None:
        return "UNKNOWN", f"{wp_id}: git could not be run, so no history is observable"
    if top[0] != 0 or not top[1]:
        return "UNKNOWN", f"{wp_id}: {root} is not inside a git repository"
    # An enclosing repository is not this one. Without this, a copy of the tree unpacked under
    # some unrelated checkout would be reconciled against THAT repository's history and the answer
    # would look authoritative.
    if os.path.normcase(os.path.realpath(top[1])) != os.path.normcase(os.path.realpath(root)):
        return "UNKNOWN", f"{wp_id}: {root} is not the root of the git repository that contains it"

    shallow = git(root, "rev-parse", "--is-shallow-repository")
    if shallow is None or shallow[0] != 0:
        return "UNKNOWN", f"{wp_id}: git could not report whether this clone is shallow"
    if shallow[1] == "true":
        return "UNKNOWN", (
            f"{wp_id}: this clone is shallow, so the history before HEAD is absent and no "
            f"ancestry can be established (the Pages workflow checks out without fetch-depth)"
        )

    tip_ref = tip_sha = ""
    for ref in MAIN_REFS:
        resolved = git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
        if resolved is not None and resolved[0] == 0 and SHA40.fullmatch(resolved[1]):
            tip_ref, tip_sha = ref, resolved[1]
            break
    if not tip_sha:
        return "UNKNOWN", (
            f"{wp_id}: neither {' nor '.join(MAIN_REFS)} resolves here, so there is no observed "
            f"main line to compare against"
        )

    held = git(root, "cat-file", "-e", f"{baseline}^{{commit}}")
    if held is None:
        return "UNKNOWN", f"{wp_id}: git could not be run, so no history is observable"
    if held[0] != 0:
        return "UNKNOWN", (
            f"{wp_id}: the recorded baseline {baseline[:12]} is not in this clone's object "
            f"database, so its relation to {tip_ref} cannot be established"
        )

    ancestry = git(root, "merge-base", "--is-ancestor", baseline, tip_sha)
    if ancestry is None or ancestry[0] not in (0, 1):
        return "UNKNOWN", f"{wp_id}: git could not decide whether {baseline[:12]} precedes {tip_ref}"
    if ancestry[0] == 1:
        return "DIVERGED", (
            f"{wp_id}: the recorded baseline {baseline[:12]} is not an ancestor of {tip_ref} "
            f"({tip_sha[:12]}); the record was branched from a history this repository does not "
            f"carry"
        )

    log = git(root, "log", "--format=%s", f"{baseline}..{tip_sha}")
    if log is None or log[0] != 0:
        return "UNKNOWN", f"{wp_id}: git could not list the commits between {baseline[:12]} and {tip_ref}"
    subjects = [line for line in log[1].splitlines() if line.strip()]
    # A package lands as a commit whose subject OPENS with its bracketed id - the convention every
    # merge on this main line has followed. Matched at the start rather than anywhere in the
    # subject, so a commit that merely mentions another package is not read as that package's
    # landing.
    landings = [subject for subject in subjects if subject.startswith(f"[{wp_id}]")]
    if landings:
        return "LAG_EXPECTED", (
            f"{wp_id} has already landed on {tip_ref} ({len(landings)} commit(s) since the "
            f"recorded baseline {baseline[:12]}); the record was written on that package's branch "
            f"before its own merge and does NOT describe work still in progress"
        )
    return "CONSISTENT", (
        f"{wp_id} has not landed on {tip_ref}; {len(subjects)} commit(s) have landed since the "
        f"recorded baseline {baseline[:12]} and none of them is this package"
    )


def reconcile_safely(root: Path, current: dict) -> tuple[str, str]:
    """`reconcile_recorded_state`, with the guarantee that it cannot break the validator.

    An advisory line is not worth a traceback in place of a verdict. Anything unforeseen here
    becomes UNKNOWN, which is exactly what UNKNOWN is for.
    """
    try:
        verdict, reason = reconcile_recorded_state(root, current)
    except BaseException as exc:  # noqa: BLE001 - advisory output must never fail the run
        return "UNKNOWN", f"the reconciliation itself failed: {type(exc).__name__}: {exc}"
    if verdict not in RECONCILIATION_VOCABULARY:
        return "UNKNOWN", f"the reconciliation returned {verdict!r}, which is not in the vocabulary"
    return verdict, " ".join(str(reason).split())


def main() -> int:
    errors: list[str] = []
    checks: list[str] = []
    required = [
        "AGENTS.md",
        "README.md",
        "index.html",
        "styles.css",
        "script.js",
        ".nojekyll",
        ".github/workflows/pages.yml",
        "badf/current-state.json",
        "badf/next-actions.json",
        "badf/decision-log.jsonl",
        "schemas/session-checkpoint.schema.json",
        "schemas/handoff.schema.json",
        "schemas/current-state.schema.json",
        "schemas/next-actions.schema.json",
        "schemas/decision-record.schema.json",
        "templates/session-checkpoint.json",
        "templates/handoff.json",
        "docs/LIVE_PREVIEW.md",
        "docs/AGENT_CONTINUITY.md",
        "docs/NEXT_STEPS.md",
    ]
    missing = [item for item in required if not (ROOT / item).is_file()]
    if missing:
        errors.append("Missing required files: " + ", ".join(missing))
    else:
        checks.append(f"required-files:{len(required)}")

    current = load_json("badf/current-state.json", errors)
    actions = load_json("badf/next-actions.json", errors)
    # An empty object is valid JSON, loads without error, and is FALSY. Before
    # these two lines, `{}` in either file skipped every continuity check below
    # and still printed PASS with exit 0 - strictly worse than the crash this
    # module was written to remove, because a crash is at least visible.
    if not current:
        errors.append("badf/current-state.json: document is empty; no state to validate")
    if not actions:
        errors.append("badf/next-actions.json: document is empty; no actions to validate")
    checkpoint: dict = {}
    checkpoint_path = current.get("latest_checkpoint")
    if checkpoint_path is not None and not isinstance(checkpoint_path, str):
        errors.append(
            "current-state: latest_checkpoint must be a string path, "
            f"found {type(checkpoint_path).__name__}"
        )
        checkpoint_path = None
    if isinstance(checkpoint_path, str) and "\x00" in checkpoint_path:
        errors.append("current-state: latest_checkpoint contains a null byte")
        checkpoint_path = None
    if isinstance(checkpoint_path, str) and checkpoint_path:
        try:
            resolved = (ROOT / checkpoint_path).resolve()
        except (OSError, ValueError) as exc:
            errors.append(f"current-state: latest_checkpoint is unusable as a path: {exc}")
            resolved = ROOT
        if ROOT not in resolved.parents and resolved != ROOT:
            errors.append(
                f"current-state: latest_checkpoint escapes the repository root: {checkpoint_path}"
            )
            checkpoint_path = None
    if checkpoint_path:
        checkpoint = load_json(checkpoint_path, errors)
        if not checkpoint:
            errors.append(f"{checkpoint_path}: checkpoint document is empty")
    else:
        errors.append("current-state: latest_checkpoint is missing")

    if current and actions:
        wp = as_object(current.get("active_work_package"), "current-state.active_work_package", errors)
        wp_id = wp.get("id")
        if not wp_id or wp_id != actions.get("work_package_id"):
            errors.append("State/action Work Package IDs do not match")
        if checkpoint and checkpoint.get("work_package_id") != wp_id:
            errors.append("Checkpoint Work Package ID does not match current state")
        if current.get("project_id") != actions.get("project_id"):
            errors.append("State/action project IDs do not match")
        baseline = as_object(current.get("source"), "current-state.source", errors).get("baseline_commit", "")
        if not isinstance(baseline, str) or not SHA40.fullmatch(baseline):
            errors.append("Current-state baseline_commit is not a 40-character SHA")
        action_rows = as_array(actions.get("actions"), "next-actions.actions", errors)
        malformed = [i for i, row in enumerate(action_rows) if not isinstance(row, dict)]
        if malformed:
            errors.append(f"next-actions: entries at positions {malformed} are not objects")
            action_rows = [row for row in action_rows if isinstance(row, dict)]
        unhashable = [i for i, row in enumerate(action_rows) if not isinstance(row.get("id"), str)]
        if unhashable:
            errors.append(f"next-actions: entries at positions {unhashable} have a non-string id")
        action_ids = [row.get("id") for row in action_rows if isinstance(row.get("id"), str)]
        if len(action_ids) != len(set(action_ids)):
            errors.append("next-actions contains duplicate action IDs")
        primary = [row for row in action_rows if row.get("primary") is True]
        if len(primary) != 1:
            errors.append("next-actions must contain exactly one primary action")
        elif primary[0].get("id") != current.get("primary_next_action_id"):
            errors.append("Primary next action does not match current state")
        if len(primary) == 1:
            # resume_decision is a CONCLUSION about the primary action, not an
            # independent field. It was carried forward unrecomputed across a
            # re-anchor once, leaving WAIT_FOR_AUTHORITY beside a granted action -
            # which tells a resuming agent to stop and to proceed at the same time.
            # Narrow on purpose: this asserts the one contradiction that occurred,
            # not a full decision function, because inventing the rest would make
            # the check unfalsifiable.
            authority = primary[0].get("authority", "")
            decision = current.get("resume_decision", "")
            if isinstance(authority, str) and authority.startswith("GRANTED") \
                    and decision == "WAIT_FOR_AUTHORITY":
                errors.append(
                    f"resume_decision is WAIT_FOR_AUTHORITY but the primary action "
                    f"{primary[0].get('id')} carries authority {authority!r}: a resuming "
                    f"agent is told to stop and to proceed at once"
                )
        priorities = [row.get("priority") for row in action_rows]
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 1 for value in priorities):
            errors.append("Every next action requires a positive integer priority")
        elif priorities != sorted(priorities):
            # Only comparable once every value is known to be a positive int:
            # sorted() on mixed types raises, and the error above already fired.
            errors.append("Next actions must be stored in priority order")
        required_action_fields = {
            "id", "primary", "priority", "owner_role", "authority", "action",
            "prerequisites", "evidence_required", "stop_conditions", "fallback"
        }
        for row in action_rows:
            absent = required_action_fields - row.keys()
            if absent:
                errors.append(f"Action {row.get('id', '<unknown>')} missing: {sorted(absent)}")
        checks.append(f"continuity-actions:{len(action_rows)}")

    if checkpoint:
        baseline = as_object(checkpoint.get("source"), "checkpoint.source", errors).get("baseline_commit", "")
        if not isinstance(baseline, str) or not SHA40.fullmatch(baseline):
            errors.append("Checkpoint baseline_commit is not a 40-character SHA")
        if checkpoint.get("next_action_id") != current.get("primary_next_action_id"):
            errors.append("Checkpoint next action does not match current state")
        if not checkpoint.get("declared_non_coverage"):
            errors.append("Checkpoint must declare non-coverage")
        recovery = as_object(checkpoint.get("recovery"), "checkpoint.recovery", errors)
        if not recovery.get("first_safe_command") or not recovery.get("stop_if"):
            errors.append("Checkpoint recovery contract is incomplete")
        checks.append("checkpoint:linked")

    decision_ids: set[str] = set()
    decision_path = ROOT / "badf/decision-log.jsonl"
    if decision_path.is_file():
        try:
            decision_lines = decision_path.read_text(encoding="utf-8").splitlines()
        except (OSError, ValueError) as exc:
            errors.append(f"badf/decision-log.jsonl: cannot read: {exc}")
            decision_lines = []
        for number, line in enumerate(decision_lines, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"decision-log line {number}: {exc}")
                continue
            if not isinstance(row, dict):
                errors.append(
                    f"decision-log line {number}: expected an object, "
                    f"found {type(row).__name__}"
                )
                continue
            decision_id = row.get("id")
            if not isinstance(decision_id, str) or not decision_id:
                errors.append(f"decision-log line {number}: id must be a non-empty string")
                continue
            if decision_id in decision_ids:
                errors.append(f"decision-log line {number}: duplicate ID {decision_id}")
            decision_ids.add(decision_id)
        checks.append(f"decisions:{len(decision_ids)}")

    schemas_ok = True
    for schema in ("schemas/session-checkpoint.schema.json", "schemas/handoff.schema.json",
                   "schemas/current-state.schema.json", "schemas/next-actions.schema.json",
                   "schemas/decision-record.schema.json"):
        data = load_json(schema, errors)
        if not data:
            schemas_ok = False
        elif data.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append(f"{schema}: unsupported or missing JSON Schema dialect")
            schemas_ok = False
    if schemas_ok:
        checks.append("schemas:json-valid")

    skip_parts = {".git", "_site", "node_modules"}
    pages = sorted(
        page
        for page in ROOT.rglob("*.html")
        # is_file() matters: rglob matches a DIRECTORY named *.html too, and
        # read_text on one raises IsADirectoryError.
        if page.is_file() and not skip_parts.intersection(page.relative_to(ROOT).parts)
    )
    page_ids: dict[Path, set[str]] = {}
    page_refs: dict[Path, list[tuple[str, str]]] = {}
    readable: list[Path] = []
    for page in pages:
        try:
            source = page.read_text(encoding="utf-8")
        except (OSError, ValueError) as exc:
            errors.append(f"{page.relative_to(ROOT).as_posix()}: cannot read page: {exc}")
            continue
        parser = SiteParser()
        parser.feed(source)
        page_ids[page.resolve()] = parser.ids
        page_refs[page.resolve()] = parser.refs
        readable.append(page)
    pages = readable

    index_path = ROOT / "index.html"
    if not index_path.is_file():
        errors.append("index.html is not present at the publishing root")
    elif index_path.stat().st_size == 0:
        errors.append("index.html is present but empty")

    for page in pages:
        key = page.resolve()
        rel = page.relative_to(ROOT).as_posix()
        for tag, ref in page_refs[key]:
            if ref.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                continue
            try:
                parts = urlsplit(ref)
            except ValueError as exc:
                errors.append(f"{rel}: unparseable {tag} reference {ref!r}: {exc}")
                continue
            if not parts.path and parts.fragment:
                if parts.fragment not in page_ids[key]:
                    errors.append(f"{rel}: broken fragment #{parts.fragment}")
                continue
            if not parts.path:
                continue
            try:
                target = (page.parent / parts.path).resolve()
            except (OSError, ValueError) as exc:
                errors.append(f"{rel}: unusable {tag} path {parts.path!r}: {exc}")
                continue
            if ROOT not in target.parents and target != ROOT:
                errors.append(f"{rel}: {tag} reference escapes the site root: {parts.path}")
                continue
            if not target.exists():
                errors.append(f"{rel}: missing local {tag} reference {parts.path}")
                continue
            if parts.fragment and target.suffix == ".html":
                target_ids = page_ids.get(target)
                if target_ids is None:
                    errors.append(f"{rel}: cross-page fragment target not validated: {parts.path}")
                elif parts.fragment not in target_ids:
                    errors.append(
                        f"{rel}: broken cross-page fragment {parts.path}#{parts.fragment}"
                    )

    total_ids = sum(len(v) for v in page_ids.values())
    total_refs = sum(len(v) for v in page_refs.values())
    # Appended CONDITIONALLY. When this ran unconditionally the "check did not
    # run" assertion could never fire for it, and a site with every page
    # deleted and index.html truncated to zero bytes still printed PASS.
    if pages:
        checks.append(f"html-pages:{len(pages)}")
    else:
        errors.append("no readable HTML page found under the site root")
    if total_refs == 0:
        errors.append(
            "no local references found in any page: the link check validated nothing"
        )
    checks.append(f"html-ids:{total_ids}")
    checks.append(f"html-refs:{total_refs}")

    # Markdown links resolve too. Until this check existed only *.html was followed, and this
    # repository's normative documents are Markdown: 48 links in the P0 design pack pointed at
    # nothing from the day the pack was written, and survived a fresh-context review of all
    # fourteen designs, because a reader reads what a link says rather than where it goes (WP-101).
    # A fragment is resolved against the ids already parsed above when the target is a page, and
    # against the target's own headings when it is a document.
    # Anchored on "](" rather than on a link's label, because every link and image target in
    # Markdown is preceded by it and a label pattern cannot span the brackets of an image nested
    # inside a link: `[![badge](image)](target)` matched the image and dropped the target around it.
    markdown_link = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
    documents = sorted(
        document
        for document in ROOT.rglob("*.md")
        if document.is_file() and not skip_parts.intersection(document.relative_to(ROOT).parts)
    )
    document_headings: dict[Path, set[str]] = {}
    markdown_refs = 0
    for document in documents:
        try:
            source = document.read_text(encoding="utf-8")
        except (OSError, ValueError) as exc:
            errors.append(f"{document.relative_to(ROOT).as_posix()}: cannot read document: {exc}")
            continue
        document_headings[document] = markdown_headings(source)
        here = document.relative_to(ROOT).as_posix()
        for target in markdown_link.findall(source):
            split = urlsplit(target)
            if split.scheme or split.netloc:
                continue
            path, fragment = split.path, split.fragment
            markdown_refs += 1
            if path:
                try:
                    resolved = (document.parent / path).resolve()
                except (OSError, ValueError) as exc:
                    errors.append(f"{here}: cannot resolve link {target!r}: {exc}")
                    continue
                if not resolved.is_relative_to(ROOT):
                    errors.append(f"{here}: link leaves the repository: {target}")
                    continue
                if not resolved.exists():
                    errors.append(f"{here}: link resolves to nothing: {target}")
                    continue
            else:
                resolved = document
            if not fragment:
                continue
            if resolved.suffix == ".html":
                if resolved not in page_ids:
                    errors.append(f"{here}: link names a fragment of an unreadable page: {target}")
                elif fragment not in page_ids[resolved]:
                    errors.append(f"{here}: no id {fragment!r} in {resolved.relative_to(ROOT).as_posix()}: {target}")
            elif resolved.suffix == ".md":
                if resolved not in document_headings:
                    try:
                        document_headings[resolved] = markdown_headings(resolved.read_text(encoding="utf-8"))
                    except (OSError, ValueError) as exc:
                        errors.append(f"{here}: cannot read the document a link names: {exc}")
                        continue
                if fragment not in document_headings[resolved]:
                    errors.append(f"{here}: no heading {fragment!r} in {resolved.relative_to(ROOT).as_posix()}: {target}")
    if markdown_refs == 0:
        errors.append("no local link found in any Markdown document: the document link check validated nothing")
    checks.append(f"markdown-refs:{markdown_refs}")

    workflow_path = ROOT / ".github/workflows/pages.yml"
    if workflow_path.is_file():
        workflow = workflow_path.read_text(encoding="utf-8")
        # Each action must be USED and PINNED - but not pinned to a version this
        # file names. Asserting the literal string "actions/deploy-pages@v4" made
        # the check fail on every upgrade, so the only way to move to v5 was to
        # edit the check that exists to guard the workflow. A gate that makes
        # maintenance fail is a gate that gets deleted or worked around.
        #
        # A full commit SHA is accepted because that is GitHub's own hardening
        # recommendation; refusing it would push the workflow toward the weaker
        # of the two supported pinning styles.
        pinned = re.compile(r"^(?:v\d+(?:\.\d+)*|[0-9a-f]{40})$")
        for action in (
            "actions/checkout",
            "actions/configure-pages",
            "actions/upload-pages-artifact",
            "actions/deploy-pages",
        ):
            match = re.search(rf"uses:\s*{re.escape(action)}@(\S+)", workflow)
            if not match:
                errors.append(f"pages workflow does not use {action}")
            elif not pinned.fullmatch(match.group(1)):
                errors.append(
                    f"pages workflow pins {action} to {match.group(1)!r}: "
                    "expected a version tag such as v5, or a full 40-character commit SHA"
                )
        for token in (
            "pages: write",
            "id-token: write",
            "environment:",
            "github-pages",
        ):
            if token not in workflow:
                errors.append(f"pages workflow missing required token: {token}")
        checks.append("pages-workflow:baseline")

    # A PASS is only meaningful if the checks actually executed. Without this,
    # any guard that silently skips its block yields a clean verdict that
    # establishes nothing - the defect class this module exists to prevent.
    produced = {check.split(":", 1)[0] for check in checks}
    for expected in (
        "required-files", "continuity-actions", "checkpoint",
        "decisions", "schemas", "html-pages", "markdown-refs", "pages-workflow",
    ):
        if expected not in produced:
            errors.append(f"check did not run: {expected}")

    if errors:
        print("CONTINUITY_VALIDATION=FAIL")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("CONTINUITY_VALIDATION=PASS")
    for check in checks:
        print(f"PASS: {check}")
    print(f"RESUME_DECISION={current.get('resume_decision', 'UNKNOWN')}")
    print(f"PRIMARY_NEXT_ACTION={current.get('primary_next_action_id', 'UNKNOWN')}")
    # Step 8, beside the two lines an agent already reads at step 7, so it is seen without being
    # told to look. Printed here and not above the verdict because it is advisory: it is one of
    # four words about the RECORD, not a check that can fail.
    verdict, reason = reconcile_safely(ROOT, current)
    print(f"STATE_RECONCILIATION={verdict}")
    print(f"STATE_RECONCILIATION_REASON={reason}")
    return 0


def _emit_failure(exc: BaseException) -> None:
    """Print the verdict, then the diagnosis, without letting either raise.

    The verdict goes to stdout because that is the channel consumers grep.
    The traceback goes to stderr so it cannot corrupt that channel, and so a
    validator defect stays diagnosable - suppressing it entirely traded one
    silent failure for a less informative one.
    """
    try:
        print("CONTINUITY_VALIDATION=FAIL")
        print(f"ERROR: unexpected validator failure: {type(exc).__name__}: {exc}")
    except BaseException:  # noqa: BLE001 - a broken stdout must not hide the exit code
        pass
    try:
        traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
    except BaseException:  # noqa: BLE001
        pass


if __name__ == "__main__":
    try:
        # main() is called INSIDE the try and its result exits OUTSIDE it, so a
        # SystemExit raised within main() is caught here rather than escaping
        # with no verdict line at all.
        _code = main()
    except KeyboardInterrupt as exc:
        # An aborted run must not be recorded as a content failure.
        _emit_failure(exc)
        sys.exit(130)
    except BaseException as exc:  # noqa: BLE001 - fail closed, never fail open
        # Exit 2, not 1: a VALIDATOR defect and a DATA defect are different
        # facts, and a consumer that cannot tell them apart will debug the
        # wrong artifact.
        _emit_failure(exc)
        sys.exit(2)
    else:
        sys.exit(_code)

