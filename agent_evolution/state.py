from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class RunState:
    last_success_at: datetime
    exit_code: int
    summary: str


def write_run_state(path: Path, state: RunState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_success_at": state.last_success_at.astimezone(timezone.utc).isoformat(),
        "exit_code": state.exit_code,
        "summary": state.summary,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_run_state(path: Path) -> RunState | None:
    if not path.exists():
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    return RunState(
        last_success_at=datetime.fromisoformat(payload["last_success_at"]),
        exit_code=int(payload["exit_code"]),
        summary=str(payload["summary"]),
    )


def should_catch_up(path: Path, now: datetime, interval_hours: int) -> bool:
    state = read_run_state(path)
    if state is None:
        return True

    last_success = state.last_success_at.astimezone(timezone.utc)
    current_time = now.astimezone(timezone.utc)
    elapsed_seconds = (current_time - last_success).total_seconds()
    return elapsed_seconds >= interval_hours * 3600
