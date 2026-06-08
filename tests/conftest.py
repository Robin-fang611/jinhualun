from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest


@pytest.fixture
def tmp_path(request):
    base = (Path.cwd() / ".test-tmp").resolve()
    base.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in request.node.name
    )
    path = (base / f"{safe_name}-{uuid.uuid4().hex}").resolve()
    if not path.is_relative_to(base):
        raise RuntimeError("refusing to create a temp path outside .test-tmp")
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        if path.is_relative_to(base):
            shutil.rmtree(path, ignore_errors=True)
