from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from agent_evolution.models import Observation
from agent_evolution.sources import ClaudeCodeSource, CodexSource, GenericJsonlSource
from agent_evolution.sources.base import iter_jsonl, iter_jsonl_files


FIXTURES = Path(__file__).parent / "fixtures"


def test_codex_source_extracts_user_input_text_and_string_content():
    observations = list(CodexSource(FIXTURES / "codex-session.jsonl").observations())

    assert observations == [
        Observation(source_type="codex", role="user", text="Codex input text"),
        Observation(source_type="codex", role="user", text="Codex string content"),
    ]


def test_claude_code_source_extracts_user_string_and_list_content():
    observations = list(
        ClaudeCodeSource(FIXTURES / "claude-code-session.jsonl").observations()
    )

    assert observations == [
        Observation(source_type="claude-code", role="user", text="Claude string content"),
        Observation(source_type="claude-code", role="user", text="Claude list content"),
    ]


def test_generic_jsonl_source_extracts_text_or_content_and_skips_bad_lines():
    records = list(iter_jsonl(FIXTURES / "generic.jsonl"))
    observations = list(GenericJsonlSource(FIXTURES / "generic.jsonl").observations())

    assert len(records) == 4
    assert observations == [
        Observation(source_type="generic-jsonl", role="user", text="Generic text content"),
        Observation(source_type="generic-jsonl", role="user", text="Generic content field"),
    ]


def test_iter_jsonl_files_accepts_a_file_or_recursive_directory():
    workspace = Path.cwd() / ".tmp" / "test-sources" / uuid4().hex
    nested = workspace / "nested"
    nested.mkdir(parents=True, exist_ok=False)
    first_file = workspace / "first.jsonl"
    second_file = nested / "second.jsonl"
    ignored_file = nested / "ignored.txt"
    first_file.write_text('{"role":"user","text":"first"}\n', encoding="utf-8")
    second_file.write_text('{"role":"user","text":"second"}\n', encoding="utf-8")
    ignored_file.write_text('{"role":"user","text":"ignored"}\n', encoding="utf-8")

    assert list(iter_jsonl_files(first_file)) == [first_file]
    assert list(iter_jsonl_files(workspace)) == [first_file, second_file]
