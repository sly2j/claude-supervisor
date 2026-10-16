# Roadmap

## Context

- This repo is the source of a Claude Code agent pack. `pack/` deploys via `scripts/deploy`
  (stdlib-only, Python 3.9, which macOS ships as `/usr/bin/python3`).
- Work goes through the supervisor harness: `researcher`/`planner`/`executor`/`writer` leads with
  worker fan-out and `critic`/`scope-critic` loops; quick tier `quick-edit`/`git-ops`/`scout`.
- Before touching the pack, read `CLAUDE.md`, `docs/architecture.md`, and the `agent-authoring`
  skill (`pack/skills/agent-authoring/SKILL.md`).
- Per change set on `main`: edit, bump `VERSION` once (`1.x` -> `1.x+1`), run
  `python3 -m pytest -q`, run `scripts/deploy install` if `pack/` changed, commit with the trailer
  exactly `Co-Authored-By: Claude`, push.
- Plans live in `docs/plan-<topic>.md`; finished plans move to `docs/archive/` with `git mv`.
  Long tasks may use work packages (`## Work Packages` in the plan; see README).
- Owner's style rule is simplicity: add rules to agent files only for observed failures, no
  anticipated-failure clauses, keep line counts and line lengths down. The body of
  `pack/agents/supervisor.md` (after frontmatter) is 76 lines; do not grow it, except through
  item 3's reflow.
- Items are orthogonal. Pick one item per change set; remove it from this file in the same
  commit when it lands.

## Items

### 1. Deploy: Opus by default, fable only on request

- **Goal:** deployed `supervisor`, `planner`, `scope-critic` (and `critic`, already opus) default
  to Opus. Fable is a manual option (e.g. `--fable`).
- **Scope:**
  - In: remove `detect_fable`, the TTY prompt, and the `auto` value; simplify `scripts/deploy`.
  - In: drop the open Todo in `docs/plan-fable-fallback.md` (line 209) and archive that plan.
  - Out: any form of model or subscription detection.
- **Decisions already made:** no detection of any kind; Opus is the default; fable is manual.
- **Left to planner:** whether the source says `opus` and `--fable` rewrites to `fable`, or the
  reverse; whether the manifest still persists the choice. Either way, cover the prose dispatch
  tokens in `planner.md` (~line 59) and `writer.md` (~line 26).
- **Done when:**
  - No model-detection code path remains; tests cover the manual flag, on and off.
  - `docs/deploy.md`, README, and `docs/architecture.md` are updated where they mention fable.
  - `docs/plan-fable-fallback.md` is archived.
- **Pointers:** `scripts/deploy` (`detect_fable`, ~309-390), `docs/deploy.md` (`## Fable Or Opus`),
  `docs/plan-fable-fallback.md`, `tests/test_deploy.py`,
  `tests/test_pack_lint.py` (`test_fable_rewrite_covers_pack`).

### 2. Deploy: sandboxed installs with a launcher

- **Goal:** by default the pack no longer touches `~/.claude`. Sandboxed installs let the owner
  run token providers in parallel and try Claude Code versions or agent defaults side by side.
- **Scope:**
  - In: default target `~/.config/claude-supervisor`, launcher `claude-supervisor`.
  - In: `--tag <tag>` targets `~/.config/claude-<tag>`; `--global` installs into `~/.claude`.
  - In: a tagged install copies (not symlinks) selected items of `~/.claude` into its dir, then
    installs a `claude-<tag>` launcher into `~/.local/bin` (prefix configurable) that runs
    `claude` with `CLAUDE_CONFIG_DIR` set to that dir.
  - In: tagged uninstall removes `~/.config/claude-<tag>` and its launcher; `--global` uninstall
    removes only the pack's additions, manifest-driven as today.
- **Decisions already made:** sandboxed default; `--global` is opt-in; copies, not symlinks.
- **Left to planner, settle with the owner:**
  - Which `~/.claude` items are copied (candidates: settings, CLAUDE.md, agents, skills,
    commands, plugins) and which never are (candidates: credentials, history, sessions, caches).
  - How today's target resolution (`--target`, else `$CLAUDE_CONFIG_DIR`, else `~/.claude`;
    `scripts/deploy:116`) fits the new modes.
  - Whether a tagged install still sets the `agent` key in its `settings.json`.
  - Verify that `CLAUDE_CONFIG_DIR` is the supported mechanism for the launcher.
- **Done when:**
  - `install`, `status`, and `uninstall` work in tagged and global modes, with tests for both.
  - `docs/deploy.md`, README, and `CLAUDE.md` are updated.
- **Pointers:** `scripts/deploy` (~116, target resolution), `docs/deploy.md`,
  `tests/test_deploy.py`.

### 3. Pack-wide line reflow and length lint

- **Goal:** all `pack/` body lines are <= 100 chars, enforced by a lint.
- **Scope:**
  - In: reflow `pack/` bodies; add the lint to `tests/test_pack_lint.py`.
  - Out: wording changes.
- **Decisions already made:** an explicit exemption list, only for lines that cannot split
  (e.g. table rows).
- **Background at time of writing:** 228 body lines > 100 chars, 166 > 120, longest 609.
- **Done when:**
  - The lint passes with no or a tiny exemption list.
  - `git diff --stat` shows only pack files, the test, and `VERSION`.
- **Pointers:** `pack/`, `tests/test_pack_lint.py`.

### 4. Persistence for long programs (deferred)

- **Goal:** carry decisions and run history across long multi-package programs.
- **Scope:**
  - In, in order of value: per-project `docs/decisions.md` (append-only, one line per decision);
    a run logbook index (one line per top-level dispatch); an `## Assumptions` section in plans.
  - Out: a standalone RAID register; issues separate from Todo (both rejected).
- **Decisions already made:** start only after the work-package flow has run on a real
  multi-package task and gaps are observed.
- **Done when:** the owner has chosen which candidates to adopt and they are implemented with
  the minimum rule text.
- **Pointers:** README (work packages), `docs/architecture.md`.

### 5. Housekeeping

- **Goal:** clear three loose ends.
- **Scope:**
  - (a) `.claude/worktrees/rebrand-claude-supervisor/` (branch
    `worktree-rebrand-claude-supervisor`) is locked by a Claude session and holds untracked
    `docs/research/rebrand-claude-supervisor.md` (relevant to item 2) and
    `docs/research/publish-sensitivity-audit.md`. Confirm with the owner that the session is
    done and whether to keep those files, then `git worktree remove --force --force <path>` and
    add `.claude/worktrees/` to `.gitignore`.
  - (b) Confirm the three Mermaid diagrams in `README.md` render on the repo's web UI; fix the
    syntax if not.
  - (c) Resolved: the Claude Code port research doc was deleted and its `README.md` link removed.
- **Decisions already made:** none.
- **Done when:** each sub-item is resolved or the owner declined it.
- **Pointers:** `README.md`, `.gitignore`.
