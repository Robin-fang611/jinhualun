"""Shared JSONL source adapter utilities."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path
from typing import Any, ClassVar

from agent_evolution.models import Observation

JsonRecord = dict[str, Any]


def iter_jsonl(path: str | Path) -> Iterator[JsonRecord]:
    jsonl_path = Path(path)
    if not jsonl_path.is_file():
        return

    with jsonl_path.open(encoding="utf-8", errors="replace") as jsonl_file:
        for raw_line in jsonl_file:
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                yield record


def iter_jsonl_files(path: str | Path) -> Iterator[Path]:
    source_path = Path(path)
    if source_path.is_file():
        if source_path.suffix.lower() == ".jsonl":
            yield source_path
        return

    if source_path.is_dir():
        yield from sorted(source_path.rglob("*.jsonl"), key=lambda file: str(file))


class JsonlObservationSource(ABC):
    source_type: ClassVar[str]

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def observations(self) -> Iterator[Observation]:
        for jsonl_file in iter_jsonl_files(self.path):
            for record in iter_jsonl(jsonl_file):
                observation = self._observation_from_record(record)
                if observation is not None:
                    yield observation

    def iter_observations(self) -> Iterator[Observation]:
        yield from self.observations()

    @abstractmethod
    def _observation_from_record(self, record: JsonRecord) -> Observation | None:
        raise NotImplementedError

    def _make_observation(self, role: str, text: str | None) -> Observation | None:
        clean_role = role.strip()
        clean_text = text.strip() if isinstance(text, str) else ""
        if not clean_role or not clean_text:
            return None
        return Observation(
            source_type=self.source_type,
            role=clean_role,
            text=clean_text,
        )


def extract_content_text(
    content: Any,
    *,
    allowed_types: set[str] | None = None,
) -> str | None:
    if isinstance(content, str):
        return content

    if not isinstance(content, list):
        return None

    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if allowed_types is not None and item.get("type") not in allowed_types:
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())

    if not parts:
        return None
    return "\n".join(parts)
