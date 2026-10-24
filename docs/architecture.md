# Architecture

## Overview

```
                         user
                          |
                    supervisor (fable)                         depth 0 (main thread)
         ________________|___________________________
        |  Mode 1: full harness (or Path: minimal)   |  Mode 2: quick tier (haiku)
        |                                            |
  researcher  planner   executor   writer            clerk   git-ops  scout  curator  depth 1
   (opus)    (fable)    (opus)     (opus)                                    (sonnet)
      |         |          |          |
      |   N parallel workers when the work splits (one wave per message)        depth 2
      |   researcher-worker (sonnet) | planner-worker (sonnet) | executor-worker (sonnet) | writer-worker (opus; fable on request)
      |
      +--> critic (opus; fable when planner calls)                              depth 2
      +--> scope-critic (fable) -- if SHOULD+ or big: rules, lists cuts         depth 2
      |
      lead decides -> fix (re-dispatch) -> review delta -> ... (cap 3 rounds)
```

## Agents

| Agent | Role | Model / effort | Tools |
|---|---|---|---|
| `supervisor` | Main thread: routing, briefing, synthesis | fable / default | all except Bash, NotebookEdit |
| `researcher` | Lead: research artifacts in `.supervisor/working/research/` | opus / default | all |
| `planner` | Lead: decision-and-outline plans in `.supervisor/working/plans/`, questions first | fable / default | all |
| `executor` | Lead: code, tests, config, agent definitions, conflicts, Python environments; implements a single unit itself and fans out two or more disjoint units; lands its change sets through a worktree and a local squash merge | opus / default | all |
| `writer` | Lead: scientific and technical prose, slide content, project docs | opus / default | all |
| `researcher-worker` | Worker: one bounded investigation | sonnet / default | all except Agent, Edit, NotebookEdit |
| `planner-worker` | Worker: one bounded repo question for a plan | sonnet / default | all except Agent, Write, Edit, NotebookEdit |
| `executor-worker` | Worker: one unit of change in its assigned files | sonnet / default | all except Agent |
| `writer-worker` | Worker: extracts sources, drafts and revises prose | opus / default (fable on request) | all except Agent |
| `critic` | Reviewer: quality and compliance, PASS/REVISE; applies the project's REVIEW.md when present | opus / default (fable when called by planner) | read-only plus Bash |
| `scope-critic` | Reviewer: KEEP/DOWNGRADE/DROP rulings and CUT list | fable / default | read-only, no Bash |
| `clerk` | Quick: small, exact edits; logs plan decisions as briefed; stages, never commits | haiku / xhigh | Read, Edit, Write, Glob, Grep, Bash |
| `curator` | Memory: closes out finished plans (distills decisions, facts, goals; archives them); remember/forget/make this a project; migrates legacy writing rules and a legacy `docs/` working set (`migrate docs/`); retires entries the delivered work encodes; audits the store on request; archives draft state; stages its writes, never commits | sonnet / default | Read, Edit, Write, Glob, Grep, Bash |
| `git-ops` | Quick: routine git with guardrails; the only Mode 2 committer (commits curator and clerk store writes, raises `VERSION` on an X.y default branch; may amend or reset a session commit when the brief names its SHA and the operation, and commits briefed paths without stopping on other changes) | haiku / xhigh | Bash, Read, Glob, Grep |
| `scout` | Quick: read-only lookups | haiku / xhigh | read-only plus Bash |

## Mode 1: The Lead Loop

All four leads preload the `lead-loop` skill (`pack/skills/lead-loop/SKILL.md`):

