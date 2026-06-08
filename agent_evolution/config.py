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
store_raw_chats = false
store_raw_evidence = false
auto_modify_global_agent_files = false

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


def load_config(path: str | Path) -> AppConfig:
    config_path = _normalize_config_path(path)
    config_data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    config_dir = config_path.parent

    workspace_data = config_data.get("workspace", {})
    models_data = config_data.get("models", {})
    privacy_data = config_data.get("privacy", {})
    schedule_data = config_data.get("schedule", {})
    sources_data = config_data.get("sources", _default_sources_data())

    return AppConfig(
        workspace=WorkspaceConfig(
            review_root=_resolve_config_path(
                workspace_data.get("review_root", "./review"),
                config_dir,
            ),
            snapshot_repo=_resolve_config_path(
                workspace_data.get("snapshot_repo", "./snapshot-repo"),
                config_dir,
            ),
            state_dir=_resolve_config_path(
                workspace_data.get("state_dir", "./state"),
                config_dir,
            ),
        ),
        models=ModelConfig(
            reflect_model=models_data.get("reflect_model", "deepseek-v4-pro"),
            review_model=models_data.get("review_model", "gpt-5.5"),
            base_url_env=models_data.get(
                "base_url_env",
                "AGENT_EVOLUTION_BASE_URL",
            ),
            api_key_env=models_data.get(
                "api_key_env",
                "AGENT_EVOLUTION_API_KEY",
            ),
        ),
        privacy=PrivacyConfig(
            store_raw_messages=privacy_data.get("store_raw_messages", False),
            include_evidence_blocks=privacy_data.get("include_evidence_blocks", False),
            redact_local_paths=privacy_data.get("redact_local_paths", True),
            redact_private_contacts=privacy_data.get("redact_private_contacts", True),
        ),
        schedule=ScheduleConfig(
            interval_hours=schedule_data.get("interval_hours", 72),
            catch_up_on_boot=schedule_data.get("catch_up_on_boot", True),
        ),
        sources=[
            SourceConfig(
                name=source["name"],
                path=_resolve_config_path(source["path"], config_dir),
                enabled=source.get("enabled", True),
            )
            for source in sources_data
        ],
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


def _default_sources_data() -> list[dict[str, Any]]:
    return [
        {
            "name": "codex",
            "path": "~/.codex/sessions",
            "enabled": True,
        },
        {
            "name": "claude-code",
            "path": "~/.claude/projects",
            "enabled": True,
        },
        {
            "name": "generic-jsonl",
            "path": "./sample-history",
            "enabled": False,
        },
    ]
