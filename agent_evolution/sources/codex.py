"""Codex JSONL history source adapter."""

from __future__ import annotations

from agent_evolution.models import Observation
from agent_evolution.sources.base import (
    JsonRecord,
    JsonlObservationSource,
    extract_content_text,
)


class CodexSource(JsonlObservationSource):
    source_type = "codex"

    def _observation_from_record(self, record: JsonRecord) -> Observation | None:
        if record.get("type") != "response_item":
            return None

        item = record.get("item")
        if not isinstance(item, dict) or item.get("role") != "user":
            return None

        text = extract_content_text(item.get("content"), allowed_types={"input_text"})
        return self._make_observation("user", text)
