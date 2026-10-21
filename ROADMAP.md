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

### 1. Persistence and long-term memory (v2.0, then 2.x)

- **Goal:** carry decisions, run history and distilled knowledge across sessions, packages and
  programs, in a committed project store that agents read just in time.
- **Background:** the earlier gate (run the work-package flow on a real multi-package task) was
  met by the install-lifecycle program (`docs/archive/plan-install-lifecycle.md`, P1-P4 at
  L326-365). Gaps observed there:
  - The mid-program `--prefix` decision (`## Decisions` item 6, L408-415) survives only in the
    archived plan's ad hoc `## Decisions`; `pack/agents/planner.md` lists no such section, and
    `pack/agents/supervisor.md:66-69,88` passes decisions only inside briefs and re-runs.
  - Glue Todo items (commit + install for P1-P4: L422, L428, L433, L437) were left unticked
    because installs were deferred; nothing records why.
  - The pack has no memory today: no decision file, logbook or `## Assumptions` section exists,
    and the supervisor's "memory files" clause names no files.
- **Scope:**
  - In: Stages 1-5 below, in order.
  - Out: a standalone RAID register; issues separate from Todo (both rejected); vector or graph
    stores and external services (the pack stays service-free).
- **Decisions already made:**
  - The owner confirms the open decisions at planning; implement each stage with the minimum rule
    text.
  - Development happens on a feature branch in a separate git worktree, deployed under a dev tag
    (the dev worktree flow in `docs/deploy.md`) so the stable sandbox is untouched. It may change
    designs that are not ready for general users.
  - D1: long-term project memory lives in `.supervisor/` in the repo and is committed.
  - D2: `.supervisor/` is the one root, with `working/` (short-term: active research, plans,
    program state), `memory/` (long-term, one file per entry) and `archive/` (spent working
    files, not read by default).
  - D3: research and plans move out of `docs/` at Stage 4, for new programs plus a one-time
    migration of existing `docs/` and `docs/archive/` (the research recommended new programs only).
  - D4: a new agent, `curator`, on Sonnet, curates and maintains memory (duties in Stage 3); the
    `clerk` records, and `scout` and the leads retrieve. The curator does no retrieval.
  - D5: the post-wave `clerk` records mid-program decisions; no separate agent.
  - D7: memory holds decisions from Stage 1 and facts from Stage 3; the curator proposes
    lessons, written only after the user approves them.
  - D8: writing rules move into memory. Standing Rules become `kind: convention` entries with
    `domain: writing`; per-draft Session Decisions and Pending Verification live with the draft in
    `working/` and are archived with it; `docs/writing-rules.md` goes away. Claude Code auto
    memory keeps the user's personal cross-project preferences.
  - D9: Stages 1-3 together land as v2.0; Stages 4-5 follow as 2.x (the research recommended
    Stages 1-2 as v2.0).
  - D11: one file per entry, replacing the single-file `docs/decisions.md`. Kinds are `decision`,
    `fact`, `lesson`, `goal` and `convention` (the planner may refine the list); each entry has a
    `domain:` (e.g. `code`, `writing`, `science`). A goal stays active until met or dropped. The
    curator maintains a generated, never hand-edited `memory/INDEX.md`. Program logs go in each
    plan's `## Log`, replacing the separate logbook index.
  - Agent names are roles: Stage 1 renames `quick-edit` to `clerk`; `git-ops` keeps its name.
- **Left to planner:**
  - Open decisions; each line gives the research's recommendation (D12: the owner's) as the
    default:
    - D6, expiry (default; confirm at planning): flag entries when an `affects:` path changes;
      time-based archiving of `fact` entries only if staleness is observed.
    - D10, hooks (default; confirm at planning): only after an observed retrieval failure.
    - D12, long-term work areas versus one-off jobs (default; confirm at planning): see Stage 1.
  - Constraint: the supervisor has 42 words of body headroom across Stages 1-3, the planner 87
    (Stage 2 adds plan sections). Stage 3's supervisor text (curator routing, remember/forget,
    the "recorded N" line, the active-goals read) needs either swapping the archive `clerk` text
    (`pack/agents/supervisor.md:90-91`) for the curator dispatch, or the owner's approval of a
    higher Main cap.
- **Done when:** v2.0 when Stages 1-3 meet their done-when on the dev branch and the branch is
  rebased on `main` and squash-merged with `VERSION` set to `2.0`, removing Stages 1-3; Stages 4
  and 5 then land as 2.x change sets, each per its own done-when and removed here when it lands.
