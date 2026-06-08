from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class SnapshotResult:
    run_dir: Path
    before_dir: Path
    after_dir: Path
    changelog_path: Path


def snapshot_file_change(
    snapshot_root: Path,
    changed_file: Path,
    before_content: bytes | None,
    reason: str,
) -> SnapshotResult:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = snapshot_root / "runs" / f"{stamp}-{uuid.uuid4().hex[:8]}"
    before_dir = run_dir / "before"
    after_dir = run_dir / "after"
    before_dir.mkdir(parents=True, exist_ok=True)
    after_dir.mkdir(parents=True, exist_ok=True)

    if before_content is not None:
        (before_dir / changed_file.name).write_bytes(before_content)
    if changed_file.exists():
        shutil.copy2(changed_file, after_dir / changed_file.name)

    changelog_path = run_dir / "CHANGELOG.md"
    changelog_path.write_text(
        "\n".join(
            [
                f"# Snapshot {stamp}",
                "",
                f"Reason: {reason}",
                "",
                f"Changed file: {changed_file.name}",
                "",
                "Rollback: copy the matching file from before/ or after/ to the review directory.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return SnapshotResult(
        run_dir=run_dir,
        before_dir=before_dir,
        after_dir=after_dir,
        changelog_path=changelog_path,
    )
