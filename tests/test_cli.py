from __future__ import annotations

import tomllib
from pathlib import Path
from uuid import uuid4

from agent_evolution.cli import main


def test_init_config_writes_privacy_safe_defaults():
    workspace = _test_workspace("cli-init")
    config_path = workspace / "agent-evolution.toml"

    result = main(["init-config", "--path", str(config_path)])

    assert result == 0
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert set(config["privacy"]) == {
        "store_raw_messages",
        "include_evidence_blocks",
        "redact_local_paths",
        "redact_private_contacts",
    }
    assert config["privacy"]["store_raw_messages"] is False
    assert config["privacy"]["include_evidence_blocks"] is False
    assert config["privacy"]["redact_local_paths"] is True
    assert config["privacy"]["redact_private_contacts"] is True


def test_help_command_does_not_fail(capsys):
    result = main([])

    assert result == 0
    assert "Privacy-safe CLI" in capsys.readouterr().out


def _test_workspace(name: str) -> Path:
    workspace = Path.cwd() / ".tmp" / "test-cli" / f"{name}-{uuid4().hex}"
    workspace.mkdir(parents=True, exist_ok=False)
    return workspace
