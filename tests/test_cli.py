from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

from agent_evolution.cli import main


FIXTURES = Path(__file__).parent / "fixtures"


def test_init_writes_privacy_safe_defaults(tmp_path: Path):
    config_path = tmp_path / "agent-evolution.toml"

    result = main(["init", "--config", str(config_path)])

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


def test_legacy_init_config_still_works(tmp_path: Path):
    config_path = tmp_path / "legacy.toml"

    result = main(["init-config", "--path", str(config_path)])

    assert result == 0
    assert config_path.exists()


def test_scan_reports_configured_fixture_source(tmp_path: Path, capsys):
    config_path = _write_cli_config(tmp_path)

    result = main(["scan", "--config", str(config_path)])

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload == {
        "enabled_sources": 1,
        "existing_sources": 1,
        "observations": 2,
    }


def test_run_writes_review_doc_and_state(tmp_path: Path, capsys):
    config_path = _write_cli_config(tmp_path)

    result = main(["run", "--config", str(config_path)])

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert Path(payload["review_doc"]).exists()
    assert (tmp_path / "state" / "last_run.json").exists()


def test_validate_rejects_broken_review_doc(tmp_path: Path, capsys):
    config_path = _write_cli_config(tmp_path)
    review_root = tmp_path / "review"
    review_root.mkdir()
    (review_root / "broken.md").write_text("## 建议 001：坏例子\n\n**原文证据**：x\n", encoding="utf-8")

    result = main(["validate", "--config", str(config_path)])

    payload = json.loads(capsys.readouterr().out)
    assert result == 1
    assert payload["errors"]


def test_catch_up_runs_when_state_is_missing(tmp_path: Path, capsys):
    config_path = _write_cli_config(tmp_path)

    result = main(["catch-up", "--config", str(config_path)])

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert Path(payload["review_doc"]).exists()


def test_catch_up_skips_when_state_is_recent(tmp_path: Path, capsys):
    config_path = _write_cli_config(tmp_path)
    assert main(["run", "--config", str(config_path)]) == 0
    capsys.readouterr()

    result = main(["catch-up", "--config", str(config_path)])

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload == {"catch_up": False}


def test_install_schedule_prints_windows_command(tmp_path: Path, capsys):
    config_path = _write_cli_config(tmp_path)

    result = main(["install-schedule", "--config", str(config_path), "--os", "windows"])

    output = capsys.readouterr().out
    assert result == 0
    assert "schtasks" in output
    assert "catch-up" in output


def test_install_schedule_prints_mac_plist(tmp_path: Path, capsys):
    config_path = _write_cli_config(tmp_path)

    result = main(["install-schedule", "--config", str(config_path), "--os", "mac"])

    output = capsys.readouterr().out
    assert result == 0
    assert "<plist version=\"1.0\">" in output
    assert "<string>catch-up</string>" in output


def test_doctor_reports_config_status(tmp_path: Path, capsys):
    config_path = _write_cli_config(tmp_path)

    result = main(["doctor", "--config", str(config_path)])

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["config_exists"] is True
    assert payload["enabled_sources"] == 1


def test_help_command_does_not_fail(capsys):
    result = main([])

    assert result == 0
    assert "Privacy-safe CLI" in capsys.readouterr().out


def test_module_execution_displays_help():
    result = subprocess.run(
        [sys.executable, "-m", "agent_evolution.cli", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Privacy-safe CLI" in result.stdout


def _write_cli_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "agent-evolution.toml"
    generic_fixture = (FIXTURES / "generic.jsonl").resolve().as_posix()
    config_path.write_text(
        f"""
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
name = "generic-jsonl"
path = "{generic_fixture}"
enabled = true
""",
        encoding="utf-8",
    )
    return config_path