1. **Contract.** Goal, acceptance criteria, in/out of scope, constraints.
2. **Fan-out.** N independent units (1-6) dispatched in one message when the work splits; a single unit follows the lead's file (the executor does it itself; researcher and writer still use one worker). Units never share files. Dependent units run in waves.
3. **Integrate.** Merge reports and run cheap validation.
4. **critic.** BLOCKING/SHOULD/NIT findings with evidence, then a PASS/REVISE verdict. It applies the project's root REVIEW.md and any REVIEW.md in a directory holding a changed file or the artifact, after the brief's contract.
5. **scope-critic.** Runs when the critic's findings table has a row above NIT (a PASS can carry SHOULD rows) or the artifact exceeds a size bound (the plan's expected change size, else more than 200 changed diff lines for code or more than two pages of new prose); otherwise the lead skips it and logs the skip. Rules KEEP/DOWNGRADE/DROP on each critic finding, lists CUTs of existing bloat, and returns a LEAN/TRIM verdict.
6. **Decide.** The lead fixes kept BLOCKING findings and applies CUTs, and logs every overrule.
7. **Loop or stop.** Done or cap (3 rounds), each followed by a bounded report. Round 2 and later review only a diff of the fixes. When the critic re-raises a finding the lead already addressed or rejected, it survives; on its second survival (stalemate) the lead decides it and logs the decision.

The supervisor's brief sets the review depth: `Review: full` (default, the loop above), `light` (one critic round, then scope-critic when the rule above calls for it, iteration only on BLOCKING findings), or `none` (the lead self-validates). The planner defaults to one review round, because the user reviews the plan next.

Why two critics? A single critic improves correctness but drifts toward defensive additions: extra validation, caveats, edge cases nobody has, and "for completeness" sections. Each one sounds reasonable, so a lead that accepts every finding grows the artifact every round. `scope-critic` sees the original request and the critic's findings together. It has two duties: ruling on which findings the contract actually needs, and an independent bloat check of the artifact itself. On a clean small round (no findings above NIT, artifact under the size bound) the lead skips it. It is barred from adding requirements, so it cannot become a third source of growth.

**Work packages.** A plan may carry a `## Work Packages` section: a breakdown into packages with disjoint ownership, dependencies, and the stages each needs, which the supervisor runs as a program one wave at a time. Each package lists only the stages it needs (`research`, `plan`, `execute`, `write`) and depends only on the packages whose output it consumes:

```
### P9: deploy hook
- Goal: deploy installs the hook; done when `./deploy doctor` reports it
- Owns: `deploy`, tests/test_deploy.py
- Deps: none
- Stages: plan, execute
- Status: plan
- Artifacts: .supervisor/working/plans/plan-hooks-p9.md
```

