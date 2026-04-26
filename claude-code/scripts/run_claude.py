#!/usr/bin/env python3
"""Run Claude Code from Codex with explicit, reviewable defaults."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


PERMISSION_MODES = ("default", "acceptEdits", "plan", "auto", "dontAsk", "bypassPermissions")
OUTPUT_FORMATS = ("text", "json", "stream-json")
EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Could not read {path}: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Claude Code non-interactively from Codex.")
    parser.add_argument("--cwd", default=".", help="Working directory for Claude Code.")
    parser.add_argument("--task", help="Prompt to send to Claude Code.")
    parser.add_argument("--task-file", type=Path, help="Read the prompt from a UTF-8 text file.")
    parser.add_argument("--stdin-file", type=Path, help="Pipe this UTF-8 file to Claude Code stdin as extra context.")
    parser.add_argument("--mode", choices=PERMISSION_MODES, default="plan", help="Claude Code permission mode.")
    parser.add_argument("--allow-bypass", action="store_true", help="Allow --mode bypassPermissions.")
    parser.add_argument("--output-format", choices=OUTPUT_FORMATS, default="json", help="Claude Code output format.")
    parser.add_argument("--tools", help='Restrict available tools, for example "Read,Grep,Glob".')
    parser.add_argument("--allowed-tools", help='Auto-approve tools, for example "Read,Edit,Bash(npm test)".')
    parser.add_argument("--disallowed-tools", help='Remove tools, for example "Bash(git push *)".')
    parser.add_argument("--model", help="Claude Code model alias or full model name.")
    parser.add_argument("--effort", choices=EFFORT_LEVELS, help="Reasoning effort level.")
    parser.add_argument("--max-turns", type=int, help="Maximum agentic turns for print mode.")
    parser.add_argument("--max-budget-usd", help="Maximum API spend for the run, as accepted by Claude Code.")
    parser.add_argument("--append-system-prompt", help="Append text to Claude Code's default system prompt.")
    parser.add_argument("--append-system-prompt-file", type=Path, help="Append system prompt text from a file.")
    parser.add_argument("--settings", help="Settings JSON file path or JSON string to pass to Claude Code.")
    parser.add_argument("--mcp-config", help="MCP config JSON file path or JSON string to pass to Claude Code.")
    parser.add_argument("--add-dir", action="append", default=[], help="Additional directory Claude Code may access.")
    parser.add_argument("--continue-session", action="store_true", help="Continue the most recent Claude Code conversation.")
    parser.add_argument("--resume", help="Resume a Claude Code session by ID or name.")
    parser.add_argument("--name", help="Set a display name for the Claude Code session.")
    parser.add_argument("--bare", action="store_true", help="Use Claude Code bare mode.")
    parser.add_argument("--skip-auth-check", action="store_true", help="Skip `claude auth status --text` preflight.")
    parser.add_argument("--timeout", type=int, default=0, help="Timeout in seconds; 0 means no timeout.")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it.")
    return parser


def preflight(claude: str, cwd: Path, skip_auth: bool) -> None:
    if skip_auth:
        return
    result = subprocess.run(
        [claude, "auth", "status", "--text"],
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit("Claude Code is not authenticated. Run `claude auth login` first.")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    claude = shutil.which("claude")
    if not claude:
        raise SystemExit("Claude Code CLI was not found on PATH.")

    cwd = Path(args.cwd).expanduser().resolve()
    if not cwd.is_dir():
        raise SystemExit(f"--cwd is not a directory: {cwd}")

    if args.task and args.task_file:
        raise SystemExit("Use either --task or --task-file, not both.")
    task = args.task if args.task is not None else read_text(args.task_file) if args.task_file else None
    if not task:
        raise SystemExit("Provide --task or --task-file.")

    if args.mode == "bypassPermissions" and not args.allow_bypass:
        raise SystemExit("Refusing bypassPermissions without --allow-bypass.")

    if args.bare and not (os.environ.get("ANTHROPIC_API_KEY") or args.settings):
        sys.stderr.write(
            "Warning: --bare skips OAuth/keychain reads. It usually requires ANTHROPIC_API_KEY "
            "or an apiKeyHelper in --settings.\n"
        )

    preflight(claude, cwd, args.skip_auth_check)

    cmd = [claude]
    if args.bare:
        cmd.append("--bare")
    if args.continue_session:
        cmd.append("--continue")
    if args.resume:
        cmd.extend(["--resume", args.resume])
    if args.name:
        cmd.extend(["--name", args.name])

    cmd.extend(["-p", task, "--permission-mode", args.mode, "--output-format", args.output_format])

    option_pairs = [
        ("--tools", args.tools),
        ("--allowedTools", args.allowed_tools),
        ("--disallowedTools", args.disallowed_tools),
        ("--model", args.model),
        ("--effort", args.effort),
        ("--max-turns", str(args.max_turns) if args.max_turns is not None else None),
        ("--max-budget-usd", args.max_budget_usd),
        ("--append-system-prompt", args.append_system_prompt),
        ("--append-system-prompt-file", str(args.append_system_prompt_file) if args.append_system_prompt_file else None),
        ("--settings", args.settings),
        ("--mcp-config", args.mcp_config),
    ]
    for flag, value in option_pairs:
        if value is not None:
            cmd.extend([flag, value])
    for path in args.add_dir:
        cmd.extend(["--add-dir", path])

    stdin_text = read_text(args.stdin_file) if args.stdin_file else None

    if args.dry_run:
        print(" ".join(shlex.quote(part) for part in cmd))
        return 0

    try:
        completed = subprocess.run(
            cmd,
            cwd=str(cwd),
            input=stdin_text,
            text=True,
            timeout=args.timeout or None,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"Claude Code timed out after {args.timeout} seconds.") from exc

    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
