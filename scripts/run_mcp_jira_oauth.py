#!/usr/bin/env python3
"""Utility to launch the MCP Jira bridge, handle OAuth login, and run a smoke call."""

from __future__ import annotations

import argparse
import os
import re
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent
BRIDGE_CMD = [sys.executable, "-m", "mcp_jira.http_server", "--host", "127.0.0.1", "--port", "8055"]
AUTH_PATTERN = re.compile(r"https://auth\.atlassian\.com/authorize[^\s]+")
READY_PATTERN = re.compile(r"MCP Jira bridge ready")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start MCP Jira bridge and guide OAuth flow")
    parser.add_argument(
        "--open",
        action="store_true",
        help="Attempt to open the authorization URL in the default browser automatically",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Invoke scripts/test_mcp_jira.py --pretty once the bridge is ready",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        help="Log level to pass to the bridge (default: info)",
    )
    return parser


def ensure_py_path(env: dict[str, str]) -> None:
    pythonpath = env.get("PYTHONPATH")
    path_str = str(REPO_ROOT)
    if pythonpath:
        if path_str not in pythonpath.split(os.pathsep):
            env["PYTHONPATH"] = os.pathsep.join([path_str, pythonpath])
    else:
        env["PYTHONPATH"] = path_str


def load_dotenv_into_env(env: dict[str, str]) -> None:
    """Load KEY=VALUE pairs from .env in repo root into both env and os.environ."""
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    try:
        with env_path.open("r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if not key:
                    continue
                env[key] = value
                os.environ[key] = value
    except Exception:
        # don't fail hard if .env is malformed; continue with whatever we have
        pass


def spawn_bridge(log_level: str) -> subprocess.Popen[str]:
    cmd = BRIDGE_CMD + ["--log-level", log_level]
    env = os.environ.copy()
    # Auto-load .env to make startup hands-free
    load_dotenv_into_env(env)
    ensure_py_path(env)
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    return process


def forward_output(process: subprocess.Popen[str], auto_open: bool) -> bool:
    """Stream bridge output, return True when ready."""
    ready = False
    if not process.stdout:
        return ready

    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()

        if auto_open:
            match = AUTH_PATTERN.search(line)
            if match:
                url = match.group(0)
                try:
                    opened = webbrowser.open(url)
                    if opened:
                        print("[mcp-jira] Opened authorization URL in your browser")
                    else:
                        print("[mcp-jira] Unable to auto-open browser; please open the URL manually")
                except Exception as exc:  # pragma: no cover - platform specific
                    print(f"[mcp-jira] Failed to open browser automatically: {exc}")
                auto_open = False

        if READY_PATTERN.search(line):
            ready = True
            break

        if process.poll() is not None:
            break

    return ready


def run_smoke_test() -> None:
    cmd = [sys.executable, "scripts/test_mcp_jira.py", "--pretty"]
    env = os.environ.copy()
    ensure_py_path(env)
    print("[mcp-jira] Running smoke test via scripts/test_mcp_jira.py --pretty ...")
    try:
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as exc:
        print(f"[mcp-jira] Smoke test failed with exit code {exc.returncode}")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    process = spawn_bridge(args.log_level)

    try:
        ready = forward_output(process, auto_open=args.open)
        if not ready:
            print("[mcp-jira] Bridge exited before becoming ready")
            process.wait(timeout=1)
            return

        if args.test:
            run_smoke_test()

        print("[mcp-jira] Bridge is running. Press Ctrl+C to stop.")
        while True:
            if process.poll() is not None:
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[mcp-jira] Stopping bridge...")
    finally:
        try:
            process.send_signal(signal.SIGINT)
            process.wait(timeout=5)
        except Exception:
            process.kill()


if __name__ == "__main__":  # pragma: no cover - CLI utility
    main()
