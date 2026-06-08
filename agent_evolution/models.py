"""Configuration models for Agent Evolution Kit."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceConfig:
    name: str
    path: Path
    enabled: bool


@dataclass(frozen=True)
class Observation:
    source_type: str
    role: str
    text: str


@dataclass(frozen=True)
class WorkspaceConfig:
    review_root: Path
    snapshot_repo: Path
    state_dir: Path


@dataclass(frozen=True)
class ModelConfig:
    reflect_model: str
    review_model: str
    base_url_env: str
    api_key_env: str


@dataclass(frozen=True)
class PrivacyConfig:
    store_raw_messages: bool
    include_evidence_blocks: bool
    redact_local_paths: bool
    redact_private_contacts: bool


@dataclass(frozen=True)
class ScheduleConfig:
    interval_hours: int
    catch_up_on_boot: bool


@dataclass(frozen=True)
class AppConfig:
    workspace: WorkspaceConfig
    models: ModelConfig
    privacy: PrivacyConfig
    schedule: ScheduleConfig
    sources: tuple[SourceConfig, ...]
