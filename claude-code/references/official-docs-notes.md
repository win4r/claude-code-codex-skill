# Official Claude Code Docs Notes

Reviewed on 2026-04-26 from official docs under `https://code.claude.com/docs/en/`.

## Pages Reviewed

- Overview: https://code.claude.com/docs/en/overview
- Quickstart: https://code.claude.com/docs/en/quickstart
- CLI reference: https://code.claude.com/docs/en/cli-reference
- Programmatic usage: https://code.claude.com/docs/en/headless
- Permission modes: https://code.claude.com/docs/en/permission-modes
- Permissions: https://code.claude.com/docs/en/permissions
- Best practices: https://code.claude.com/docs/en/best-practices
- Common workflows: https://code.claude.com/docs/en/common-workflows
- Memory and CLAUDE.md: https://code.claude.com/docs/en/memory
- Claude Code skills: https://code.claude.com/docs/en/slash-commands

## Operational Summary

Claude Code is an agentic coding tool available through terminal, IDEs, desktop, browser, Slack, and CI surfaces. The local terminal CLI is the most useful surface for Codex delegation because it can read/edit the current repo, run commands, and return output through the shell.

Daily CLI commands:

- `claude`: start an interactive session in the current project.
- `claude "query"`: start interactive mode with an initial prompt.
- `claude -p "query"`: run non-interactively, print output, and exit.
- `cat file | claude -p "query"`: pipe context into a non-interactive run.
- `claude --continue` or `claude -c`: continue the most recent conversation in the current directory.
- `claude --resume <session>` or `claude -r <session>`: resume by session ID or name.
- `claude auth status --text`: verify authentication.

Programmatic usage:

- Use `-p` or `--print` for scripted calls.
- Use `--output-format text`, `json`, or `stream-json` depending on how Codex needs to consume the result.
- With `--output-format json`, the textual answer is in `result`; session and usage metadata are also returned.
- Use `--json-schema` with JSON output when a strict machine-readable shape is required.
- Use `--max-turns` and `--max-budget-usd` to bound unattended runs.
- `--bare` starts faster by skipping hooks, skills, plugins, MCP servers, auto memory, and CLAUDE.md. It also skips OAuth and keychain reads, so it usually needs `ANTHROPIC_API_KEY` or an `apiKeyHelper` passed through settings.

Permission model:

- `default`: read-only actions run; edits, Bash, and network actions ask.
- `acceptEdits`: file edits and common filesystem commands inside the working directory are accepted.
- `plan`: use for analysis and planning before edits.
- `auto`: reduces prompts with a background safety classifier; availability depends on plan, admin settings, model, and provider.
- `dontAsk`: auto-denies anything not pre-approved by allow rules.
- `bypassPermissions`: skips permission checks except protected paths; official docs recommend it only inside isolated containers, VMs, or devcontainers.

Permission rules:

- Rule format is `Tool` or `Tool(specifier)`, for example `Read`, `Edit(/src/**)`, `WebFetch(domain:example.com)`, or `Bash(npm test)`.
- Deny rules take precedence over ask and allow rules.
- Bash wildcard matching is powerful but fragile. Prefer exact commands or narrow prefixes such as `Bash(npm test)` and `Bash(git diff *)`.
- A space before a trailing `*` matters: `Bash(git diff *)` matches `git diff --stat`; `Bash(git diff*)` is broader.
- Read/Edit rules do not constrain Bash subprocesses such as `cat .env`; use sandboxing or deny Bash patterns for stronger isolation.

Prompting and workflow:

- Provide a verification path: tests, lint, screenshots, expected output, or a command Claude can run.
- For uncertain or multi-file work, use explore -> plan -> implement -> verify -> commit/PR.
- For small, obvious diffs, direct implementation is acceptable.
- Keep prompts specific: target files, symptoms, reproduction commands, constraints, expected behavior, and what "done" means.
- Use CLI tools such as `gh`, package managers, and language-specific test runners instead of making Claude infer external service APIs.
- Avoid long omnibus sessions; clear or restart when tasks are unrelated or after repeated course corrections.

Project memory and instructions:

- Claude Code reads `CLAUDE.md`, not `AGENTS.md`.
- If a repo already uses `AGENTS.md`, create a `CLAUDE.md` that imports it with `@AGENTS.md` and adds Claude-specific notes below.
- Use CLAUDE.md for stable project facts and broad conventions.
- Use skills for repeatable procedures or domain-specific context that should load only when relevant.
- Auto memory is local per project and stores learnings such as build commands and debugging insights.

Skill implications for Codex:

- Codex should invoke Claude Code as a bounded delegated worker, not treat it as the source of truth.
- Prefer non-interactive `claude -p` so Codex can continue supervising the workflow.
- Always inspect local diffs after implementation runs.
- Keep Codex responsible for final verification and the final user report.
