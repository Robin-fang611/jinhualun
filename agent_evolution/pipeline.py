from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from agent_evolution.models import AppConfig, Observation, ReviewNote, Suggestion
from agent_evolution.review_docs import build_review_doc
from agent_evolution.sources import ClaudeCodeSource, CodexSource, GenericJsonlSource


@dataclass(frozen=True)
class ScanSummary:
    enabled_sources: int
    existing_sources: int
    observations: int


def collect_observations(config: AppConfig) -> tuple[Observation, ...]:
    observations: list[Observation] = []
    for source_config in config.sources:
        if not source_config.enabled or not source_config.path.exists():
            continue
        source = _source_for(source_config.name, source_config.path)
        observations.extend(source.iter_observations())
    return tuple(observations)


def scan(config: AppConfig) -> ScanSummary:
    enabled_sources = sum(1 for source in config.sources if source.enabled)
    existing_sources = sum(
        1 for source in config.sources if source.enabled and source.path.exists()
    )
    observations = collect_observations(config)
    return ScanSummary(
        enabled_sources=enabled_sources,
        existing_sources=existing_sources,
        observations=len(observations),
    )


def run(config: AppConfig) -> Path:
    observations = collect_observations(config)
    suggestions, notes = build_suggestions(observations)
    config.workspace.review_root.mkdir(parents=True, exist_ok=True)
    review_doc = config.workspace.review_root / "进化建议与批注.md"
    review_doc.write_text(
        build_review_doc("进化建议与批注", suggestions, notes),
        encoding="utf-8",
    )
    return review_doc


def build_suggestions(
    observations: tuple[Observation, ...],
) -> tuple[tuple[Suggestion, ...], tuple[ReviewNote, ...]]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    source_types = sorted({observation.source_type for observation in observations})
    if source_types:
        source_summary = "、".join(source_types)
        body = (
            f"本轮从 {len(observations)} 条脱敏观察中读取到 {source_summary} 来源；"
            "写入建议前继续保持只保存结论、不保存原文证据。"
        )
    else:
        body = "本轮没有读取到可用观察；建议先检查来源路径，再运行完整进化流程。"

    suggestion = Suggestion(
        title="先审阅再修改 agent 行为文件",
        author="Codex",
        created_at=now,
        target="Claude Code",
        risk_level="低",
        evolution_suggestion=body,
    )
    note = ReviewNote(
        author="Claude Code",
        created_at=now,
        judgment="采纳",
        reason="审阅优先可以降低误改全局配置和泄露原始历史的风险。",
        risk_level="低",
        handling_suggestion="保留为默认安全边界；后续修改全局文件前先生成审阅文档。",
    )
    return (suggestion,), (note,)


def _source_for(name: str, path: Path):
    if name == "codex":
        return CodexSource(path)
    if name == "claude-code":
        return ClaudeCodeSource(path)
    if name == "generic-jsonl":
        return GenericJsonlSource(path)
    raise ValueError(f"unsupported source type: {name}")
