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
- Plans live in `.supervisor/working/plans/plan-<topic>.md`; the `curator` archives finished ones
  to `.supervisor/archive/working/plans/`. Long tasks may use work packages (`## Work Packages`
  in the plan; see README).
- Owner's style rule is simplicity: add rules to agent files only for observed failures, no
  anticipated-failure clauses, keep word counts and line lengths down. Body word caps per tier
  are linted in `tests/test_pack_lint.py`; do not raise a cap without the owner's approval.
- Items are ordered; each cites its decision entries under `Decisions:` and the items it needs,
  by title, under `Depends on:`. Pick one item per change set; the `curator` moves it to
  `.supervisor/history.md` at close-out.

## Items

Ordering (2026-10-21): priority first, effort second, so a large high-priority item outranks
small lower-priority ones; an item that another needs comes before it.

### 1. Persistence and long-term memory (2.x)

- **Goal:** carry decisions, run history and distilled knowledge across sessions, packages and
  programs, in a committed project store that agents read just in time.
- **Background:** the earlier gate (run the work-package flow on a real multi-package task) was
  met by the install-lifecycle program
  (`.supervisor/archive/working/plans/plan-install-lifecycle.md`, P1-P4 at L326-365). Gaps
  observed there:
  - Glue Todo items (commit + install for P1-P4: L422, L428, L433, L437) were left unticked
    because installs were deferred; nothing records why.
  - The pack has no memory today: no decision file, logbook or `## Assumptions` section exists,
    and the supervisor's "memory files" clause names no files.
- **Scope:**
  - In: Stage 5 below, after v2.0 (Stages 1-3) and Stage 4, both shipped (see
    `.supervisor/archive/working/plans/plan-memory-v2.md`).
  - Out: a standalone RAID register; issues separate from Todo (both rejected); vector or graph
    stores and external services (the pack stays service-free).
- **Decisions:**
  - `.supervisor/memory/decisions/2026-10-21-the-owner-confirms-open-decisions-at.md`
  - `.supervisor/memory/decisions/2026-10-21-memory-work-was-developed-on-a-feature.md`
  - `.supervisor/memory/decisions/2026-10-21-project-memory-lives-in-supervisor-in.md` (D1)
  - `.supervisor/memory/decisions/2026-10-21-store-layout-is-memory-per-kind-working-2.md` (D2)
  - `.supervisor/memory/decisions/2026-10-21-research-and-plans-live-in-supervisor.md` (D3)
  - `.supervisor/memory/decisions/2026-10-21-a-sonnet-curator-curates-memory-clerk.md` (D4)
  - `.supervisor/memory/decisions/2026-10-21-the-post-wave-clerk-records-mid-program.md` (D5)
  - `.supervisor/memory/decisions/2026-10-21-expiry-flags-an-entry-when-its-affects.md` (D6)
  - `.supervisor/memory/decisions/2026-10-21-memory-holds-decisions-then-facts.md` (D7)
  - `.supervisor/memory/decisions/2026-10-21-writing-rules-are-conventions-per-draft.md` (D8)
  - `.supervisor/memory/decisions/2026-10-21-stages-1-3-of-memory-land-together-as-v2.md` (D9)
  - `.supervisor/memory/decisions/2026-10-21-no-retrieval-hooks-in-v2-0-add-one-only.md` (D10)
  - `.supervisor/memory/decisions/2026-10-21-one-file-per-entry-kinds-decision-fact.md` (D11)
  - `.supervisor/memory/decisions/2026-10-21-one-off-directories-persist-nothing-and.md`
  - `.supervisor/memory/decisions/2026-10-21-no-supervisor-word-cap-raise-the-archive.md` (word cap)
  - `.supervisor/memory/decisions/2026-10-21-agent-names-are-roles-quick-edit-became.md`
  - `.supervisor/memory/decisions/2026-10-21-three-horizons-goals-roadmap-supervisor.md`
- **Done when:** v2.0 (Stages 1-3) and Stage 4 shipped; see `.supervisor/history.md`. Stage 5
  lands as a 2.x change set per its own done-when and is removed here when it lands.
