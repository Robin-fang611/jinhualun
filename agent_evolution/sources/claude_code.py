"""Claude Code JSONL history source adapter."""

from __future__ import annotations

from agent_evolution.models import Observation
from agent_evolution.sources.base import (
    JsonRecord,
    JsonlObservationSource,
    extract_content_text,
)


class ClaudeCodeSource(JsonlObservationSource):
    source_type = "claude-code"

    def _observation_from_record(self, record: JsonRecord) -> Observation | None:
        message = record.get("message")
        if not isinstance(message, dict) or message.get("role") != "user":
            return None

        text = extract_content_text(message.get("content"))
        return self._make_observation("user", text)