- **Pointers:** `docs/research-memory.md` (sections 8-11: architecture, staged proposal, D1-D11,
  risks); `docs/archive/plan-install-lifecycle.md` (`## Decisions` L394-415, `## Todo` L417+);
  `README.md` (Larger Work L83-149, work packages L87-99); `docs/architecture.md:43-60`;
  `pack/agents/planner.md:24-32,75-81`; `pack/agents/supervisor.md:66-69,78-91` (archive
  `quick-edit` text L90-91, `clerk` after Stage 1); `pack/agents/executor.md:28-30,61`;
  `pack/skills/writing-rules-persistence/`; `deploy:767-780` (removal of dropped files).

#### Stage 1: Decision records

- **Goal:** no user decision, or lead decision that binds later stages, is lost between sessions
  or packages.
- **Scope:**
  - Rename `quick-edit` to `clerk`: the agent file and every reference in `pack/`,
    `docs/architecture.md`, README, the tests, and `docs/deploy.md` if needed. `deploy` already
    removes the old managed file on upgrade unless it was edited locally (`deploy:767-780`).
  - A new `project-memory` skill: entry schema (D11 kinds, `domain:`), naming, the supersede
    rule, validate-before-use.
  - The long-term store in `.supervisor/memory/`; each entry carries `affects:`, `verified:` and
    `source:`, and `affects:` accepts any repo path, not only code (item 2 reuses it).
  - The supervisor has the post-wave `clerk` write an entry when a user answer or lead decision
    binds later stages (about one supervisor line).
  - `lead-loop` contract step: grep the store if it exists and pass relevant entries to workers
    in briefs; workers never search memory.
  - D12, long-term work areas versus one-off jobs (default; confirm at planning):
    - Create `.supervisor/` automatically only where the directory is clearly a long-term work
      area: a git repo, a `CLAUDE.md` or `.claude/`, an Obsidian vault (`.obsidian/`), an
      existing `.supervisor/`, or the user says so.
    - A clear one-off job gets scratch only: short-term working files go to a user-global
      scratch area under the deployed config dir, keyed by path and pruned by age, and only
      personal preferences persist, via auto memory.
    - When the signals are ambiguous, the supervisor asks the user once whether this is a
      long-term project or work area; when they are clear either way, it never asks.
    - The staleness check falls back to file mtime when git is absent.
    - Left to the planner: the exact signal list, retention and pruning, and the store without
      git.
- **Done when:** on the dev tag, a program's mid-program decision is recorded as an entry; a new
  session's planner cites it unprompted; the suite passes with no cap raised.
- **Dependencies:** D1, D2, D5, D11, D12.

#### Stage 2: Program state that explains itself

- **Goal:** a resumed session can say what ran, what was deferred, and why.
- **Scope:**
  - `## Assumptions` and `## Log` sections in plans (`planner.md` required sections).
  - The post-wave `clerk` appends one log line per top-level dispatch, deferrals included (such
    as the unticked glue items).
  - The supervisor's resume `scout` call returns the log tail.
- **Done when:** on a replay of an install-lifecycle-style program, `scout` answers "why is L422
  unticked" from the plan alone.
- **Dependencies:** none; uses Stage 1 entries if present.

#### Stage 3: Curator close-out