- **Pointers:** `.supervisor/working/research/research-memory.md` (sections 8-11: architecture,
  staged proposal, D1-D11, risks); `.supervisor/archive/working/plans/plan-memory-v2.md` (the
  v2.0 plan).

Priority: high — active goal; finishes the memory feature; follows the small deploy items
that make its dev cycle cleaner. Effort: L.

#### Stage 5 (conditional): Retrieval automation

- **Goal:** relevant memory arrives without an explicit lookup step.
- **Scope:** a SessionStart or SubagentStart hook injecting active entry summaries, shipped in
  `supervisor.md` frontmatter.
- **Done when:** it fixes an observed failure after v2.0 or Stage 4 (a relevant entry missed).
  Start this stage only on such a failure.
- **Dependencies:** v2.0.
- **Decisions:**
  - `.supervisor/memory/decisions/2026-10-21-no-retrieval-hooks-in-v2-0-add-one-only.md` (D10)

### 2. Make room in supervisor.md

`pack/agents/supervisor.md` is at its 1000-word Main cap, and Program logs for flat plans needs a
clause there. The owner chose (2026-10-21) to keep the cap and cut: propose specific cuts to the
owner for approval before adding clauses.
Priority: normal — unblocks Program logs for flat plans. Effort: S.

### 3. Roadmap intake: tell users they can add items

The README does not say the roadmap takes user-added tasks. Candidates: an "Adding to the
roadmap" README section (hand-editing `.supervisor/roadmap.md`, with the item format), and a
supervisor "add to the roadmap: ..." path. On 2026-10-21 the owner selected neither; confirm
which, if any, before starting, or drop the item.
Priority: normal — small. Effort: S.

### 4. Light path for small prose revisions

A one-paragraph `revise` currently runs the full writer lead with writer–critic–scope-critic
rounds. Owner decisions (2026-10-21): the writer defaults to `Review: light` below a size
threshold (the planner proposes the threshold), and scope-critic reviews writer output only under
`Review: full`.
Priority: normal. Effort: M.

### 5. Program logs for flat plans

In 2.0 only programs (`## Work Packages`) get `## Log` lines appended by the post-wave clerk;
flat `## Todo` plans and child plans do not. Owner decision (2026-10-21): flat and child plans get
the same logging as programs, not deferrals only.
Depends on: Make room in supervisor.md
Priority: normal. Effort: M.

### 6. Configurable model tiers for alternative providers

Let users map the Opus/Fable, Sonnet and Haiku tiers to custom model names when using local or
third-party providers that implement the Anthropic API via API keys. Owner direction
(2026-10-21): when an install is configured with an API key, `deploy` asks whether to configure
the tiers, lists the provider's available models, and lets the user pick one per tier by number
or by typing a name. `deploy` stays standard-library-only.
Priority: normal. Effort: M.

### 7. Memory across branches and worktrees (future release)

`.supervisor/memory/` is versioned, so feature branches and worktrees can diverge in memory
state; define how conflicting or duplicate entries are reconciled when a feature is merged
(supersede rules, curator pass at merge, or merge-time report). Undecided.
Priority: low — future release. Effort: L.

### 8. Science artefacts (future release)

- **Goal:** support scientific workflows, the third use the supervisor targets alongside coding
  and writing/information management.
- **Scope:** artefacts live under `artefacts/` in date- or time-stamped subdirectories. Each holds
  a README (what we were trying to do, what we learned) next to the figures, data files and other
  output. Likely needs a new skill.
- **Depends on:** Persistence and long-term memory (artefact READMEs may feed long-term memory)
- **Left to planner:**
  - Is `artefacts/` at the repo root an accepted exception to `.supervisor/` as the one root?
  - Stamp format: date, time, or date plus a slug?
  - Which agent writes the artefacts, and which the README?
  - What feeds long-term memory, and who distills it?
  - How are large data files handled?
- **Done when:** a scientific run leaves a stamped `artefacts/` subdirectory whose README states
  the goal and what was learned, with its outputs beside it; the suite passes.
- **Pointers:** `.supervisor/working/research/research-memory.md` section 8 item 7.

Priority: low — deferred by the owner 2026-10-21 to a future release. Effort: L.
