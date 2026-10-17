# claude-supervisor

This is the source repo for a Claude Code agent pack. `pack/` is deployed by `deploy` into `~/.config/claude-supervisor` (run with `claude-supervisor`), or into `~/.claude` with `--global`.

- To deploy, update, or uninstall, follow `docs/deploy.md`.
- To edit agents or skills, follow the `agent-authoring` skill (`pack/skills/agent-authoring/SKILL.md`). Keep the inventory in `docs/architecture.md` in sync with any change to an agent's name, scope, model, or tools.
- Before deploying, run `python3 -m pytest -q`. The suite covers the deploy tool and lints the pack.
- `deploy` (at the repo root) must stay standard-library-only and compatible with Python 3.9, which is what macOS ships as `/usr/bin/python3`.
- Edits under `pack/` only reach other sessions after `./deploy install`. Deployed agents pick up changes in new sessions.
- `VERSION` holds the pack version as `X.y`. Every commit on `main` raises y (normally by one), once per change set, except that the squash-merge commit of a major feature branch sets `X.0` (X raised by one): the editing agent (under fan-out, the lead or the unit it names, not every worker) bumps `VERSION` with the change before running the tests; `tests/test_version.py` fails on `main` when tracked files differ from `HEAD` and `VERSION` was not raised. `git-ops` stages `VERSION` with the commit when it is modified in the working tree and, on `main`, escalates instead of committing when the staged diff leaves it unchanged (`git diff --cached --stat -- VERSION` is empty).
- Feature branches rebase on `main` frequently and never touch `VERSION`. To land a branch: `git rebase main` on the branch, then `git merge --squash <branch>` on `main`, and bump `VERSION` in the squash commit. These two rules are specific to this repo and stay out of the `git-safety` skill.
