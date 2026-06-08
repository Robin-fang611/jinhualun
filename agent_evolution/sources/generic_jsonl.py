"""Generic JSONL history source adapter."""

from __future__ import annotations

from agent_evolution.models import Observation
from agent_evolution.sources.base import (
    JsonRecord,
    JsonlObservationSource,
    extract_content_text,
)


class GenericJsonlSource(JsonlObservationSource):
    source_type = "generic-jsonl"

    def _observation_from_record(self, record: JsonRecord) -> Observation | None:
        role = record.get("role")
        if not isinstance(role, str):
            return None

        content = record.get("text") if "text" in record else record.get("content")
        text = extract_content_text(content)
        return self._make_observation(role, text)
