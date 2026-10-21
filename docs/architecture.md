# Architecture

## Overview

```
                         user
                          |
                    supervisor (fable)                         depth 0 (main thread)
         ________________|___________________________
        |  Mode 1: full harness                      |  Mode 2: quick tier (haiku)
        |                                            |
  researcher  planner   executor   writer            clerk   git-ops  scout  curator  depth 1
   (opus)    (fable)    (opus)     (opus)                                    (sonnet)
      |         |          |          |
      |   N parallel workers (one wave per message)                              depth 2
      |   researcher-worker (sonnet) | planner-worker (sonnet) | executor-worker (sonnet) | writer-worker (opus; fable on request)
      |
      +--> critic (opus, xhigh; fable when planner calls)                       depth 2
      +--> scope-critic (fable) -- rules on the critic's findings, lists cuts    depth 2
      |
      lead decides -> fix (re-dispatch) -> review delta -> ... (cap 3 rounds)
```

## Agents

| Agent | Role | Model / effort | Tools |
|---|---|---|---|
| `supervisor` | Main thread: routing, briefing, synthesis | fable / high | all except Bash, NotebookEdit |
| `researcher` | Lead: research artifacts in `docs/research-*.md` | opus / high | all |
| `planner` | Lead: implementation plans in `docs/plan-*.md` | fable / xhigh | all |
| `executor` | Lead: code, tests, config, agent definitions, conflicts, Python environments | opus / high | all |
| `writer` | Lead: scientific and technical prose, slide content, project docs | opus / high | all |
| `researcher-worker` | Worker: one bounded investigation | sonnet / high | all except Agent, Edit, NotebookEdit |
| `planner-worker` | Worker: one bounded repo question for a plan | sonnet / high | all except Agent, Write, Edit, NotebookEdit |
| `executor-worker` | Worker: one unit of change in its assigned files | sonnet / high | all except Agent |
| `writer-worker` | Worker: extracts sources, drafts and revises prose | opus / high (fable on request) | all except Agent |
| `critic` | Reviewer: quality and compliance, PASS/REVISE; applies the project's REVIEW.md when present | opus / xhigh (fable when called by planner) | read-only plus Bash |
| `scope-critic` | Reviewer: KEEP/DOWNGRADE/DROP rulings and CUT list | fable / high | read-only, no Bash |
| `clerk` | Quick: small, exact edits; records memory entries as briefed | haiku / xhigh | Read, Edit, Write, Glob, Grep, Bash |
| `curator` | Memory: closes out finished plans (distills decisions, facts, goals; archives them); remember/forget/make this a project; migrates legacy writing rules; archives draft state | sonnet / high | Read, Edit, Write, Glob, Grep, Bash |
| `git-ops` | Quick: routine git with guardrails | haiku / xhigh | Bash, Read, Glob, Grep |
| `scout` | Quick: read-only lookups | haiku / xhigh | read-only plus Bash |

## Mode 1: The Lead Loop

All four leads preload the `lead-loop` skill (`pack/skills/lead-loop/SKILL.md`):

1. **Contract.** Goal, acceptance criteria, in/out of scope, constraints.
2. **Fan-out.** N independent units (1-6) dispatched in one message. Units never share files. Dependent units run in waves.
3. **Integrate.** Merge reports and run cheap validation.
4. **critic.** BLOCKING/SHOULD/NIT findings with evidence, then a PASS/REVISE verdict. It applies the project's root REVIEW.md and any REVIEW.md in a directory holding a changed file or the artifact, after the brief's contract.
5. **scope-critic.** Rules KEEP/DOWNGRADE/DROP on each critic finding, lists CUTs of existing bloat, and returns a LEAN/TRIM verdict.
6. **Decide.** The lead fixes kept BLOCKING findings and applies CUTs, and logs every overrule.
7. **Loop or stop.** Done or cap (3 rounds), each followed by a bounded report. Round 2 and later review only a diff of the fixes. When the critic re-raises a finding the lead already addressed or rejected, it survives; on its second survival (stalemate) the lead decides it and logs the decision.

The supervisor's brief sets the review depth: `Review: full` (default, the loop above), `light` (one critic round, then scope-critic, iteration only on BLOCKING findings), or `none` (the lead self-validates). The planner defaults to one review round, because the user reviews the plan next.

Why two critics? A single critic improves correctness but drifts toward defensive additions: extra validation, caveats, edge cases nobody has, and "for completeness" sections. Each one sounds reasonable, so a lead that accepts every finding grows the artifact every round. `scope-critic` sees the original request and the critic's findings together, and its only job is to say which findings the contract actually needs. It is barred from adding requirements, so it cannot become a third source of growth.

**Work packages.** A plan may carry a `## Work Packages` section: a breakdown into packages with disjoint ownership, dependencies, and the stages each needs, which the supervisor runs as a program one wave at a time. The rules are in `pack/agents/planner.md` (`## Work Packages`) and `pack/agents/supervisor.md` (`## Programs`); the README's `## Larger Work` section has the diagrams. After each wave, one `clerk` advances each package's `Status`, appends each lead's `Log:` line to the plan's `## Log`, and applies any `Amend parent:`: a package's planner splits it by returning new packages for the parent plan, so plans never nest. A blocked package is skipped until the user answers, which re-runs its stage. When every package is `done` (or a flat plan's `## Todo` is complete), `curator` closes the plan out: it distills decisions, facts, and goals into memory, then archives the plan, its child plans, and its research to `docs/archive/`.

