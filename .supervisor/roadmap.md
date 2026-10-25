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

### 2. Make room in supervisor.md

`pack/agents/supervisor.md` is at its Main word cap (raised to the smallest multiple of 10 that
fit, twice, for the writer-model rule and the Codex critic; now 1039 of 1040), and Program logs for flat plans needs a clause
there. The owner chose (2026-10-21) to keep the cap and cut: propose specific cuts to the owner
for approval before adding clauses; a cap raise is minimal, on a multiple of 10, per
`.supervisor/memory/decisions/2026-10-24-raise-a-word-cap-only-on-the-owner-s-sa.md`.
Priority: normal — unblocks Program logs for flat plans. Effort: S.

### 3. Roadmap intake: tell users they can add items

The README does not say the roadmap takes user-added tasks. Candidates: an "Adding to the
roadmap" README section (hand-editing `.supervisor/roadmap.md`, with the item format), and a
supervisor "add to the roadmap: ..." path. On 2026-10-21 the owner selected neither; confirm
which, if any, before starting, or drop the item.
Priority: normal — small. Effort: S.

### 4. Program logs for flat plans

In 2.0 only programs (`## Work Packages`) get `## Log` lines appended by the post-wave clerk;
flat `## Todo` plans and child plans do not. Owner decision (2026-10-21): flat and child plans get
the same logging as programs, not deferrals only.
Depends on: Make room in supervisor.md
Priority: normal. Effort: M.

### 5. Configurable model tiers for alternative providers

Let users map the Opus/Fable, Sonnet and Haiku tiers to custom model names when using local or
third-party providers that implement the Anthropic API via API keys. Owner direction
(2026-10-21): when an install is configured with an API key, `deploy` asks whether to configure
the tiers, lists the provider's available models, and lets the user pick one per tier by number
or by typing a name. `deploy` stays standard-library-only.
Priority: normal. Effort: M.

### 6. Science artefacts (future release)

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

### 7. Re-measure harness efficiency (from late November 2026)

Once a few weeks of v6.0 sessions exist, run `python3 -I tools/audit/audit.py` and compare with
`.supervisor/memory/facts/2026-10-24-efficiency-baseline-for-drift.md`. Tune the scope-critic skip
condition and the executor single-unit rule on the numbers. Output is never committed.
Decisions:
- `.supervisor/memory/decisions/2026-10-24-every-lead-does-a-single-unit-itself-and.md`
- `.supervisor/memory/decisions/2026-10-24-tools-audit-is-opt-in-tooling.md`

Priority: low — opt-in check, not before late November 2026. Effort: S.

### 8. Chore: bring supervisor.md back under 1000 words

`pack/agents/supervisor.md` is at 1039 of 1040 words; cut it back below 1000 with the owner's
approval of each cut. Optionally do the same for the lead-loop skill (1371 of 1380).
Decisions:
- `.supervisor/memory/decisions/2026-10-24-raise-a-word-cap-only-on-the-owner-s-sa.md`

Priority: low. Effort: S.

### 9. Codex critic follow-ups (optional)

Only if the need shows up: a Haiku relay agent for UI visibility if the Bash-line description of
the Codex review call proves insufficient; an interpreter-path setting so Codex can run tests
(`.supervisor/memory/facts/2026-10-24-codex-read-only-sandbox-cannot-run-te.md`).
Priority: low. Effort: S.