- **Goal:** finished programs leave distilled knowledge behind, and nothing stale in view.
- **Scope:**
  - A new `curator` agent. At close-out it merges duplicates, settles contradictions by
    superseding, re-verifies facts, decides keep or discard, distills spent research and plans,
    and archives; it also runs migrations and handles "remember X" / "forget X". It replaces
    the archive `clerk` step, and also runs on request and after a single-stage run that
    produced a user decision.
  - `fact`, `goal` and `convention` entries start here; the curator proposes lessons (D7) and
    maintains `memory/INDEX.md` (D11).
  - The supervisor reads active goals when it starts on a project.
  - Writing rules move into memory (D8): `writing-rules-persistence` is reworked or folded into
    `project-memory` (the planner's call), per-draft state goes to `.supervisor/working/`,
    created here, and the curator migrates an existing `docs/writing-rules.md` (this repo has
    none).
  - Tier table and `docs/architecture.md` inventory updates.
- **Done when:** closing a dev-tag program yields a few entries, each with `source:` and
  `affects:`, plus an archived plan; a seeded contradictory entry ends up superseded; an entry
  whose `affects:` file changed is re-verified or superseded; a seeded `docs/writing-rules.md`
  migrates to `convention` entries that a writer run then applies.
- **Dependencies:** Stage 1 (store); D4, D6, D7, D8, D11; the supervisor headroom constraint
  above.

**v2.0 boundary:** Stages 1-3 above land together as v2.0; Stages 4-5 below are 2.x change sets.

#### Stage 4: Move the working set out of `docs/`

- **Goal:** agent working state is separate from the project's human documentation.
- **Scope:**
  - New programs write research, plans and logs under `.supervisor/working/`; the curator
    archives spent ones to `.supervisor/archive/`.
  - Path updates in `researcher`, `planner`, `supervisor`, `executor`, README and
    `docs/architecture.md`.
  - One-time migration: the curator sweeps this repo's `docs/` research and plans and
    `docs/archive/`, distills the decisions and facts still in force into `.supervisor/memory/`,
    and moves the rest into `.supervisor/archive/`, so old plans do not linger as stale memory.
    It ships as a reusable procedure that other projects using the pack can run.
- **Done when:** a full program writes nothing to `docs/` except documents the user asked for;
  after the migration this repo's `docs/` holds only human documentation; the procedure runs in
  another project; the suite passes.
- **Dependencies:** Stage 3 (archive owner); D2, D3.

#### Stage 5 (conditional): Retrieval automation

- **Goal:** relevant memory arrives without an explicit lookup step.
- **Scope:** a SessionStart or SubagentStart hook injecting active entry summaries, shipped in
  `supervisor.md` frontmatter.
- **Done when:** it fixes an observed failure from Stages 1-4 (a relevant entry missed). Start
  this stage only on such a failure.
- **Dependencies:** Stages 1-3; D10.

### 2. Science artefacts

- **Goal:** support scientific workflows, the third use the supervisor targets alongside coding
  and writing/information management.
- **Scope:** artefacts live under `artefacts/` in date- or time-stamped subdirectories. Each holds
  a README (what we were trying to do, what we learned) next to the figures, data files and other
  output. Likely needs a new skill.
- **Decisions already made:**
  - Depends on item 1: artefact READMEs may feed long-term memory.
- **Left to planner:**
  - Stamp format: date, time, or date plus a slug?
  - Which agent writes the artefacts, and which the README?
  - What feeds long-term memory, and who distills it?
  - How are large data files handled?
- **Done when:** a scientific run leaves a stamped `artefacts/` subdirectory whose README states
  the goal and what was learned, with its outputs beside it; the suite passes.
- **Pointers:** `docs/research-memory.md` section 8 item 7.

### 3. README clarity and provider neutrality

Make README less Claude-specific; reword the model-tier mentions so "Opus/Fable" reads as a
capability level ("Opus/Fable-level", e.g. for `planner`) rather than a specific product, and
remove confusion between the two names. Small, do early.

### 4. Configurable model tiers for alternative providers

Let users map the Opus/Fable, Sonnet and Haiku tiers to custom model names when using local or
third-party providers that implement the Anthropic API via API keys (deploy-time or settings-level
mapping).

### 5. Light path for small prose revisions

A one-paragraph `revise` currently runs the full writer lead with writer–critic–scope-critic
rounds. Add a quick-tier writing path or default to `Review: light` below a size threshold;
reconsider whether scope-critic adds value for `writer` at all.

### 6. lead-loop: stop after a clean minor round

When a critic round returns only SHOULD/NIT findings and all are applied, do not run another
critic round; re-review only after BLOCKING fixes or new material.

### 7. Program logs for flat plans

In 2.0 only programs (`## Work Packages`) get `## Log` lines appended by the post-wave clerk;
flat `## Todo` plans and child plans do not. Decide whether flat plans should log deferrals too
(needs a supervisor clause; supervisor.md is at its word cap).

### 8. Memory across branches and worktrees (future release)

`.supervisor/memory/` is versioned, so feature branches and worktrees can diverge in memory
state; define how conflicting or duplicate entries are reconciled when a feature is merged
(supersede rules, curator pass at merge, or merge-time report).

### 9. deploy update: downgrade guard

When `deploy update` finds the installed version (or commit) is newer than the upstream branch it
would install — as happens when a worktree install is ahead of the pushed branch — print a warning
naming both versions and ask `Continue with the update? [y/N]`; default No. Non-interactive runs
fail unless `--yes` is passed.
Priority: high — do early.

### 10. Launcher help instead of blind forwarding

`claude-<tag> -h` / `--help` (and unknown launcher-level flags) currently forward straight to
`claude`, so there is no way to list what the launcher offers. Show the launcher's own help page
first: its subcommands (`install`, `update`, `status`, `uninstall`, …), the tag and target it runs
with, and a closing line stating that any other arguments are forwarded unchanged to `claude` (with
`claude --help` as the pointer).
Priority: high — do early.
