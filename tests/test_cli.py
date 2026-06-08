from __future__ import annotations

import tomllib
from pathlib import Path

from agent_evolution.cli import main


def test_init_config_writes_privacy_safe_defaults(tmp_path: Path):
    config_path = tmp_path / "agent-evolution.toml"

    result = main(["init-config", "--path", str(config_path)])

    assert result == 0
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert config["privacy"]["store_raw_chats"] is False
    assert config["privacy"]["store_raw_evidence"] is False
    assert config["privacy"]["auto_modify_global_agent_files"] is False


def test_help_command_does_not_fail(capsys):
    result = main([])

    assert result == 0
    assert "Privacy-safe CLI" in capsys.readouterr().out