The field rules and Status values are in `pack/skills/plan-writing/SKILL.md` (`## Work Packages`), the split rules (when to split, `Amend parent:`) in `pack/agents/planner.md` (`## Work Packages`), and the run rules in `pack/agents/supervisor.md` (`## Programs`); user view and diagrams: [README](../README.md#larger-work). After each wave, one `clerk` advances each package's `Status`, appends each lead's `Log:` line to the plan's `## Log`, and applies any `Amend parent:`: a package's planner splits it by returning new packages for the parent plan, so plans never nest. `## Log` holds one line per lead run, with what was deferred and why, so a new session can tell what ran and what is still open. One `git-ops` then commits the wave's store changes. A question blocks its package, which is skipped until the user answers; the answer re-runs that stage, also in a new session, because the plan file holds the state. When every package is `done` (or a flat plan's `## Todo` is complete), `curator` closes the plan out: it distills decisions, facts, and goals into memory, then moves the plan, its child plans, and its research with `git mv` into `.supervisor/archive/working/`.

## Mode 2: The Quick Tier

The supervisor dispatches one Haiku specialist directly, with no review loop. The Sonnet `curator` is the other direct dispatch: close-out, "remember X" / "forget X" / "make this a project", and recording a single-stage decision. Specialists reply with `ESCALATE:` when the task turns out to be larger, ambiguous, or risky. The supervisor then re-routes the task to Mode 1, passing along the specialist's findings.

## Routing

The supervisor picks the mode. An explicit user choice ("quick", "full") wins. Otherwise Mode 2 applies only when the task is fully specified, small, local, needs no design decision, and is cheap to undo. Larger work chains through the leads: `researcher` -> `planner` (questions, then the plan) -> user approval -> `executor`, skipping stages that add nothing. Mechanical multi-file work gets `Review: light`. A request that fails the Mode 2 test only on "cheap to undo" or "needs no design decision", with a specified, local outcome (one subsystem, a few files), gets `Path: minimal`: one lead that does the single unit itself, one critic round, scope-critic only on findings above NIT or a large artifact, implying `Review: light`; the lead fans out if it finds several disjoint units. The default for Mode 1 stays the full shape. When the session is confined to a worktree (the environment forbids the parent checkout), the supervisor confirms the push with the user, then briefs `executor` and `git-ops` with `Confined to worktree: <path>; push to <default> authorized`.

Git conflicts: `git-ops` never resolves them. It returns a structured `ESCALATE` (operation, both sides, conflicted files with hunk counts and mechanical flags). The supervisor sends easy conflicts to `executor` with `Review: light`, and hard ones through `researcher` -> `planner` -> user approval -> `executor`.

## Git Work

In a git project, each `executor` change set works in its own worktree at `<toplevel>/.claude/worktrees/<slug>` on a new branch; its workers share the lead's worktree, and only the lead changes git state in it. The branch is cut from the default branch and named like the repo's existing branches, else `<type>/<slug>`. If the worktree path is not already ignored, `/.claude/worktrees/` is appended to `.git/info/exclude`; `.gitignore` is never edited for this. Small ignored files such as `.env` are copied into the worktree; virtual environments and `node_modules` are built per worktree, never linked. The lead lands the branch locally with a squash merge into the checkout holding the default branch, and never pushes. The exception is a session confined to its worktree (no checkout has the default branch, or the harness forbids the parent): the lead lands from the worktree itself and fast-forward pushes `HEAD:<default>` only when the brief authorizes it, otherwise stops before the push and reports the squash SHA (`pack/skills/repo-workflow/references/landing-from-worktree.md`). Landing rebases the branch on the default branch and squash-merges it as one commit, then removes the worktree and the branch; if the default checkout is busy or missing, the branch is left ready and reported. Pending `.supervisor/` changes ride along with commits.

Quick-tier work, conflict resolution, environment repair and repos with submodules stay in the current checkout, as does work the user asks for "in place" or in a named checkout or worktree, which then merges only on request. Other worktrees are reported and cleaned up only on request, never forced, with unmerged branches kept.

No version is created or bumped unless the repo opts in (`X.y` scheme, asked until `CLAUDE.md` records an answer). A project with no versioning and no `CLAUDE.md` line is asked whether to adopt the `repo-workflow` `X.y` scheme: yes adds "Versioning: uses the repo-workflow X.y scheme." to `CLAUDE.md` and creates `VERSION` at `1.0`; no adds "Versioning: none; do not ask." Under `X.y`, y rises once per change set that lands on the default branch and X on a major change; a repo with its own scheme keeps it. A `CLAUDE.md` line can grant `--force-with-lease` on feature branches after a rebase; it never covers the default branch, which is force-pushed only when the user names it. The repo's `CLAUDE.md` (plain prose, no config file) and the brief override the `repo-workflow` defaults. Outside a project nothing is persisted. Rules: `pack/skills/repo-workflow/SKILL.md`; user view: [README](../README.md#branches-worktrees-and-versions).

## Models And Cost

The full assignment is in the [Agents](#agents) table. Fable runs where judgment has the most leverage: the supervisor's routing, the planner's plans, and scope-critic's resistance to reasonable-sounding additions. Every agent runs at default effort except the Haiku quick tier, which runs at xhigh. Planner overrides the critic to Fable for plan reviews, and writer overrides writer-worker to Fable when the user asks for the strongest drafter ("best possible"), which changes anything only where Fable is not remapped to Opus: `ANTHROPIC_DEFAULT_FABLE_MODEL` unset and the session not started with `--fable-is-opus`. writer-worker runs on Opus because voice matching and AI-tell avoidance need the stronger model, and it usually runs as a single drafter and fans out only for source extraction. The other workers run on Sonnet and the quick tier on Haiku. Deployed agents keep `model: fable`; Fable runs as Fable unless `ANTHROPIC_DEFAULT_FABLE_MODEL` maps it to Opus, in the environment or via the launcher's `--fable-is-opus` (see `docs/deploy.md`).

A Mode 1 round costs N worker calls plus the critic, scope-critic (when it runs) and the lead's own turns; a clean small round skips scope-critic. A `Path: minimal` run costs the lead plus one critic call, and scope-critic only if the critic found something above NIT or the change is large. Mode 2 costs one Haiku call, and a plan close-out one Sonnet call. Routing small work to Mode 2 is the main cost control; `Review: light` drops the extra rounds for mechanical Mode 1 work.

## Memory

Three horizons: long-term `goal` entries, a mid-term roadmap (`.supervisor/roadmap.md`), and short-term plans. The store `.supervisor/` holds `memory/<kind>/` (entries in force), `working/` (research, plans, per-document writer state), `archive/`, and `history.md` (one line per landed item). Folders carry fixed properties (an entry's kind), labels carry changing ones, and the archive mirrors the live tree. The `clerk` logs plan decisions, the `curator` curates, and `writer` owns `working/writing/`. Leads read matching entries at contract time, `scout` reads for the supervisor, and workers never read. Entries are claims to validate before use; a change supersedes the old entry and moves it to `archive/`. Only the `curator` creates the store. `curator` and `clerk` never commit: they stage their writes, and the supervisor then dispatches `git-ops` to commit them (`chore(memory): <what>`). Off the default branch, a lead or `writer` that writes store files commits them itself (no `VERSION` change); on the default branch they ride with the next commit in that checkout. A worktree's store is its branch's memory, landed with the branch. The curator writes at most five new entries per run, except when migrating a legacy layout or auditing the store on request. Outside a project (a git repo, or a directory with `.supervisor/`, `.claude/`, `CLAUDE.md` or `AGENTS.md` here or above, never counting `$HOME` or its ancestors; a git toplevel outranks anything above it) nothing is stored until the user opts in ("remember X", "make this a project", or a close-out).

## Skills

| Skill | Used by | Origin |
|---|---|---|
| lead-loop | all leads (preloaded) | new |
| plan-writing | planner (preloaded), critic | new |
| project-memory | clerk, curator, writer, writer-worker (preloaded); leads via lead-loop; critic on demand | new |
| git-safety | executor, git-ops (preloaded); executor reads `references/conflict-resolution.md` on unmerged paths | old git-expert + conflict-resolver |
| repo-workflow | executor, planner, git-ops (preloaded); referenced by project-memory and curator | new |
| python-env | executor, executor-worker (loaded on demand) | old python-maintainer |
| agent-authoring | executor, executor-worker, critic | old agent-builder/agent-critic + AGENTS.md |
| science-writing-style, presentation-style | writer (picks), writer-worker, critic | ported |
| document-extraction, email-extraction, meeting-summary | researcher-worker, writer-worker, writer (names in briefs), user | ported (meeting-summary merges the old summarizer) |
| project-backup | user | ported |

Anthropic's document skills (docx, pdf, pptx, xlsx) and Claude Code built-ins (web search, `/code-review`, `/security-review`) replace the old `docx`, `pdf`, `pptx`, `xlsx`, `ddgr`, and `code-reviewer`.

## Platform Constraints

- Nesting depth: the default allows 3 levels below the main thread, and this design uses 2. If `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` is below 2, Mode 1 breaks. `./deploy doctor` checks for this.
- An `Agent(type, ...)` allowlist only applies to the main-thread agent. Leads are restricted by their prompts. The supervisor's ban on the built-in `general-purpose`, `Explore`, `Plan`, and `claude` agents is prompt-only too: a `tools` allowlist would drop unlisted MCP tools, and a `permissions.deny` rule in `settings.json` would also apply to plain sessions.
- `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` ignores every per-agent model, and `CLAUDE_CODE_EFFORT_LEVEL` overrides every per-agent effort. `doctor` warns about both.
- Subagents cannot ask the user questions directly. Leads return questions to the supervisor, which batches them.
