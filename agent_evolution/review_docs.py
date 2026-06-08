"""Markdown review document generation and validation."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import zip_longest

from agent_evolution.models import ReviewNote, Suggestion
from agent_evolution.redaction import contains_forbidden_content, redact_text

DOCUMENT_AUTHOR = "Agent Evolution Kit"

_SUGGESTION_HEADING_RE = re.compile(r"^## 建议 (?P<number>\d{3})：(?P<title>.*)$")
_NOTE_CALLOUT_RE = re.compile(r"^> \[!note\]\s*(?P<author>.*?)\s*批注\s*$")
_NOTE_AUTHOR_FIELD_RE = re.compile(r"^> - 批注作者：(?P<author>.*)$")


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: list[str]


def build_review_doc(
    title: str,
    suggestions: Iterable[Suggestion],
    notes: Iterable[ReviewNote],
) -> str:
    suggestion_items = tuple(suggestions)
    note_items = tuple(notes)
    lines = [
        f"# {_safe(title)}",
        f"作者：{DOCUMENT_AUTHOR}",
        f"建议数量：{len(suggestion_items)}",
        "",
    ]

    for index, (suggestion, note) in enumerate(
        zip_longest(suggestion_items, note_items),
        start=1,
    ):
        if suggestion is None and note is not None:
            lines.extend(_render_note(note))
            lines.append("")
            continue

        if suggestion is None:
            continue

        lines.append(f"## 建议 {index:03d}：{_safe(suggestion.title)}")
        if note is not None:
            lines.extend(_render_note(note))
        lines.extend(_render_suggestion(suggestion))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def validate_review_doc(content: str) -> ValidationResult:
    errors: list[str] = []
    lines = content.splitlines()
    suggestion_lines: list[tuple[int, str]] = []
    note_lines: list[tuple[int, str]] = []

    if contains_forbidden_content(content):
        errors.append("包含禁止写出的原文证据或敏感内容")

    for line_number, line in enumerate(lines):
        suggestion_match = _SUGGESTION_HEADING_RE.match(line)
        if suggestion_match:
            suggestion_lines.append((line_number, suggestion_match.group("number")))

        note_match = _NOTE_CALLOUT_RE.match(line)
        if note_match:
            note_lines.append((line_number, note_match.group("author").strip()))

    if len(suggestion_lines) != len(note_lines):
        errors.append(
            f"建议数 {len(suggestion_lines)} 与批注数 {len(note_lines)} 不一致"
        )

    for line_number, suggestion_number in suggestion_lines:
        next_content_line = _next_non_empty_line(lines, line_number + 1)
        if next_content_line is None or _NOTE_CALLOUT_RE.match(next_content_line) is None:
            errors.append(f"建议 {suggestion_number} 后缺少紧跟的批注")

    errors.extend(_validate_note_authors(lines, note_lines))

    return ValidationResult(is_valid=not errors, errors=errors)


def _render_suggestion(suggestion: Suggestion) -> list[str]:
    return [
        f"- 建议作者：{_safe(suggestion.author)}",
        f"- 建议时间：{_safe(suggestion.created_at)}",
        f"- 目标对象：{_safe(suggestion.target)}",
        f"- 风险等级：{_safe(suggestion.risk_level)}",
        f"- 进化建议：{_safe(suggestion.evolution_suggestion)}",
    ]


def _render_note(note: ReviewNote) -> list[str]:
    return [
        f"> [!note] {_safe(note.author)} 批注",
        f"> - 批注作者：{_safe(note.author)}",
        f"> - 批注时间：{_safe(note.created_at)}",
        f"> - 判断：{_safe(note.judgment)}",
        f"> - 理由：{_safe(note.reason)}",
        f"> - 风险等级：{_safe(note.risk_level)}",
        f"> - 处理建议：{_safe(note.handling_suggestion)}",
    ]


def _safe(value: object) -> str:
    return redact_text(str(value))


def _next_non_empty_line(lines: list[str], start_index: int) -> str | None:
    for line in lines[start_index:]:
        if line.strip():
            return line
    return None


def _validate_note_authors(
    lines: list[str],
    note_lines: list[tuple[int, str]],
) -> list[str]:
    errors: list[str] = []
    for line_number, callout_author in note_lines:
        if not callout_author:
            errors.append("批注作者缺失")
            continue

        author_field = _find_note_author_field(lines, line_number + 1)
        if author_field is None or not author_field.strip():
            errors.append("批注作者缺失")

    return errors


def _find_note_author_field(lines: list[str], start_index: int) -> str | None:
    for line in lines[start_index:]:
        if _SUGGESTION_HEADING_RE.match(line) or _NOTE_CALLOUT_RE.match(line):
            return None
        author_match = _NOTE_AUTHOR_FIELD_RE.match(line)
        if author_match:
            return author_match.group("author")
    return None
