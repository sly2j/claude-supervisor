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
  `pack/agents/supervisor.md` (after frontmatter) is 109 lines; do not grow it.
- Items are orthogonal. Pick one item per change set; remove it from this file in the same
  commit when it lands.

## Items

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
