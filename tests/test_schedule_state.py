from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from agent_evolution.schedule import build_launch_agent_plist, build_windows_task_command
from agent_evolution.state import RunState, read_run_state, should_catch_up, write_run_state


def test_run_state_round_trip(tmp_path: Path):
    state_path = tmp_path / "last_run.json"
    state = RunState(
        last_success_at=datetime(2026, 6, 8, 4, 0, tzinfo=timezone.utc),
        exit_code=0,
        summary="wrote review doc",
    )

    write_run_state(state_path, state)

    assert read_run_state(state_path) == state


def test_should_catch_up_when_state_is_missing(tmp_path: Path):
    assert should_catch_up(
        tmp_path / "missing.json",
        now=datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc),
        interval_hours=72,
    )


def test_should_catch_up_when_last_success_is_old(tmp_path: Path):
    state_path = tmp_path / "last_run.json"
    write_run_state(
        state_path,
        RunState(
            last_success_at=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
            exit_code=0,
            summary="ok",
        ),
    )

    assert should_catch_up(
        state_path,
        now=datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc),
        interval_hours=72,
    )


def test_should_not_catch_up_when_last_success_is_recent(tmp_path: Path):
    state_path = tmp_path / "last_run.json"
    write_run_state(
        state_path,
        RunState(
            last_success_at=datetime(2026, 6, 8, 10, 0, tzinfo=timezone.utc),
            exit_code=0,
            summary="ok",
        ),
    )

    assert not should_catch_up(
        state_path,
        now=datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc),
        interval_hours=72,
    )


def test_windows_task_command_calls_catch_up():
    command = build_windows_task_command(
        task_name="AgentEvolutionKit",
        python_executable="C:\\Python311\\python.exe",
        config_path="C:\\project\\agent-evolution.toml",
        interval_hours=72,
    )

    assert "schtasks" in command
    assert "/SC HOURLY" in command
    assert "/MO 72" in command
    assert "catch-up" in command
    assert "--config" in command
    assert "C:\\project\\agent-evolution.toml" in command


def test_launch_agent_plist_calls_catch_up_and_escapes_values():
    plist = build_launch_agent_plist(
        label="com.example.agent-evolution-kit",
        agent_evolve_path="/usr/local/bin/agent-evolve",
        config_path="/Users/example/A&B/agent-evolution.toml",
        interval_hours=72,
    )

    assert "<key>RunAtLoad</key>" in plist
    assert "<true/>" in plist
    assert "<key>StartInterval</key>" in plist
    assert "<integer>259200</integer>" in plist
    assert "<string>catch-up</string>" in plist
    assert "<string>--config</string>" in plist
    assert "/Users/example/A&amp;B/agent-evolution.toml" in plist
