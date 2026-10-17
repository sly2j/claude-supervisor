# Roadmap

## Context

- This repo is the source of a Claude Code agent pack. `pack/` deploys via `deploy`
  (stdlib-only, Python 3.9, which macOS ships as `/usr/bin/python3`).
- Work goes through the supervisor harness: `researcher`/`planner`/`executor`/`writer` leads with
  worker fan-out and `critic`/`scope-critic` loops; quick tier `quick-edit`/`git-ops`/`scout`.
- Before touching the pack, read `CLAUDE.md`, `docs/architecture.md`, and the `agent-authoring`
  skill (`pack/skills/agent-authoring/SKILL.md`).
- Per change set on `main`: edit, bump `VERSION` once (`1.x` -> `1.x+1`), run
  `python3 -m pytest -q`, run `./deploy install` if `pack/` changed, commit with the trailer
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

- **Goal:** clear the remaining loose end.
- **Scope:**
  - Confirm the three Mermaid diagrams in `README.md` render on the repo's web UI; fix the
    syntax if not.
- **Decisions already made:** none.
- **Done when:** each sub-item is resolved or the owner declined it.
- **Pointers:** `README.md`.

### 6. Launcher: choose Opus or Fable at launch time

- **Goal:** `claude-<tag> --fable` launches in Fable mode; without the flag, fable-tagged agents
  run as Opus. The choice moves from install time to launch time.
- **Scope:**
  - In: deployed agent definitions always say `model: fable`; the launcher sets the environment
    variable that remaps the fable model to Opus unless `--fable` is given, then runs `claude`
    with the remaining arguments.
  - In: once the launcher carries the choice, remove the install-time rewrite (`FABLE_TOKEN`,
    `deployed_bytes`), the install `--fable` flag, the manifest `fable` boolean, and the lint
    `test_fable_rewrite_covers_pack`.
  - Out: any form of model or subscription detection.
- **Decisions already made:** definitions always use fable; the launcher sets the env var; the
  owner verified by hand that setting the env var before running `claude` works.
- **Left to planner:** the env var name (confirm with the owner); what `--global` installs
  (no launcher) do about Opus; how the prose dispatch tokens in `planner.md` and `writer.md`
  behave under the remap.
- **Done when:** launcher tests cover `--fable` on and off; `docs/deploy.md`, README, and
  `docs/architecture.md` are updated.
- **Pointers:** `deploy` (`FABLE_TOKEN`, `deployed_bytes`, `launcher_text`),
  `tests/test_deploy.py`, `tests/test_pack_lint.py`.
