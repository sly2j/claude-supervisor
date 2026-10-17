# Roadmap

## Context

- This repo is the source of a Claude Code agent pack. `pack/` deploys via `deploy`
  (stdlib-only, Python 3.9, which macOS ships as `/usr/bin/python3`).
- Work goes through the supervisor harness: `researcher`/`planner`/`executor`/`writer` leads with
  worker fan-out and `critic`/`scope-critic` loops; quick tier `quick-edit`/`git-ops`/`scout`.
- Before touching the pack, read `CLAUDE.md`, `docs/architecture.md`, and the `agent-authoring`
  skill (`pack/skills/agent-authoring/SKILL.md`).
- Per change set on `main`: edit, bump `VERSION` once (`X.y` -> `X.y+1`; a major branch's squash
  merge sets `X.0`), run `python3 -m pytest -q`, run `./deploy install` if `pack/` changed, commit
  with the trailer exactly `Co-Authored-By: Claude Supervisor`, push.
- Plans live in `docs/plan-<topic>.md`; finished plans move to `docs/archive/` with `git mv`.
  Long tasks may use work packages (`## Work Packages` in the plan; see README).
- Owner's style rule is simplicity: add rules to agent files only for observed failures, no
  anticipated-failure clauses, keep word counts and line lengths down. Body word caps per tier
  are linted in `tests/test_pack_lint.py`; do not raise a cap without the owner's approval.
- Items are ordered; each states its dependencies under "Decisions already made". Pick one item
  per change set; remove it from this file in the same commit when it lands.

## Items

### 1. Persistence for long programs (v2.0)

- **Goal:** carry decisions and run history across long multi-package programs.
- **Background:** the earlier gate (run the work-package flow on a real multi-package task) was
  met by the install-lifecycle program (`docs/archive/plan-install-lifecycle.md`, P1-P4 at
  L326-365). Gaps observed there:
  - A mid-program user decision (`--prefix`, `## Decisions` item 6, L408-415) was recorded only in
    the plan's ad hoc `## Decisions` section, which is now archived. `pack/agents/planner.md`
    lists no such section, and `pack/agents/supervisor.md:66-69,88` passes decisions only inside
    briefs and re-runs.
  - Glue Todo items (commit + install for P1-P4: L422, L428, L433, L437) were left unticked
    because installs were deferred; nothing records why.
  - No `docs/decisions.md`, logbook, or `## Assumptions` section exists anywhere in `pack/`,
    `docs/`, or `README.md`; `docs/archive/plan-wbs.md:276` excluded them explicitly.
- **Scope:**
  - In, in order of value: per-project `docs/decisions.md` (append-only, one line per decision);
    a run logbook index (one line per top-level dispatch); an `## Assumptions` section in plans.
  - Out: a standalone RAID register; issues separate from Todo (both rejected).
- **Decisions already made:**
  - The owner chooses which candidates to adopt; implement them with the minimum rule text.
  - Development happens on a feature branch in a separate git worktree, deployed under a dev tag
    (the dev worktree flow in `docs/deploy.md`) so the stable sandbox is untouched. It may change
    designs that are not ready for general users.
  - Lands as v2.0 (major bump per `CLAUDE.md`).
- **Left to planner:** which agent writes `docs/decisions.md` and the logbook (`supervisor` via
  `quick-edit`, or the lead that took the decision); where the tier word caps bind, since every
  candidate adds rule text to Main or Lead agents.
- **Done when:** the owner has chosen which candidates to adopt and they are implemented with the
  minimum rule text on the branch; the branch is rebased on `main` and squash-merged with
  `VERSION` set to `2.0`.
- **Pointers:** `docs/archive/plan-install-lifecycle.md` (`## Decisions` L394-415, `## Todo`
  L417+); `README.md` (Larger Work L74-140, work packages L78-91); `docs/architecture.md:43-60`;
  `pack/agents/planner.md:24-32,75-81`; `pack/agents/supervisor.md:66-69,79-92`;
  `pack/agents/executor.md:28-30,61`.
