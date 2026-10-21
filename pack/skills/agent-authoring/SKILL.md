---
name: agent-authoring
description: Conventions for writing and reviewing Claude Code subagent and skill definitions in the claude-supervisor pack (tiers, models, tool restrictions, prompt structure, report contracts, scope boundaries). Use when creating, editing, or critiquing files under pack/agents or pack/skills, or any .claude/agents or skills definition.
---

# Agent And Skill Authoring

## Tiers

| Tier | Agents | Model / effort | Tools |
|---|---|---|---|
| Main | supervisor | fable / default | no Bash, no NotebookEdit; writes only its memory files |
| Lead | researcher, executor, writer | opus / default | all; preload `lead-loop` |
| Lead | planner | fable / default | all; preload `lead-loop` |
| Worker | researcher-worker, planner-worker, executor-worker | sonnet / default | `disallowedTools` includes `Agent` |
| Worker | writer-worker | opus / default | `disallowedTools` includes `Agent` |
| Review | critic | opus / default | read-only plus Bash; no `Agent` |
| Review | scope-critic | fable / default | read-only, no Bash, no `Agent` |
| Memory | curator | sonnet / default | explicit allowlist; no `Agent` |
| Quick | clerk, git-ops, scout | haiku / xhigh | explicit allowlist or denylist; no `Agent` |

- `planner` dispatches `critic` with `model: fable`, and `writer` dispatches `writer-worker` with
  `model: fable` when the user asks for the strongest drafter; these per-call overrides are the only
  exceptions to the Tiers table.
- Depth is main (0) -> lead or curator (1) -> worker or reviewer (2). Nothing below depth 2
  dispatches.
- Use model aliases (`fable`, `opus`, `sonnet`, `haiku`). Pin full IDs only when reproducibility
  matters.
- One critic serves all domains. Add domain criteria to `critic.md` or to a skill it loads, not as a
  new critic agent.

## Agent Files

- Frontmatter:
  - `name` (kebab-case, equal to the filename stem)
  - `description` (one sentence that says what and when, because it drives routing)
  - `model`, `effort` (omit `effort` when the Tiers table says `default`)
  - `tools` or `disallowedTools`
  - optional `skills` (a YAML list) and `color`
- Body: start with `You are ...`, then the sections the role needs, in the order Mission or Scope,
  Rules or Operating, the domain procedure, then Report or Output.
- Budget: body word caps per tier are main 1000, lead 700, review 600, worker 400, memory 400,
  quick 350; `tests/test_pack_lint.py` enforces them. They are ceilings, not targets: spend the
  length on load-bearing contracts such as verdict tokens, output schemas, or routing tables.
- State scope boundaries with a named destination: "X goes to `executor`". When agent A routes to B,
  B's scope must accept that work.
- Keep definitions self-contained: behaviour an agent or skill needs is stated in the pack's own
  files, never delegated to the source repo's memory entries, plans, or docs, which do not exist
  where the pack is deployed.
- Agents that report upward use a bounded report with explicit size caps.
- Prefer a skill over an agent when the thing is a procedure or a body of knowledge rather than a
  role with its own model or context needs.

## Skill Files

- `skills/<name>/SKILL.md` with `name` equal to the directory name. Spend effort on the
  `description`, which triggers loading: say what it does and when to use it.
- Set `user-invocable: false` for protocol skills that agents preload. Use
  `disable-model-invocation: true` for skills that should run only by slash command.
- Keep SKILL.md under 300 lines and 1300 body words (linted). Put bulky references in
  `references/` and helpers in `scripts/`, and reference them via `${CLAUDE_SKILL_DIR}`.

## Reviewing Definitions (for critic)

Judge a definition by its likely operational effect, not its tidiness:
- Will the routing description trigger at the right times?
- Can the agent do its job with the tools it has?
- Are its boundaries reciprocal with its neighbors?
- Are its contracts checkable?
- Does it duplicate rules that live in a preloaded skill?
- Is it self-contained, or does behaviour depend on the source repo's memory, plans, or docs?

## After Changing The Pack

Update the inventory in `docs/architecture.md` (`## Agents`, `## Skills`) when an agent's name,
scope, model, or tools change. Run `python3 -m pytest -q`, which includes the pack lint, then
`./deploy install --dry-run`.
