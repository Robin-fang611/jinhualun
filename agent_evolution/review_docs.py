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
_DECLARED_COUNT_RE = re.compile(r"^建议数量：(?P<count>\d+)$")
_SUGGESTION_FIELD_RE = re.compile(r"^- (?P<label>[^：]+)：(?P<value>.*)$")
_NOTE_FIELD_RE = re.compile(r"^> - (?P<label>[^：]+)：(?P<value>.*)$")
_PLACEHOLDER_RE = re.compile(r"<[^>\r\n]+>")
_FIELD_BREAK_RE = re.compile(r"[\r\n\t]+")

_REQUIRED_SUGGESTION_FIELDS = (
    "建议作者",
    "建议时间",
    "目标对象",
    "风险等级",
    "进化建议",
)
_REQUIRED_NOTE_FIELDS = (
    "批注作者",
    "批注时间",
    "判断",
    "理由",
    "风险等级",
    "处理建议",
)


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
    declared_count = _declared_suggestion_count(lines)

    if not lines or not lines[0].startswith("# ") or not lines[0][2:].strip():
        errors.append("缺少 # 标题")

    has_author = any(
        line.startswith("作者：") and line.removeprefix("作者：").strip()
        for line in lines
    )
    if not has_author:
        errors.append("缺少作者")

    if declared_count is None:
        errors.append("缺少建议数量")

    if _PLACEHOLDER_RE.search(content):
        errors.append("包含未替换的模板占位符")

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

    if declared_count is not None and declared_count != len(suggestion_lines):
        errors.append(
            f"声明建议数 {declared_count} 与实际建议数 {len(suggestion_lines)} 不一致"
        )

    if not _suggestion_numbers_are_consecutive(suggestion_lines):
        errors.append("建议编号必须从 001 连续递增")

    for line_number, suggestion_number in suggestion_lines:
        next_content = _next_non_empty_line(lines, line_number + 1)
        if next_content is None or _NOTE_CALLOUT_RE.match(next_content[1]) is None:
            errors.append(f"建议 {suggestion_number} 后缺少紧跟的批注")
            note_line_number = None
        else:
            note_line_number = next_content[0]

        block_end = _next_suggestion_line_number(lines, line_number + 1)
        block_lines = lines[line_number + 1 : block_end]
        errors.extend(
            _missing_field_errors(
                f"建议 {suggestion_number}",
                block_lines,
                _SUGGESTION_FIELD_RE,
                _REQUIRED_SUGGESTION_FIELDS,
            )
        )

        if note_line_number is not None:
            note_match = _NOTE_CALLOUT_RE.match(lines[note_line_number])
            if note_match is not None and not note_match.group("author").strip():
                errors.append("批注作者缺失")
            errors.extend(
                _missing_field_errors(
                    f"批注 {suggestion_number}",
                    block_lines,
                    _NOTE_FIELD_RE,
                    _REQUIRED_NOTE_FIELDS,
                )
            )

    errors = list(dict.fromkeys(errors))
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
    return _FIELD_BREAK_RE.sub(" ", redact_text(str(value))).strip()


def _declared_suggestion_count(lines: list[str]) -> int | None:
    for line in lines:
        match = _DECLARED_COUNT_RE.match(line)
        if match:
            return int(match.group("count"))
    return None


def _suggestion_numbers_are_consecutive(
    suggestion_lines: list[tuple[int, str]],
) -> bool:
    actual_numbers = [int(number) for _, number in suggestion_lines]
    expected_numbers = list(range(1, len(suggestion_lines) + 1))
    return actual_numbers == expected_numbers


def _next_non_empty_line(
    lines: list[str],
    start_index: int,
) -> tuple[int, str] | None:
    for index, line in enumerate(lines[start_index:], start=start_index):
        if line.strip():
            return index, line
    return None


def _next_suggestion_line_number(lines: list[str], start_index: int) -> int:
    for index, line in enumerate(lines[start_index:], start=start_index):
        if _SUGGESTION_HEADING_RE.match(line):
            return index
    return len(lines)


def _missing_field_errors(
    prefix: str,
    lines: list[str],
    field_pattern: re.Pattern[str],
    required_fields: tuple[str, ...],
) -> list[str]:
    fields = _field_values(lines, field_pattern)
    missing_errors: list[str] = []
    for field in required_fields:
        if fields.get(field, "").strip():
            continue
        if field == "批注作者":
            missing_errors.append("批注作者缺失")
        else:
            missing_errors.append(f"{prefix} 缺少字段：{field}")
    return missing_errors


def _field_values(
    lines: list[str],
    field_pattern: re.Pattern[str],
) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in lines:
        match = field_pattern.match(line)
        if match:
            values[match.group("label")] = match.group("value")
    return values
