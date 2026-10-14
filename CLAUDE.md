# claude-agents

This is the source repo for a Claude Code agent pack. `pack/` is deployed into `~/.claude` by `scripts/deploy`.

- To deploy, update, or uninstall, follow `docs/deploy.md`.
- To edit agents or skills, follow the `agent-authoring` skill (`pack/skills/agent-authoring/SKILL.md`). Keep `README.md`'s inventory and `docs/architecture.md` in sync with any change to an agent's name, scope, model, or tools.
- Before deploying, run `python3 -m pytest -q`. The suite covers the deploy tool and lints the pack.
- `scripts/deploy` must stay standard-library-only and compatible with Python 3.9, which is what macOS ships as `/usr/bin/python3`.
- Edits under `pack/` only reach other sessions after `scripts/deploy install`. Agents in `~/.claude/agents` pick up changes in new sessions.
