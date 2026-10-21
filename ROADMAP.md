# Roadmap

## Context

- This repo is the source of a Claude Code agent pack. `pack/` deploys via `deploy`
  (stdlib-only, Python 3.9, which macOS ships as `/usr/bin/python3`).
- Work goes through the supervisor harness: `researcher`/`planner`/`executor`/`writer` leads with
  worker fan-out and `critic`/`scope-critic` loops; quick tier `clerk`/`git-ops`/`scout`.
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
  per change set; the `curator` moves it to `.supervisor/history.md` at close-out.

## Items

Ordering (2026-10-21): priority first, effort second, so a large high-priority item outranks
small lower-priority ones; an item that another needs comes before it.

### 1. Launcher help instead of blind forwarding

`claude-<tag> -h` / `--help` (and unknown launcher-level flags) currently forward straight to
`claude`, so there is no way to list what the launcher offers. Show the launcher's own help page
first: its subcommands (`install`, `update`, `status`, `uninstall`, …), the tag and target it runs
with, and a closing line stating that any other arguments are forwarded unchanged to `claude` (with
`claude --help` as the pointer).
Priority: high — do early. Effort: S.

### 2. README clarity and provider neutrality

Make README less Claude-specific; reword the model-tier mentions so "Opus/Fable" reads as a
capability level ("Opus/Fable-level", e.g. for `planner`) rather than a specific product, and
remove confusion between the two names. Small, do early.
Priority: high — do early. Effort: S.

### 3. Branch and worktree versioning

- **Gap:** feature branches never touch `VERSION`, so a worktree install reports the `main`
  version it branched from. After a rebase onto a newer `main` that number reads as stale or as a
  mismatch, the version string does not tell a branch install from a `main` install of the same
  `X.y`, and `deploy update` can silently replace a branch install that is ahead with an older
  build (item 4).
- **Owner's suggestion:** `<main>-<branch>`, e.g. `1.23-worktree-zz`, with the main part updated
  at each rebase.
- **Recommended scheme:** keep `VERSION` as the `main` version only, and let `deploy` derive the
  installed version from git at install and status time:
  `<VERSION at merge-base with main>+<branch>.<commits-ahead>.g<short-sha>`, e.g.
  `2.0+memory-v2.7.g8b1d7de`. This is the PEP 440 local-version / SemVer build-metadata style and
  carries what `git describe` gives (base, commits ahead, short SHA) plus the branch. Nothing is
  edited on rebase, because the main part is read from `VERSION` at the merge-base. `deploy
  status` and the downgrade guard (item 4) compare the main version first, then commits-ahead;
  `main` installs stay plain `X.y`.
- **Touches:** in `deploy`, `read_pack_version` (reads `VERSION` from the checkout),
  `git_info`/`git_branch` (commit, dirty flag, branch), `install_cmd` (records `pack_version` in
  the manifest, prints "(was ...)"), `register_install` (`installs.json` holds no version today;
  it changes only if update needs the base ref recorded), `status_cmd` (string equality,
  `MISMATCH` flag) and `update_cmd` (no version check today; its `git clone --depth 1` has no
  merge-base, so it needs `main` fetched or a deeper clone).
  `tests/test_version.py` keeps checking `VERSION` on `main` only; new tests cover the derived
  string and the comparison.
- **Left to planner:** base ref when `main` is absent locally (`origin/main`), branch-name
  sanitizing (`/` and other characters), whether a dirty tree adds a marker.
- **Done when:** a worktree install shows the derived version in `deploy status`, it stays right
  after a rebase with no edits, `main` installs show `X.y`, and the suite passes.

Priority: high — do early. Effort: M.

### 4. deploy update: downgrade guard

When `deploy update` finds the installed version (or commit) is newer than the upstream branch it
would install — as happens when a worktree install is ahead of the pushed branch — print a warning
naming both versions and ask `Continue with the update? [y/N]`; default No. Non-interactive runs
fail unless `--yes` is passed.
Priority: high — do early, after item 3. Effort: S.

### 5. Persistence and long-term memory (2.x)

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
  - In: Stages 4-5 below, in order, after v2.0 (Stages 1-3, shipped; see
    `docs/archive/plan-memory-v2.md`).
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
    files, not read by default). `memory/` has one folder per kind, `working/` one per area, and
    `archive/` mirrors both.
  - D3: research and plans move out of `docs/` at Stage 4, for new programs plus a one-time
    migration of existing `docs/` and `docs/archive/` (the research recommended new programs only).
  - D4: a new agent, `curator`, on Sonnet, curates and maintains memory (duties in
    `pack/agents/curator.md`, shipped in v2.0); the `clerk` records, and `scout` and the leads
    retrieve. The curator does no retrieval.
  - D5: the post-wave `clerk` records mid-program decisions; no separate agent.
  - D7: memory holds decisions and facts (both shipped in v2.0); the curator proposes
    lessons, written only after the user approves them.
  - D8: writing rules move into memory. Standing Rules become `convention` entries with
    `domain: writing`; per-draft Session Decisions and Pending Verification live with the draft in
    `working/` and are archived with it; `docs/writing-rules.md` goes away. Claude Code auto
    memory keeps the user's personal cross-project preferences.
  - D9: Stages 1-3 together land as v2.0; Stages 4-5 follow as 2.x (the research recommended
    Stages 1-2 as v2.0).
  - D11: one file per entry, replacing the single-file `docs/decisions.md`. Kinds are `decision`,
    `fact`, `lesson`, `goal` and `convention` (the planner may refine the list); each entry has a
    `domain:` (e.g. `code`, `writing`, `science`). A goal stays active until met or dropped.
    Program logs go in each plan's `## Log`, replacing the separate logbook index.
  - Agent names are roles: v2.0 renamed `quick-edit` to `clerk`; `git-ops` keeps its name.
