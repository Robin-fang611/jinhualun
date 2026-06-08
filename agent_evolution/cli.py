"""Command line entry point for Agent Evolution Kit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from agent_evolution import __version__
from agent_evolution.config import load_config
from agent_evolution.config import write_default_config as write_default_config_file
from agent_evolution.pipeline import run as run_pipeline
from agent_evolution.pipeline import scan as scan_pipeline
from agent_evolution.review_docs import validate_review_doc
from agent_evolution.schedule import build_launch_agent_plist, build_windows_task_command
from agent_evolution.state import RunState, should_catch_up, write_run_state


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

    init = subparsers.add_parser(
        "init",
        help="write a privacy-safe starter TOML config",
    )
    init.add_argument(
        "--config",
        default="agent-evolution.toml",
        help="config path to write",
    )
    init.add_argument(
        "--force",
        action="store_true",
        help="overwrite the config path if it already exists",
    )
    init.set_defaults(func=write_default_config)

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

    scan = subparsers.add_parser("scan", help="scan configured sources")
    _add_config_arg(scan)
    scan.set_defaults(func=scan_sources)

    run = subparsers.add_parser("run", help="write paired review suggestions")
    _add_config_arg(run)
    run.set_defaults(func=run_evolution)

    validate = subparsers.add_parser("validate", help="validate review Markdown")
    _add_config_arg(validate)
    validate.set_defaults(func=validate_review_docs)

    catch_up = subparsers.add_parser("catch-up", help="run if interval was missed")
    _add_config_arg(catch_up)
    catch_up.set_defaults(func=catch_up_if_needed)

    install_schedule = subparsers.add_parser(
        "install-schedule",
        help="print a Windows Task Scheduler command or macOS LaunchAgent plist",
    )
    _add_config_arg(install_schedule)
    install_schedule.add_argument("--os", choices=["windows", "mac"], required=True)
    install_schedule.add_argument("--name", default="AgentEvolutionKit")
    install_schedule.add_argument("--python", default="python")
    install_schedule.add_argument("--agent-evolve", default="agent-evolve")
    install_schedule.set_defaults(func=print_schedule)

    doctor = subparsers.add_parser("doctor", help="check local configuration")
    _add_config_arg(doctor)
    doctor.set_defaults(func=doctor_check)

    return parser


def _add_config_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        default="agent-evolution.toml",
        help="config path to read",
    )


def write_default_config(args: argparse.Namespace) -> int:
    config_path = Path(getattr(args, "config", None) or args.path)
    if config_path.exists() and not args.force:
        raise SystemExit(f"{config_path} already exists; pass --force to overwrite.")

    write_default_config_file(config_path)
    print(json.dumps({"config": str(config_path.resolve())}, ensure_ascii=False))
    return 0


def scan_sources(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    summary = scan_pipeline(config)
    print(json.dumps(summary.__dict__, ensure_ascii=False))
    return 0


def run_evolution(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    review_doc = run_pipeline(config)
    state_path = config.workspace.state_dir / "last_run.json"
    write_run_state(
        state_path,
        RunState(
            last_success_at=datetime.now(timezone.utc),
            exit_code=0,
            summary=f"wrote {review_doc}",
        ),
    )
    print(json.dumps({"review_doc": str(review_doc)}, ensure_ascii=False))
    return 0


def validate_review_docs(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    errors: list[str] = []
    if config.workspace.review_root.exists():
        for path in sorted(config.workspace.review_root.glob("*.md")):
            result = validate_review_doc(path.read_text(encoding="utf-8"))
            if not result.is_valid:
                errors.extend(f"{path.name}: {error}" for error in result.errors)
    print(json.dumps({"errors": errors}, ensure_ascii=False))
    return 1 if errors else 0


def catch_up_if_needed(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    state_path = config.workspace.state_dir / "last_run.json"
    due = should_catch_up(
        state_path,
        now=datetime.now(timezone.utc),
        interval_hours=config.schedule.interval_hours,
    )
    if not due:
        print(json.dumps({"catch_up": False}, ensure_ascii=False))
        return 0
    result = run_evolution(args)
    return result


def print_schedule(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    config_path = str(Path(args.config).resolve())
    if args.os == "windows":
        print(
            build_windows_task_command(
                task_name=args.name,
                python_executable=args.python,
                config_path=config_path,
                interval_hours=config.schedule.interval_hours,
            )
        )
        return 0

    print(
        build_launch_agent_plist(
            label=args.name,
            agent_evolve_path=args.agent_evolve,
            config_path=config_path,
            interval_hours=config.schedule.interval_hours,
        )
    )
    return 0


def doctor_check(args: argparse.Namespace) -> int:
    config_path = Path(args.config)
    payload = {"config_exists": config_path.exists()}
    if config_path.exists():
        config = load_config(config_path)
        payload["enabled_sources"] = sum(1 for source in config.sources if source.enabled)
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["config_exists"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)
