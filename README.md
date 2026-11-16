# [🚀观看我的哔哩哔哩视频](https://space.bilibili.com/3493277319825652)

# Claude Code Codex Skill

Codex skill for invoking the local Claude Code CLI as a delegated development agent.

The skill wraps `claude -p` with safer defaults, documents when to use `plan`, `acceptEdits`, `dontAsk`, and `auto`, and keeps Codex responsible for inspecting diffs and verifying results before reporting back.

## Install

Clone this repository and copy the skill directory into Codex's skills folder:

```bash
git clone https://github.com/win4r/claude-code-codex-skill.git
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$CODEX_HOME/skills"
rm -rf "$CODEX_HOME/skills/claude-code"
cp -R claude-code-codex-skill/claude-code "$CODEX_HOME/skills/"
```

Then invoke it in Codex with `$claude-code` when you want Codex to consult or delegate work to Claude Code.

## Contents

- `claude-code/SKILL.md`: Codex-facing workflow and guardrails.
- `claude-code/scripts/run_claude.py`: wrapper around the local `claude` CLI.
- `claude-code/references/official-docs-notes.md`: condensed notes from official Claude Code docs.

## Requirements

- Claude Code CLI installed and on `PATH`.
- `claude auth status --text` succeeds.
- Python 3 is available on `PATH`.
- Codex can read `${CODEX_HOME:-$HOME/.codex}/skills/claude-code`.
