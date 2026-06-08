from __future__ import annotations

from html import escape


def build_windows_task_command(
    task_name: str,
    python_executable: str,
    config_path: str,
    interval_hours: int,
) -> str:
    task_command = (
        f'\\"{python_executable}\\" '
        f'-m agent_evolution.cli catch-up --config \\"{config_path}\\"'
    )
    return (
        f'schtasks /Create /TN "{task_name}" /SC HOURLY /MO {interval_hours} '
        f'/TR "{task_command}" /F'
    )


def build_launch_agent_plist(
    label: str,
    agent_evolve_path: str,
    config_path: str,
    interval_hours: int,
) -> str:
    interval_seconds = interval_hours * 3600
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{escape(label)}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{escape(agent_evolve_path)}</string>
    <string>catch-up</string>
    <string>--config</string>
    <string>{escape(config_path)}</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>StartInterval</key>
  <integer>{interval_seconds}</integer>
</dict>
</plist>
"""