## Mode 2: The Quick Tier

The supervisor dispatches one Haiku specialist directly, with no review loop. The Sonnet `curator` is the other direct dispatch: close-out, "remember X" / "forget X" / "make this a project", and recording a single-stage decision. Specialists reply with `ESCALATE:` when the task turns out to be larger, ambiguous, or risky. The supervisor then re-routes the task to Mode 1, passing along the specialist's findings.

## Routing

The supervisor picks the mode. An explicit user choice ("quick", "full") wins. Otherwise Mode 2 applies only when the task is fully specified, small, local, needs no design decision, and is cheap to undo. Larger work chains through the leads: `researcher` -> `planner` -> user approval -> `executor`, skipping stages that add nothing. Mechanical multi-file work gets `Review: light`.

Git conflicts: `git-ops` never resolves them. It returns a structured `ESCALATE` (operation, both sides, conflicted files with hunk counts and mechanical flags). The supervisor sends easy conflicts to `executor` with `Review: light`, and hard ones through `researcher` -> `planner` -> user approval -> `executor`.

## Models And Cost

The full assignment is in the [Agents](#agents) table. Fable runs where judgment has the most leverage: the supervisor's routing, the planner's plans, and scope-critic's resistance to reasonable-sounding additions. The critic runs on Opus at xhigh effort, and planner overrides it to Fable for plan reviews, and writer can override writer-worker to Fable when the user asks for the strongest drafter. writer-worker runs on Opus because voice matching and AI-tell avoidance need the stronger model, and it usually runs as a single drafter and fans out only for source extraction. The other workers run on Sonnet and the quick tier on Haiku. Deployed agents keep `model: fable`; the sandbox launcher maps Fable to Opus unless started with `--fable` (see `docs/deploy.md`).

A Mode 1 round costs N worker calls plus three more (critic, scope-critic, and the lead's own turns). Mode 2 costs one Haiku call, and a plan close-out one Sonnet call. Routing small work to Mode 2 is the main cost control; `Review: light` drops the extra rounds for mechanical Mode 1 work.

## Memory

Three horizons: long-term `goal` entries, a mid-term roadmap, and short-term plans. The store `.supervisor/` holds `memory/<kind>/` (entries in force), `working/` (per-document writer state), `archive/`, and `history.md` (one line per landed item). Folders carry fixed properties (an entry's kind), labels carry changing ones, and the archive mirrors the live tree. The `clerk` records, the `curator` curates, and `writer` owns `working/writing/`. Leads read matching entries at contract time, `scout` reads for the supervisor, and workers never read. Entries are claims to validate before use; a change supersedes the old entry and moves it to `archive/`. The curator writes at most five new entries per run. Outside a project (a git repo, or a directory with `.supervisor/`, `.claude/`, `CLAUDE.md` or `AGENTS.md` here or above, never counting `$HOME` or its ancestors; a git toplevel outranks anything above it) nothing is stored until the user opts in ("remember X", "make this a project", or a close-out). Stage 4 moves research, plans, and the roadmap into `.supervisor/`.

## Skills

| Skill | Used by | Origin |
|---|---|---|
| lead-loop | all leads (preloaded) | new |
| project-memory | clerk, curator, writer, writer-worker (preloaded); leads via lead-loop; critic on demand | new |
| git-safety | executor, git-ops (preloaded); executor reads `references/conflict-resolution.md` on unmerged paths | old git-expert + conflict-resolver |
| python-env | executor, executor-worker | old python-maintainer |
| agent-authoring | executor, executor-worker, critic | old agent-builder/agent-critic + AGENTS.md |
| science-writing-style, presentation-style | writer-worker, critic | ported |
| document-extraction, email-extraction, meeting-summary | researcher-worker, writer-worker, user | ported (meeting-summary merges the old summarizer) |
| project-backup | user | ported |

Anthropic's document skills (docx, pdf, pptx, xlsx) and Claude Code built-ins (web search, `/code-review`, `/security-review`) replace the old `docx`, `pdf`, `pptx`, `xlsx`, `ddgr`, and `code-reviewer`.

## Platform Constraints

- Nesting depth: the default allows 3 levels below the main thread, and this design uses 2. If `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` is below 2, Mode 1 breaks. `./deploy doctor` checks for this.
- An `Agent(type, ...)` allowlist only applies to the main-thread agent. Leads are restricted by their prompts. The supervisor's ban on the built-in `general-purpose`, `Explore`, `Plan`, and `claude` agents is prompt-only too: a `tools` allowlist would drop unlisted MCP tools, and a `permissions.deny` rule in `settings.json` would also apply to plain sessions.
- `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` ignores every per-agent model, and `CLAUDE_CODE_EFFORT_LEVEL` overrides every per-agent effort. `doctor` warns about both.
- Subagents cannot ask the user questions directly. Leads return questions to the supervisor, which batches them.
