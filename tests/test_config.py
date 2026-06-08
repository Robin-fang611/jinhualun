from __future__ import annotations

import tomllib
from pathlib import Path
from uuid import uuid4

from agent_evolution.config import DEFAULT_CONFIG_TOML, load_config, write_default_config


def test_write_default_config_then_load_config():
    workspace = _test_workspace("default")
    config_path = workspace / "agent-evolution.toml"

    write_default_config(config_path)
    raw_config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    config = load_config(config_path)

    assert set(raw_config["privacy"]) == {
        "store_raw_messages",
        "include_evidence_blocks",
        "redact_local_paths",
        "redact_private_contacts",
    }
    assert config.workspace.review_root == workspace / "review"
    assert config.workspace.snapshot_repo == workspace / "snapshot-repo"
    assert config.workspace.state_dir == workspace / "state"
    assert config.models.reflect_model == "deepseek-v4-pro"
    assert config.models.review_model == "gpt-5.5"
    assert config.models.base_url_env == "AGENT_EVOLUTION_BASE_URL"
    assert config.models.api_key_env == "AGENT_EVOLUTION_API_KEY"
    assert config.privacy.store_raw_messages is False
    assert config.privacy.include_evidence_blocks is False
    assert config.privacy.redact_local_paths is True
    assert config.privacy.redact_private_contacts is True
    assert config.schedule.interval_hours == 72
    assert config.schedule.catch_up_on_boot is True
    assert isinstance(config.sources, tuple)
    assert [(source.name, source.path, source.enabled) for source in config.sources] == [
        ("codex", Path.home() / ".codex" / "sessions", True),
        ("claude-code", Path.home() / ".claude" / "projects", True),
        ("generic-jsonl", workspace / "sample-history", False),
    ]


def test_load_config_resolves_relative_paths_from_config_directory():
    workspace = _test_workspace("relative")
    config_dir = workspace / "nested"
    config_dir.mkdir()
    config_path = config_dir / "agent-evolution.toml"
    config_path.write_text(
        """
[workspace]
review_root = "local-review"
snapshot_repo = "../snapshots"
state_dir = "./local-state"

[[sources]]
name = "local"
path = "history"
enabled = true
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.workspace.review_root == config_dir / "local-review"
    assert config.workspace.snapshot_repo == workspace / "snapshots"
    assert config.workspace.state_dir == config_dir / "local-state"
    assert config.sources[0].path == config_dir / "history"


def test_load_config_expands_tilde_paths(monkeypatch):
    workspace = _test_workspace("tilde")
    home_dir = workspace / "home"
    monkeypatch.setenv("USERPROFILE", str(home_dir))
    monkeypatch.setenv("HOME", str(home_dir))
    config_path = workspace / "agent-evolution.toml"
    config_path.write_text(
        """
[workspace]
review_root = "~/reviews"
snapshot_repo = "~/snapshots"
state_dir = "~/state"

[[sources]]
name = "home-history"
path = "~/.agent-history"
enabled = true
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.workspace.review_root == home_dir / "reviews"
    assert config.workspace.snapshot_repo == home_dir / "snapshots"
    assert config.workspace.state_dir == home_dir / "state"
    assert config.sources[0].path == home_dir / ".agent-history"


def test_template_matches_default_config_toml():
    template_path = Path("templates") / "agent-evolution.toml"

    assert template_path.read_text(encoding="utf-8") == DEFAULT_CONFIG_TOML


def _test_workspace(name: str) -> Path:
    workspace = Path.cwd() / ".tmp" / "test-config" / f"{name}-{uuid4().hex}"
    workspace.mkdir(parents=True, exist_ok=False)
    return workspace
