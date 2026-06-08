"""TOML configuration loading and defaults."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from agent_evolution.models import (
    AppConfig,
    ModelConfig,
    PrivacyConfig,
    ScheduleConfig,
    SourceConfig,
    WorkspaceConfig,
)


DEFAULT_CONFIG_TOML = """# Agent Evolution Kit configuration

[workspace]
review_root = "./review"
snapshot_repo = "./snapshot-repo"
state_dir = "./state"

[models]
reflect_model = "deepseek-v4-pro"
review_model = "gpt-5.5"
base_url_env = "AGENT_EVOLUTION_BASE_URL"
api_key_env = "AGENT_EVOLUTION_API_KEY"

[privacy]
store_raw_messages = false
include_evidence_blocks = false
redact_local_paths = true
redact_private_contacts = true

[schedule]
interval_hours = 72
catch_up_on_boot = true

[[sources]]
name = "codex"
path = "~/.codex/sessions"
enabled = true

[[sources]]
name = "claude-code"
path = "~/.claude/projects"
enabled = true

[[sources]]
name = "generic-jsonl"
path = "./sample-history"
enabled = false
"""

DEFAULT_CONFIG_DATA = tomllib.loads(DEFAULT_CONFIG_TOML)


def load_config(path: str | Path) -> AppConfig:
    config_path = _normalize_config_path(path)
    user_config_data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    config_data = _overlay_config(DEFAULT_CONFIG_DATA, user_config_data)
    config_dir = config_path.parent

    workspace_data = config_data["workspace"]
    models_data = config_data["models"]
    privacy_data = config_data["privacy"]
    schedule_data = config_data["schedule"]
    sources_data = config_data["sources"]

    return AppConfig(
        workspace=WorkspaceConfig(
            review_root=_resolve_config_path(
                workspace_data["review_root"],
                config_dir,
            ),
            snapshot_repo=_resolve_config_path(
                workspace_data["snapshot_repo"],
                config_dir,
            ),
            state_dir=_resolve_config_path(
                workspace_data["state_dir"],
                config_dir,
            ),
        ),
        models=ModelConfig(
            reflect_model=models_data["reflect_model"],
            review_model=models_data["review_model"],
            base_url_env=models_data["base_url_env"],
            api_key_env=models_data["api_key_env"],
        ),
        privacy=PrivacyConfig(
            store_raw_messages=privacy_data["store_raw_messages"],
            include_evidence_blocks=privacy_data["include_evidence_blocks"],
            redact_local_paths=privacy_data["redact_local_paths"],
            redact_private_contacts=privacy_data["redact_private_contacts"],
        ),
        schedule=ScheduleConfig(
            interval_hours=schedule_data["interval_hours"],
            catch_up_on_boot=schedule_data["catch_up_on_boot"],
        ),
        sources=tuple(
            SourceConfig(
                name=source["name"],
                path=_resolve_config_path(source["path"], config_dir),
                enabled=source.get("enabled", True),
            )
            for source in sources_data
        ),
    )


def write_default_config(path: str | Path) -> None:
    config_path = Path(path).expanduser()
    config_path.write_text(DEFAULT_CONFIG_TOML, encoding="utf-8")


def _normalize_config_path(path: str | Path) -> Path:
    config_path = Path(path).expanduser()
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    return config_path.resolve(strict=False)


def _resolve_config_path(value: str | Path, config_dir: Path) -> Path:
    expanded_path = Path(value).expanduser()
    if not expanded_path.is_absolute():
        expanded_path = config_dir / expanded_path
    return expanded_path.resolve(strict=False)


def _overlay_config(
    defaults: dict[str, Any],
    overrides: dict[str, Any],
) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for key, value in defaults.items():
        if isinstance(value, dict):
            merged[key] = value.copy()
        elif isinstance(value, list):
            merged[key] = [
                item.copy() if isinstance(item, dict) else item
                for item in value
            ]
        else:
            merged[key] = value

    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value

    return merged
