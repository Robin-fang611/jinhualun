# Agent Evolution Kit

Agent Evolution Kit is a privacy-safe Python CLI skeleton for reviewing and
organizing agent improvement suggestions.

It does not train model weights. It does not save raw chats or raw evidence by
default. It also does not automatically modify global agent files unless a
future workflow explicitly asks for that behavior and the operator approves it.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
agent-evolve --help
agent-evolve init-config --path agent-evolution.toml
pytest
```

## Privacy Defaults

- Raw chats are not stored.
- Raw evidence files are not stored.
- Generated state and review output are ignored by Git.
- Global agent configuration files are not changed automatically.

## Development

This project targets Python 3.11 or newer and uses only the Python standard
library at runtime. The optional development extra installs `pytest` for tests.
