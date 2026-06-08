"""Command line entry point for Agent Evolution Kit."""

from __future__ import annotations

import argparse
from pathlib import Path

from agent_evolution import __version__


DEFAULT_CONFIG_TOML = """# Agent Evolution Kit configuration

[privacy]
store_raw_chats = false
store_raw_evidence = false
auto_modify_global_agent_files = false

[output]
state_dir = "state"
review_dir = "review"
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-evolve",
        description="Privacy-safe CLI for agent evolution workflows.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    init_config = subparsers.add_parser(
        "init-config",
        help="write a privacy-safe starter TOML config",
    )
    init_config.add_argument(
        "--path",
        default="agent-evolution.toml",
        help="config path to write",
    )
    init_config.add_argument(
        "--force",
        action="store_true",
        help="overwrite the config path if it already exists",
    )
    init_config.set_defaults(func=write_default_config)

    return parser


def write_default_config(args: argparse.Namespace) -> int:
    config_path = Path(args.path)
    if config_path.exists() and not args.force:
        raise SystemExit(f"{config_path} already exists; pass --force to overwrite.")

    config_path.write_text(DEFAULT_CONFIG_TOML, encoding="utf-8")
    print(f"Wrote {config_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)
