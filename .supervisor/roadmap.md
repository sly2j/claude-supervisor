# Roadmap

## Context

- This repo is the source of a Claude Code agent pack. `pack/` deploys via `deploy`
  (stdlib-only, Python 3.9, which macOS ships as `/usr/bin/python3`).
- Work goes through the supervisor harness: `researcher`/`planner`/`executor`/`writer` leads with
  worker fan-out and `critic`/`scope-critic` loops; quick tier `fixer`/`git-ops`/`scout`.
- Before touching the pack, read `CLAUDE.md`, `docs/architecture.md`, and the `agent-authoring`
  skill (`pack/skills/agent-authoring/SKILL.md`).
- Per change set on `main`: edit, bump `VERSION` once (`X.y` -> `X.y+1`; a major branch's squash
  merge sets `X.0`), run `python3 -m pytest -q`, run `./deploy install` if `pack/` changed, commit
  with the trailer exactly `Co-Authored-By: Supervisor for Claude`, push.
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

Only retrieval automation remains; the store itself and its curation shipped (see
`.supervisor/history.md`).

#### Retrieval automation (conditional)

- **Goal:** relevant memory arrives without an explicit lookup step.
- **Scope:** a SessionStart or SubagentStart hook injecting active entry summaries, shipped in
  `supervisor.md` frontmatter.
- **Done when:** it fixes an observed failure (a relevant entry missed at contract time). Start
  this stage only on such a failure.
- **Decisions:**
  - `.supervisor/memory/decisions/2026-10-24-no-sessionstart-or-subagentstart-hook.md`

Priority: high. Effort: M.

### 2. Roadmap intake: tell users they can add items

The README does not say the roadmap takes user-added tasks. Candidates: an "Adding to the
roadmap" README section (hand-editing `.supervisor/roadmap.md`, with the item format), and a
supervisor "add to the roadmap: ..." path. On 2026-10-21 the owner selected neither; confirm
which, if any, before starting, or drop the item.
Priority: normal — small. Effort: S.

### 3. Program logs for flat plans

In 2.0 only programs (`## Work Packages`) get `## Log` lines appended by the post-wave fixer;
flat `## Todo` plans and child plans do not. Owner decision (2026-10-21): flat and child plans get
the same logging as programs, not deferrals only. `pack/agents/supervisor.md` has 23 words of
headroom under its Main cap; wording trims need no owner approval, but cutting rules to fit does
(`.supervisor/memory/decisions/2026-10-25-raising-a-pack-word-cap-is-owner-only.md`).
Priority: normal. Effort: M.

### 4. Configurable model tiers for alternative providers

Let users map the Opus/Fable, Sonnet and Haiku tiers to custom model names when using local or
third-party providers that implement the Anthropic API via API keys. Owner direction
(2026-10-21): when an install is configured with an API key, `deploy` asks whether to configure
the tiers, lists the provider's available models, and lets the user pick one per tier by number
or by typing a name. `deploy` stays standard-library-only.
Priority: normal. Effort: M.

### 5. Science artefacts (future release)

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

### 6. Re-measure harness efficiency (from late November 2026)

Once a few weeks of v6.0 sessions exist, run `python3 -I tools/audit/audit.py` and compare with
`.supervisor/memory/facts/2026-10-24-efficiency-baseline-for-drift.md`. Tune the scope-critic skip
condition and the executor single-unit rule on the numbers. Output is never committed.
Decisions:
- `.supervisor/memory/decisions/2026-10-24-every-lead-does-a-single-unit-itself-and.md`
- `.supervisor/memory/decisions/2026-10-24-tools-audit-is-opt-in-tooling.md`

Priority: low — opt-in check, not before late November 2026. Effort: S.

### 7. Haiku relay agent for the Codex critic (optional)

Only if the transcript visibility of the Codex critic step proves insufficient: a thin
`codex-critic` Haiku relay subagent, so the step shows as an agent launch. The current two-call
Bash-description approach (`critic: check review backend` and `critic → codex <model> <effort>,
round N`) was judged adequate in the smoke test.
Decisions:
- `.supervisor/memory/decisions/2026-10-24-critic-step-is-two-calls.md`

Priority: low. Effort: S.

### 8. Interpreter-path setting so Codex can run tests (optional)

Only if the need shows up: a setting naming the Python interpreter for Codex's sandbox, so Codex
can run the tests (`.supervisor/memory/facts/2026-10-24-codex-read-only-sandbox-cannot-run-tests.md`).
Priority: low. Effort: S.
