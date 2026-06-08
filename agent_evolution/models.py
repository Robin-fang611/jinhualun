"""Configuration models for Agent Evolution Kit."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SourceConfig:
    name: str
    path: Path
    enabled: bool


@dataclass(frozen=True)
class WorkspaceConfig:
    review_root: Path = Path("./review")
    snapshot_repo: Path = Path("./snapshot-repo")
    state_dir: Path = Path("./state")


@dataclass(frozen=True)
class ModelConfig:
    reflect_model: str = "deepseek-v4-pro"
    review_model: str = "gpt-5.5"
    base_url_env: str = "AGENT_EVOLUTION_BASE_URL"
    api_key_env: str = "AGENT_EVOLUTION_API_KEY"


@dataclass(frozen=True)
class PrivacyConfig:
    store_raw_messages: bool = False
    include_evidence_blocks: bool = False
    redact_local_paths: bool = True
    redact_private_contacts: bool = True


@dataclass(frozen=True)
class ScheduleConfig:
    interval_hours: int = 72
    catch_up_on_boot: bool = True


@dataclass(frozen=True)
class AppConfig:
    workspace: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    sources: list[SourceConfig] = field(default_factory=list)
