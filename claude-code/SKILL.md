---
name: claude-code
description: Invoke the local Claude Code CLI from Codex for delegated development tasks, second-opinion codebase analysis, implementation attempts, test fixing, PR preparation, or automation. Use when the user asks Codex to call, run, use, consult, compare with, or delegate work to Claude Code, or when a task benefits from having Claude Code inspect or modify the same repository under Codex supervision.
---

# Claude Code

Use this skill to run Claude Code as a local development agent from Codex. Treat Claude Code as a delegated worker: give it a bounded task, inspect its output and diffs yourself, then verify before reporting back.

## Preconditions

Check the local CLI before a real run:

```bash
command -v claude
claude --version
claude auth status --text
```

If `claude` is missing or unauthenticated, tell the user. Do not install or log in unless the user asked for setup. Current official install options include native install, Homebrew, WinGet, and distro packages; see `references/official-docs-notes.md`.

## Invocation Workflow

1. Choose the permission mode before running Claude Code.
2. Write a prompt that includes the repo path, exact task, allowed side effects, files or areas to prioritize, verification commands, and required final format.
3. Prefer the wrapper script to avoid shell quoting mistakes:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/claude-code"
python3 "$SKILL_DIR/scripts/run_claude.py" \
  --cwd "$PWD" \
  --mode plan \
  --tools "Read,Grep,Glob" \
  --task "Analyze the authentication flow and return a concise implementation plan. Do not edit files."
```

Wrapper flags use kebab-case for Codex ergonomics; the wrapper translates them to Claude Code's camelCase flags where needed, such as `--allowed-tools` to `--allowedTools`.

4. After Claude Code returns, inspect `git status --short` and `git diff` yourself.
5. Run the relevant tests or checks in Codex, even if Claude Code says it already did.
6. Report what Claude Code did separately from what Codex verified or changed afterward.

## Mode Selection

- Use `plan` for read-only analysis, task scoping, migration plans, and second opinions. This is the default in the wrapper.
- Use `acceptEdits` for implementation only after the task is clear. Pair it with narrow `--allowed-tools` entries for expected commands.
- Use `dontAsk` for locked-down non-interactive checks where anything not pre-approved should fail.
- Use `auto` only when the user wants autonomous execution and the account supports it.
- Do not use `bypassPermissions` unless the user explicitly asks and the work is inside an isolated container, VM, or disposable worktree. The wrapper requires `--allow-bypass` as an extra guard.
- Avoid `--bare` by default on this machine because official docs say bare mode skips OAuth and keychain reads; use it only when API-key or settings-based auth is deliberately configured.

## Prompt Contract

For development tasks, include this shape in the Claude Code prompt:

```text
You are Claude Code working under Codex supervision in <repo path>.
Task: <specific task>.
Constraints:
- Do not commit, push, install global tools, change credentials, or touch unrelated files unless explicitly requested.
- Keep changes minimal and follow existing repository patterns.
- Run or propose these verification commands: <commands>.
- End with: changed files, commands run, result, and unresolved risks.
```

For review or planning tasks, ask for file paths, line references where possible, severity or priority, and no edits.

## Useful Commands

Read-only second opinion:

```bash
python3 "$SKILL_DIR/scripts/run_claude.py" \
  --cwd "$PWD" \
  --mode plan \
  --tools "Read,Grep,Glob" \
  --max-turns 4 \
  --task "Review the current diff for correctness risks. Do not edit files. Return findings first with file paths."
```

Do not use `--max-turns 1` for Claude Code smoke tests or reviews. On this machine even a trivial `Reply exactly: CLAUDE_OK` prompt can fail with `Error: Reached max turns (1)`. Use at least `--max-turns 3` for smoke prompts and `--max-turns 4-8` for reviews.

Implementation with narrow approvals:

```bash
python3 "$SKILL_DIR/scripts/run_claude.py" \
  --cwd "$PWD" \
  --mode acceptEdits \
  --allowed-tools "Read,Edit,Bash(npm test),Bash(git status *),Bash(git diff *)" \
  --max-turns 8 \
  --task "Implement <task>. Run npm test if relevant. Do not commit or push."
```

Structured output:

```bash
python3 "$SKILL_DIR/scripts/run_claude.py" \
  --cwd "$PWD" \
  --mode plan \
  --output-format json \
  --task "Summarize this project and list the top three risky areas to inspect."
```

Continue a prior Claude Code conversation:

```bash
python3 "$SKILL_DIR/scripts/run_claude.py" \
  --cwd "$PWD" \
  --continue-session \
  --task "Continue the previous investigation and focus only on database query performance."
```

Low-noise read-only review fallback:

```bash
python3 "$SKILL_DIR/scripts/run_claude.py" \
  --cwd "$PWD" \
  --mode plan \
  --output-format text \
  --tools "Read,Grep,Glob" \
  --max-turns 6 \
  --timeout 180 \
  --setting-sources project \
  --mcp-config '{"mcpServers":{}}' \
  --strict-mcp-config \
  --no-chrome \
  --no-session-persistence \
  --disable-slash-commands \
  --task "Review this project read-only. Return findings first with file paths."
```

Use `{"mcpServers":{}}`, not `{}`, when disabling MCP servers with `--strict-mcp-config`; Claude Code rejects `{}` as an invalid MCP configuration.

If a normal read-only run produces no stdout for about 60-90 seconds, inspect `pgrep -fl 'claude|run_claude.py|bun run --cwd .*\\.claude/plugins'`. If plugin, MCP, or Chrome startup is visible, stop that run and retry with the low-noise command above. If no plugin/MCP startup is visible, remember that print mode may stay silent until completion; enforce the wrapper timeout and avoid repeatedly extending the same run.

If a review run times out, run a minimal smoke check before blaming authentication or installation:

```bash
python3 "$SKILL_DIR/scripts/run_claude.py" \
  --cwd "$PWD" \
  --mode plan \
  --output-format text \
  --model sonnet \
  --max-turns 3 \
  --timeout 45 \
  --setting-sources project \
  --mcp-config '{"mcpServers":{}}' \
  --strict-mcp-config \
  --no-chrome \
  --no-session-persistence \
  --disable-slash-commands \
  --task "Reply exactly: CLAUDE_OK"
```

For repeated review stalls, avoid full-file snapshots. Try a very small line-numbered excerpt of only the risky code paths; if that still times out around 75-120 seconds while the smoke check passes, stop delegating the review and continue with Codex-local inspection plus tests. Report this as a Claude Code review-path timeout, not as a project test failure.

## Guardrails

- Never pass secrets, API keys, tokens, private credentials, or raw `.env` contents in a prompt.
- Do not assume Claude Code's summary is true. Verify diffs and tests locally.
- Keep delegated tasks bounded. If Claude Code fails twice on the same issue, start a fresh prompt with the new evidence instead of continuing a polluted session.
- For unattended or long-running work, pass `--timeout <seconds>` so the wrapper cannot run indefinitely.
- Preserve user changes. If Claude Code edits unrelated files or conflicts with user work, stop and inspect before proceeding.
- For parallel Claude Code runs, use separate git worktrees or other isolated directories so changes cannot collide.

## References

- `scripts/run_claude.py`: wrapper for local `claude -p` calls with safer defaults.
- `references/official-docs-notes.md`: condensed notes from the official Claude Code docs reviewed for this skill.
