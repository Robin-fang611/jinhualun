from __future__ import annotations

from agent_evolution.redaction import contains_forbidden_content, redact_text


def test_redact_text_replaces_secret_assignments():
    text = (
        "token=fake_token_value\n"
        "api_key: \"fake-api-key-value\"\n"
        "private_key='fake-private-key-value'\n"
        "password = fake-password-value\n"
        "cookie: fake_cookie_value"
    )

    redacted = redact_text(text)

    assert "token=[REDACTED_SECRET]" in redacted
    assert "api_key: [REDACTED_SECRET]" in redacted
    assert "private_key=[REDACTED_SECRET]" in redacted
    assert "password = [REDACTED_SECRET]" in redacted
    assert "cookie: [REDACTED_SECRET]" in redacted
    assert "fake" not in redacted


def test_redact_text_replaces_user_paths():
    text = (
        r"Windows path C:\Users\alice\project\notes.md "
        "and macOS path /Users/bob/project/notes.md"
    )

    redacted = redact_text(text)

    assert redacted.count("[REDACTED_PATH]") == 2
    assert "alice" not in redacted
    assert "bob" not in redacted


def test_redact_text_replaces_otp_codes_with_context_only():
    text = "OTP 123456, 验证码：9876, release year 2026"

    redacted = redact_text(text)

    assert "OTP [REDACTED_CODE]" in redacted
    assert "验证码：[REDACTED_CODE]" in redacted
    assert "123456" not in redacted
    assert "9876" not in redacted
    assert "release year 2026" in redacted


def test_contains_forbidden_content_detects_raw_evidence_markers():
    assert contains_forbidden_content("**原文证据**\nprivate text") is True
    assert contains_forbidden_content("Raw evidence: private text") is True


def test_contains_forbidden_content_detects_user_paths():
    assert contains_forbidden_content(r"C:\Users\alice\project") is True
    assert contains_forbidden_content("/Users/bob/project") is True


def test_contains_forbidden_content_detects_secrets_and_codes():
    assert contains_forbidden_content("secret=fake_secret_value") is True
    assert contains_forbidden_content("OTP 123456") is True
    assert contains_forbidden_content("验证码：9876") is True


def test_contains_forbidden_content_allows_sanitized_summary():
    text = "Summary uses [REDACTED_SECRET] and release year 2026."

    assert contains_forbidden_content(text) is False
