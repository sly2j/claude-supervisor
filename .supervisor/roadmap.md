# Roadmap

## Context

- This repo is the source of Supervisor for Claude, a multi-agent orchestration layer for Claude Code. `pack/` deploys via `deploy`
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
the same logging as programs, not deferrals only. `pack/agents/supervisor.md` has 2 words of
headroom under its Main cap; wording trims need no owner approval, but cutting rules to fit does
(`.supervisor/memory/decisions/2026-10-25-raising-a-pack-word-cap-is-owner-only.md`).
Priority: normal. Effort: M.

### 5. Dangling memory references after archiving working files

Archiving a working file (plan, research, draft state) leaves citations of its old path in live
entries and archived plans. The `project-memory` skill and the `curator` archive step in `pack/`
need a way to keep those references resolving; the fix belongs in the pack, not in this repo's
memory. Recurring: five files cite `.supervisor/working/research/research-fold-subagents.md`,
which exists only under `.supervisor/archive/working/research/`. It must be backward compatible:
stores and entries written before the change keep working unchanged.
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
- **Pointers:** `.supervisor/archive/working/research/research-memory.md` section 8 item 7.

Priority: low — deferred by the owner 2026-10-21 to a future release. Effort: L.

### 7. Re-measure harness efficiency (from late November 2026)

Once a few weeks of v6.0 sessions exist, run `python3 -I tools/audit/audit.py` and compare with
`.supervisor/memory/facts/2026-10-24-efficiency-baseline-for-drift.md`. Tune the scope-critic skip
condition and the executor single-unit rule on the numbers. Output is never committed.
Decisions:
- `.supervisor/memory/decisions/2026-10-24-every-lead-does-a-single-unit-itself-and.md`
- `.supervisor/memory/decisions/2026-10-24-tools-audit-is-opt-in-tooling.md`

Priority: low — opt-in check, not before late November 2026. Effort: S.

### 8. Haiku relay agent for the Codex critic (optional)

Only if the transcript visibility of the Codex critic step proves insufficient: a thin
`codex-critic` Haiku relay subagent, so the step shows as an agent launch. The current two-call
Bash-description approach (`critic: check review backend` and `critic → codex <model> <effort>,
round N`) was judged adequate in the smoke test.
Decisions:
- `.supervisor/memory/decisions/2026-10-24-critic-step-is-two-calls.md`

Priority: low. Effort: S.

### 9. Interpreter-path setting so Codex can run tests (optional)

Only if the need shows up: a setting naming the Python interpreter for Codex's sandbox, so Codex
can run the tests (`.supervisor/memory/facts/2026-10-24-codex-read-only-sandbox-cannot-run-tests.md`).
Priority: low. Effort: S.

### 10. Verify the ALCF preset on first live use

On first live ALCF use, check that `alcf-tokens get-token inference` prints only the bare token
and that `<base URL>/v1/models` exists. If either differs, fix `deploy`'s ALCF preset. Until then
the code fails loudly or falls back to typed model ids.
Source: `.supervisor/archive/working/plans/api-access-install.md`.
Priority: normal — needs live ALCF access. Effort: S.

### 11. Argo preset (ANL), including argo-proxy URLs

Add `--provider argo` beside `openrouter`, `nrp` and `alcf`, with a section in `docs/deploy.md`
(API Providers) and tests. Findings from a manual setup (2026-10-29, Claude Code 2.1.312):
- Base URL `https://apps.inside.anl.gov/argoapi` is reachable only inside ANL or over VPN. The
  "token" is the user's ANL domain username, supplied through the token helper `echo <username>`
  (Argo's own recipe). That username can differ from `$USER`, so the preset needs a way to pass it.
- `/v1/models` lists display names (`Claude Opus 5.5`), not ids. Messages accepts the standard ids
  (`claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5`). There is no Fable, so the default
  tiers should map Fable to Opus and skip the picker, or the picker should offer the standard ids.
- Argo's recipe also sets `CLAUDE_CODE_AUTO_MODE_SERVER=0`, which turns off the server-side
  auto-mode classifier, and `CLAUDE_CODE_SKIP_ANTHROPIC_AUTH=1`, which 2.1.312 never reads (drop
  it). `deploy` has no way to set extra env vars, so a preset needs a managed `env` mechanism
  (launcher exports or managed `settings.json` keys).
- argo-proxy (a local tunnel) serves Argo at another URL. `--base-url` with `--provider argo`
  should replace only the URL, as it does for ALCF. Planner to confirm argo-proxy's path, and
  whether it needs the username helper.
- Done when: `./deploy install --tag argo-supervisor --provider argo` (with the username flag)
  reproduces the manual setup with no hand-edited `settings.json`, the same works with an
  argo-proxy `--base-url`, and the suite passes.

Priority: normal. Effort: S–M.

### 12. `--global` installs and the deploy tool (open decision)

A `--global` install has no launcher, so `memory` and `doctor` run only as `./deploy …` from a
source checkout (`docs/deploy.md`). Open decision: deprecate `--global` installs, or ship the
deploy tool with them so `memory`/`doctor` work without a checkout. The owner leans toward
deprecation (2026-10-29). Decide before starting.
Source: `.supervisor/archive/working/plans/externalize-memory.md` (D15, D19).
Priority: normal. Effort: S.
