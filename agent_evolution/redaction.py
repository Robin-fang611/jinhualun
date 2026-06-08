"""Privacy redaction helpers."""

from __future__ import annotations

import re


REDACTED_SECRET = "[REDACTED_SECRET]"
REDACTED_PATH = "[REDACTED_PATH]"
REDACTED_CODE = "[REDACTED_CODE]"

_SECRET_KEY_PATTERN = r"(?:api[_-]?key|private[_-]?key|password|token|secret|cookie)"
_SECRET_ASSIGNMENT_RE = re.compile(
    rf"(?P<key>\b{_SECRET_KEY_PATTERN}\b)"
    r"(?P<separator>\s*[:=]\s*)"
    r"(?P<value>\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s,;\r\n]+)",
    re.IGNORECASE,
)
_WINDOWS_USER_PATH_RE = re.compile(
    r'\b[A-Z]:\\Users\\[^\\/\s]+(?:\\[^\s<>"|?*,;)]*)*',
    re.IGNORECASE,
)
_MACOS_USER_PATH_RE = re.compile(r"(?<!\w)/Users/[^/\s]+(?:/[^\s<>\"']*)*")
_CODE_LABEL_PATTERN = (
    r"(?:\b(?:otp|verification\s+code|one[-\s]?time\s+password|code)\b"
    r"|验证码|校验码|动态码|一次性密码)"
)
_CODE_AFTER_LABEL_RE = re.compile(
    rf"(?P<label>{_CODE_LABEL_PATTERN}\s*[:：=]?\s*)"
    r"(?P<code>\d{4,8})(?=\b)",
    re.IGNORECASE,
)
_CODE_BEFORE_LABEL_RE = re.compile(
    rf"\b(?P<code>\d{{4,8}})"
    rf"(?P<label>\s*(?:is\s+your\s+)?{_CODE_LABEL_PATTERN})",
    re.IGNORECASE,
)
_RAW_EVIDENCE_RE = re.compile(r"\*\*原文证据\*\*|\braw\s+evidence\b", re.IGNORECASE)


def redact_text(text: str) -> str:
    redacted = _SECRET_ASSIGNMENT_RE.sub(_redact_secret_assignment, text)
    redacted = _WINDOWS_USER_PATH_RE.sub(REDACTED_PATH, redacted)
    redacted = _MACOS_USER_PATH_RE.sub(REDACTED_PATH, redacted)
    redacted = _CODE_AFTER_LABEL_RE.sub(
        lambda match: f"{match.group('label')}{REDACTED_CODE}",
        redacted,
    )
    redacted = _CODE_BEFORE_LABEL_RE.sub(
        lambda match: f"{REDACTED_CODE}{match.group('label')}",
        redacted,
    )
    return redacted


def contains_forbidden_content(text: str) -> bool:
    return (
        _RAW_EVIDENCE_RE.search(text) is not None
        or _contains_unredacted_secret(text)
        or _CODE_AFTER_LABEL_RE.search(text) is not None
        or _CODE_BEFORE_LABEL_RE.search(text) is not None
    )


def _redact_secret_assignment(match: re.Match[str]) -> str:
    return f"{match.group('key')}{match.group('separator')}{REDACTED_SECRET}"


def _contains_unredacted_secret(text: str) -> bool:
    for match in _SECRET_ASSIGNMENT_RE.finditer(text):
        value = match.group("value").strip("\"'")
        if value != REDACTED_SECRET:
            return True
    return False
