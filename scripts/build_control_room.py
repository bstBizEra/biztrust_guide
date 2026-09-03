#!/usr/bin/env python3
"""Build the BizTrust Delivery Control Room from governed Markdown sources.

The generated HTML is committed because GitHub Pages serves static files.  CI
runs this script with ``--check`` so Markdown remains the source of truth and a
hand-edited HTML copy cannot drift silently.

Only a deliberately small Markdown subset is supported.  Raw HTML is escaped,
links are scheme-checked, frontmatter is validated, and ambiguous source state
fails closed.  The implementation uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "docs" / "control-room"
DEFAULT_TEMPLATE = ROOT / "templates" / "control-room-shell.tpl"
DEFAULT_OUTPUT = ROOT / "stages" / "control-room.html"

REQUIRED_FIELDS = {
    "id",
    "title",
    "order",
    "kind",
    "status",
    "owner",
    "updated",
    "source",
}
ALLOWED_KINDS = {
    "execution",
    "planning",
    "governance",
    "assurance",
    "continuity",
    "research",
}
ALLOWED_STATUSES = {
    "DRAFT",
    "READY",
    "AUTHORIZED",
    "IN_PROGRESS",
    "IN_REVIEW",
    "VALIDATING",
    "ENGINEERING_READY",
    "ACCEPTED",
    "CLOSED",
    "BLOCKED",
    "WAIT_FOR_AUTHORITY",
    "RECOVERY_REQUIRED",
    "QUEUED",
    "COMPLETE",
    "CURRENT",
}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{1,48}$")
TABLE_DIVIDER = re.compile(r"^\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?$")
LIST_ITEM = re.compile(r"^\s*[-*]\s+(.+)$")
ORDERED_ITEM = re.compile(r"^\s*\d+[.)]\s+(.+)$")
HEADING = re.compile(r"^(#{1,5})\s+(.+)$")
INLINE_TOKEN = re.compile(r"(`[^`\n]+`|\[[^\]\n]+\]\([^\s)]+\))")
LINK_TOKEN = re.compile(r"^\[([^\]]+)\]\(([^\s)]+)\)$")


class ControlRoomError(ValueError):
    """A source-contract or rendering error that must stop generation."""


@dataclass(frozen=True)
class Section:
    path: Path
    metadata: dict[str, object]
    body: str

    @property
    def id(self) -> str:
        return str(self.metadata["id"])

    @property
    def title(self) -> str:
        return str(self.metadata["title"])

    @property
    def order(self) -> int:
        return int(self.metadata["order"])


def parse_scalar(raw: str) -> object:
    value = raw.strip()
    if not value:
        return ""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if re.fullmatch(r"\d+", value):
        return int(value)
    return value


def parse_frontmatter(path: Path) -> Section:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ControlRoomError(f"{path}: missing opening frontmatter delimiter")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration as exc:
        raise ControlRoomError(f"{path}: missing closing frontmatter delimiter") from exc

    metadata: dict[str, object] = {}
    for line_number, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ControlRoomError(f"{path}:{line_number}: expected key: value")
        key, value = line.split(":", 1)
        key = key.strip()
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key):
            raise ControlRoomError(f"{path}:{line_number}: invalid frontmatter key {key!r}")
        if key in metadata:
            raise ControlRoomError(f"{path}:{line_number}: duplicate frontmatter key {key!r}")
        metadata[key] = parse_scalar(value)

    missing = sorted(REQUIRED_FIELDS - metadata.keys())
    if missing:
        raise ControlRoomError(f"{path}: missing required frontmatter: {', '.join(missing)}")
    unknown = sorted(set(metadata) - REQUIRED_FIELDS - {
        "summary",
        "primary",
        "primary_action",
        "work_package",
        "architecture_state",
        "active_slice",
        "evidence",
        "snapshot_at",
        "refresh_by",
    })
    if unknown:
        raise ControlRoomError(f"{path}: unsupported frontmatter: {', '.join(unknown)}")

    section_id = metadata["id"]
    if not isinstance(section_id, str) or not ID_PATTERN.fullmatch(section_id):
        raise ControlRoomError(f"{path}: id must match {ID_PATTERN.pattern}")
    if not isinstance(metadata["title"], str) or not str(metadata["title"]).strip():
        raise ControlRoomError(f"{path}: title must be non-empty text")
    if not isinstance(metadata["order"], int) or int(metadata["order"]) <= 0:
        raise ControlRoomError(f"{path}: order must be a positive integer")
    if metadata["kind"] not in ALLOWED_KINDS:
        raise ControlRoomError(f"{path}: unsupported kind {metadata['kind']!r}")
    if metadata["status"] not in ALLOWED_STATUSES:
        raise ControlRoomError(f"{path}: unsupported status {metadata['status']!r}")
    if not isinstance(metadata["owner"], str) or not str(metadata["owner"]).strip():
        raise ControlRoomError(f"{path}: owner must be non-empty text")
    if metadata.get("primary") not in {None, True, False}:
        raise ControlRoomError(f"{path}: primary must be true or false")

    validate_date(str(metadata["updated"]), f"{path}: updated")
    validate_href(str(metadata["source"]), f"{path}: source", external_required=True)
    for field in ("snapshot_at", "refresh_by"):
        if field in metadata:
            validate_datetime(str(metadata[field]), f"{path}: {field}")
    if metadata.get("primary") is True and not str(metadata.get("primary_action", "")).strip():
        raise ControlRoomError(f"{path}: primary section requires primary_action")

    body = "\n".join(lines[end + 1 :]).strip()
    if not body:
        raise ControlRoomError(f"{path}: Markdown body is empty")
    return Section(path=path, metadata=metadata, body=body)


def validate_date(value: str, context: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ControlRoomError(f"{context} must be ISO 8601 YYYY-MM-DD") from exc


def validate_datetime(value: str, context: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ControlRoomError(f"{context} must be an RFC 3339 timestamp") from exc
    if parsed.tzinfo is None:
        raise ControlRoomError(f"{context} must include a timezone offset")


def validate_href(value: str, context: str, *, external_required: bool = False) -> str:
    if not value or any(char in value for char in "\r\n\t"):
        raise ControlRoomError(f"{context}: empty or malformed link")
    parsed = urlsplit(value)
    if external_required and parsed.scheme not in {"https", "http"}:
        raise ControlRoomError(f"{context}: expected an HTTP(S) source link")
    if parsed.scheme and parsed.scheme not in {"https", "http"}:
        raise ControlRoomError(f"{context}: unsafe link scheme {parsed.scheme!r}")
    if not parsed.scheme and (value.startswith("//") or "\\" in value):
        raise ControlRoomError(f"{context}: unsafe relative link")
    return value


def format_plain(text: str) -> str:
    escaped = html.escape(text, quote=True)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def render_inline(text: str) -> str:
    output: list[str] = []
    position = 0
    for match in INLINE_TOKEN.finditer(text):
        output.append(format_plain(text[position : match.start()]))
        token = match.group(0)
        if token.startswith("`"):
            output.append(f"<code>{html.escape(token[1:-1], quote=True)}</code>")
        else:
            link = LINK_TOKEN.fullmatch(token)
            if link is None:  # pragma: no cover - constrained by INLINE_TOKEN
                raise ControlRoomError(f"cannot parse link token: {token}")
            label, href = link.groups()
            validate_href(href, f"Markdown link {label!r}")
            external = urlsplit(href).scheme in {"http", "https"}
            attrs = ' target="_blank" rel="noopener noreferrer"' if external else ""
            output.append(
                f'<a href="{html.escape(href, quote=True)}"{attrs}>{format_plain(label)}</a>'
            )
        position = match.end()
    output.append(format_plain(text[position:]))
    return "".join(output)


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def slugify(value: str) -> str:
    value = re.sub(r"`([^`]+)`", r"\1", value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "section"


def markdown_to_html(markdown: str, section_id: str = "content") -> str:
    lines = markdown.splitlines()
    rendered: list[str] = []
    heading_ids: set[str] = set()
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            language = stripped[3:].strip()
            if language and not re.fullmatch(r"[a-zA-Z0-9_-]+", language):
                raise ControlRoomError(f"invalid fenced-code language {language!r}")
            i += 1
            code: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            if i >= len(lines):
                raise ControlRoomError("unclosed fenced code block")
            klass = f' class="language-{language}"' if language else ""
            rendered.append(f"<pre><code{klass}>{html.escape(chr(10).join(code))}</code></pre>")
            i += 1
            continue

        heading = HEADING.match(stripped)
        if heading:
            markdown_level = len(heading.group(1))
            level = min(6, markdown_level + 2)
            text = heading.group(2).strip()
            base = f"{section_id}-{slugify(text)}"
            heading_id = base
            suffix = 2
            while heading_id in heading_ids:
                heading_id = f"{base}-{suffix}"
                suffix += 1
            heading_ids.add(heading_id)
            rendered.append(f'<h{level} id="{heading_id}">{render_inline(text)}</h{level}>')
            i += 1
            continue

        if stripped.startswith(">"):
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].lstrip())
                i += 1
            rendered.append(f"<blockquote><p>{render_inline(' '.join(quote))}</p></blockquote>")
            continue

        if (
            stripped.startswith("|")
            and i + 1 < len(lines)
            and TABLE_DIVIDER.fullmatch(lines[i + 1].strip())
        ):
            headers = split_table_row(lines[i])
            i += 2
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = split_table_row(lines[i])
                if len(row) != len(headers):
                    raise ControlRoomError("Markdown table row has a different column count")
                rows.append(row)
                i += 1
            head = "".join(f"<th scope=\"col\">{render_inline(cell)}</th>" for cell in headers)
            body = "".join(
                "<tr>" + "".join(f"<td>{render_inline(cell)}</td>" for cell in row) + "</tr>"
                for row in rows
            )
            rendered.append(
                '<div class="cr-table-wrap"><table><thead><tr>'
                + head
                + "</tr></thead><tbody>"
                + body
                + "</tbody></table></div>"
            )
            continue

        unordered = LIST_ITEM.match(line)
        if unordered:
            items: list[str] = []
            while i < len(lines):
                item_match = LIST_ITEM.match(lines[i])
                if item_match is None:
                    break
                item = item_match.group(1)
                task = re.match(r"^\[([ xX])\]\s+(.+)$", item)
                if task:
                    checked = " checked" if task.group(1).lower() == "x" else ""
                    items.append(
                        f'<li class="cr-task"><input type="checkbox" disabled{checked} '
                        f'aria-label="Task status"> <span>{render_inline(task.group(2))}</span></li>'
                    )
                else:
                    items.append(f"<li>{render_inline(item)}</li>")
                i += 1
            rendered.append("<ul>" + "".join(items) + "</ul>")
            continue

        ordered = ORDERED_ITEM.match(line)
        if ordered:
            items = []
            while i < len(lines):
                item_match = ORDERED_ITEM.match(lines[i])
                if item_match is None:
                    break
                items.append(f"<li>{render_inline(item_match.group(1))}</li>")
                i += 1
            rendered.append("<ol>" + "".join(items) + "</ol>")
            continue

        paragraph = [stripped]
        i += 1
        while i < len(lines):
            candidate = lines[i]
            candidate_stripped = candidate.strip()
            if not candidate_stripped:
                break
            if (
                candidate_stripped.startswith(("```", ">", "|"))
                or HEADING.match(candidate_stripped)
                or LIST_ITEM.match(candidate)
                or ORDERED_ITEM.match(candidate)
            ):
                break
            paragraph.append(candidate_stripped)
            i += 1
        rendered.append(f"<p>{render_inline(' '.join(paragraph))}</p>")

    return "\n".join(rendered)


def load_sections(source_dir: Path) -> list[Section]:
    paths = sorted(path for path in source_dir.glob("*.md") if path.name.lower() != "readme.md")
    if not paths:
        raise ControlRoomError(f"{source_dir}: no registered Markdown sections")
    sections = [parse_frontmatter(path) for path in paths]

    ids = [section.id for section in sections]
    duplicate_ids = sorted({value for value in ids if ids.count(value) > 1})
    if duplicate_ids:
        raise ControlRoomError(f"duplicate section id(s): {', '.join(duplicate_ids)}")
    orders = [section.order for section in sections]
    duplicate_orders = sorted({value for value in orders if orders.count(value) > 1})
    if duplicate_orders:
        raise ControlRoomError(f"duplicate section order(s): {duplicate_orders}")
    primary = [section for section in sections if section.metadata.get("primary") is True]
    if len(primary) != 1:
        raise ControlRoomError(f"expected exactly one primary section; found {len(primary)}")
    if "session" not in ids:
        raise ControlRoomError("required section id 'session' is missing")
    return sorted(sections, key=lambda section: section.order)


def badge_class(status: str) -> str:
    if status in {"ACCEPTED", "CLOSED", "COMPLETE", "CURRENT"}:
        return "is-positive"
    if status in {"BLOCKED", "RECOVERY_REQUIRED"}:
        return "is-negative"
    if status in {"WAIT_FOR_AUTHORITY", "QUEUED", "DRAFT"}:
        return "is-warning"
    return "is-active"


def source_digest(sections: list[Section]) -> str:
    digest = hashlib.sha256()
    for section in sections:
        digest.update(section.path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(section.path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def build_control_room(source_dir: Path, template_path: Path) -> str:
    sections = load_sections(source_dir)
    session = next(section for section in sections if section.id == "session")
    primary = next(section for section in sections if section.metadata.get("primary") is True)
    template = template_path.read_text(encoding="utf-8")

    navigation: list[str] = []
    panels: list[str] = []
    page_data: list[dict[str, object]] = []
    repository_blob = "https://github.com/bstBizEra/biztrust_guide/blob/main/"

    for section in sections:
        metadata = section.metadata
        status = str(metadata["status"])
        kind = str(metadata["kind"])
        refresh = str(metadata.get("refresh_by", ""))
        source = str(metadata["source"])
        try:
            repository_path = section.path.resolve().relative_to(ROOT)
        except ValueError:
            # Custom source directories are useful for fail-closed tests and
            # previews. Their files have no stable repository URL, so point
            # the secondary evidence link at the already-validated record.
            markdown_href = source
        else:
            markdown_href = repository_blob + repository_path.as_posix()
        navigation.append(
            f'<a href="#{section.id}" data-nav-kind="{html.escape(kind, quote=True)}">'
            f'<span>{section.order:02d}</span><strong>{html.escape(section.title)}</strong>'
            f'<small>{html.escape(status.replace("_", " ").title())}</small></a>'
        )
        meta_bits = [
            f'<span class="cr-status {badge_class(status)}">{html.escape(status)}</span>',
            f'<span>Owner · {html.escape(str(metadata["owner"]))}</span>',
            f'<span>Updated · <time datetime="{html.escape(str(metadata["updated"]), quote=True)}">'
            f'{html.escape(str(metadata["updated"]))}</time></span>',
        ]
        panels.append(
            f'<section class="cr-panel" id="{section.id}" data-kind="{html.escape(kind, quote=True)}" '
            f'data-status="{html.escape(status, quote=True)}" data-refresh-by="{html.escape(refresh, quote=True)}">'
            '<header class="cr-panel-head"><div>'
            f'<p class="cr-eyebrow">{section.order:02d} · {html.escape(kind.upper())}</p>'
            f'<h2>{html.escape(section.title)}</h2>'
            f'<p class="cr-summary-copy">{html.escape(str(metadata.get("summary", "")))}</p>'
            '</div><div class="cr-source-links">'
            f'<a href="{html.escape(source, quote=True)}" target="_blank" rel="noopener noreferrer">Record ↗</a>'
            f'<a href="{html.escape(markdown_href, quote=True)}" target="_blank" rel="noopener noreferrer">Markdown ↗</a>'
            '</div></header>'
            f'<div class="cr-meta">{"".join(meta_bits)}</div>'
            f'<div class="cr-markdown">{markdown_to_html(section.body, section.id)}</div>'
            '</section>'
        )
        page_data.append(
            {
                "id": section.id,
                "title": section.title,
                "kind": kind,
                "status": status,
                "refresh_by": refresh or None,
            }
        )

    replacements = {
        "@@NAVIGATION@@": "\n".join(navigation),
        "@@PANELS@@": "\n".join(panels),
        "@@PAGE_DATA@@": json.dumps(page_data, ensure_ascii=False).replace("<", "\\u003c"),
        "@@SOURCE_DIGEST@@": source_digest(sections),
        "@@SOURCE_COUNT@@": str(len(sections)),
        "@@WORK_PACKAGE@@": html.escape(str(session.metadata.get("work_package", "UNRECORDED"))),
        "@@DELIVERY_STATUS@@": html.escape(str(session.metadata["status"])),
        "@@DELIVERY_STATUS_CLASS@@": badge_class(str(session.metadata["status"])),
        "@@ARCHITECTURE_STATE@@": html.escape(str(session.metadata.get("architecture_state", "UNRECORDED"))),
        "@@ACTIVE_SLICE@@": html.escape(str(session.metadata.get("active_slice", "UNRECORDED"))),
        "@@PRIMARY_ACTION@@": html.escape(str(primary.metadata.get("primary_action", "UNRECORDED"))),
        "@@EVIDENCE@@": html.escape(str(session.metadata.get("evidence", "UNRECORDED"))),
        "@@SNAPSHOT_AT@@": html.escape(str(session.metadata.get("snapshot_at", session.metadata["updated"])), quote=True),
        "@@REFRESH_BY@@": html.escape(str(session.metadata.get("refresh_by", "")), quote=True),
        "@@UPDATED@@": html.escape(str(session.metadata["updated"])),
    }
    generated = template
    for token, value in replacements.items():
        if token not in generated:
            raise ControlRoomError(f"template is missing token {token}")
        generated = generated.replace(token, value)
    leftovers = sorted(set(re.findall(r"@@[A-Z_]+@@", generated)))
    if leftovers:
        raise ControlRoomError(f"unresolved template tokens: {', '.join(leftovers)}")
    return generated.rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="Fail if generated output differs")
    args = parser.parse_args(argv)

    try:
        generated = build_control_room(args.source_dir.resolve(), args.template.resolve())
    except (ControlRoomError, OSError) as exc:
        print(f"CONTROL_ROOM_BUILD=FAIL\n{exc}")
        return 1

    output = args.output.resolve()
    if args.check:
        if not output.is_file():
            print(f"CONTROL_ROOM_BUILD=FAIL\nmissing generated file: {output}")
            return 1
        if output.read_text(encoding="utf-8") != generated:
            print("CONTROL_ROOM_BUILD=FAIL\ngenerated HTML is stale; run scripts/build_control_room.py")
            return 1
        print("CONTROL_ROOM_BUILD=PASS")
        return 0

    output.write_text(generated, encoding="utf-8")
    print(f"CONTROL_ROOM_BUILD=UPDATED sections={len(load_sections(args.source_dir.resolve()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