- **Left to planner:**
  - Decided at v2.0 planning (entries in `.supervisor/memory/decisions/`):
    - D6, expiry: flag entries when an `affects:` path changes; time-based archiving of `fact`
      entries only if staleness is observed.
    - D10, hooks: only after an observed retrieval failure.
    - D12, long-term work areas versus one-off jobs: superseded by D13 (one-off directories
      persist nothing).
  - Constraint (resolved in v2.0): the supervisor's body word cap was not raised; the curator
    dispatch replaced the archive `clerk` text (see `.supervisor/memory/decisions/`).
- **Done when:** v2.0 (Stages 1-3) shipped; see `.supervisor/history.md`. Stages 4 and 5 land as
  2.x change sets, each per its own done-when and removed here when it lands.
- **Pointers:** `docs/research-memory.md` (sections 8-11: architecture, staged proposal, D1-D11,
  risks); `docs/archive/plan-memory-v2.md` (the v2.0 plan; Interfaces 12 for Stage 4);
  `.supervisor/memory/decisions/` (D1-D13 entries; D12 under `archive/`).

Priority: high — active goal; finishes the memory feature; follows the small deploy items
that make its dev cycle cleaner. Effort: L.

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
  - Research goes under `.supervisor/working/research/` and plans under `working/plans/`; the
    curator archives them to `archive/working/research/` and `archive/working/plans/`, mirroring
    the live tree. Move `ROADMAP.md` to `.supervisor/roadmap.md`; each item names the `goal`
    entries it serves and lists its "Decisions already made" as references to `decision`
    entries, never as prose; landed items go to `history.md`, never to an archive (Interfaces 1,
    3 and 12 of `docs/archive/plan-memory-v2.md`).
- **Done when:** a full program writes nothing to `docs/` except documents the user asked for;
  after the migration this repo's `docs/` holds only human documentation; the procedure runs in
  another project; the suite passes.
- **Dependencies:** v2.0 (curator); D2, D3.

#### Stage 5 (conditional): Retrieval automation

- **Goal:** relevant memory arrives without an explicit lookup step.
- **Scope:** a SessionStart or SubagentStart hook injecting active entry summaries, shipped in
  `supervisor.md` frontmatter.
- **Done when:** it fixes an observed failure after v2.0 or Stage 4 (a relevant entry missed).
  Start this stage only on such a failure.
- **Dependencies:** v2.0; D10.

### 6. lead-loop: stop after a clean minor round

When a critic round returns only SHOULD/NIT findings and all are applied, do not run another
critic round; re-review only after BLOCKING fixes or new material.
Priority: normal. Effort: S.

### 7. Light path for small prose revisions

A one-paragraph `revise` currently runs the full writer lead with writer–critic–scope-critic
rounds. Add a quick-tier writing path or default to `Review: light` below a size threshold;
reconsider whether scope-critic adds value for `writer` at all.
Priority: normal. Effort: M.

### 8. Program logs for flat plans

In 2.0 only programs (`## Work Packages`) get `## Log` lines appended by the post-wave clerk;
flat `## Todo` plans and child plans do not. Decide whether flat plans should log deferrals too
(needs a supervisor clause; supervisor.md is at its word cap).
Priority: normal. Effort: M.

### 9. Configurable model tiers for alternative providers

Let users map the Opus/Fable, Sonnet and Haiku tiers to custom model names when using local or
third-party providers that implement the Anthropic API via API keys (deploy-time or settings-level
mapping).
Priority: normal. Effort: M.

### 10. Science artefacts

- **Goal:** support scientific workflows, the third use the supervisor targets alongside coding
  and writing/information management.
- **Scope:** artefacts live under `artefacts/` in date- or time-stamped subdirectories. Each holds
  a README (what we were trying to do, what we learned) next to the figures, data files and other
  output. Likely needs a new skill.
- **Decisions already made:**
  - Depends on item 5: artefact READMEs may feed long-term memory.
- **Left to planner:**
  - Stamp format: date, time, or date plus a slug?
  - Which agent writes the artefacts, and which the README?
  - What feeds long-term memory, and who distills it?
  - How are large data files handled?
- **Done when:** a scientific run leaves a stamped `artefacts/` subdirectory whose README states
  the goal and what was learned, with its outputs beside it; the suite passes.
- **Pointers:** `docs/research-memory.md` section 8 item 7.

Priority: normal, after item 5. Effort: L.

### 11. Memory across branches and worktrees (future release)

`.supervisor/memory/` is versioned, so feature branches and worktrees can diverge in memory
state; define how conflicting or duplicate entries are reconciled when a feature is merged
(supersede rules, curator pass at merge, or merge-time report).
Priority: low — future release. Effort: L.

### 12. Roadmap intake: tell users they can add items

The README does not say the roadmap takes user-added tasks. Add an "Adding to the roadmap" section:
ask the supervisor ("add to the roadmap: ...") to append an item (VERSION bump and commit), or edit
ROADMAP.md by hand. Show the format (numbered heading, 2-5 line body, `Priority: high|normal|low`
and `Effort: S|M|L` line); items are ordered by priority, then effort; `curator` moves landed items
to `.supervisor/history.md`. After item 5 (Stage 4), the README names `.supervisor/roadmap.md`.
Priority: normal — small. Effort: S.
