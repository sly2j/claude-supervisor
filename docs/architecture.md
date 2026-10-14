# Architecture

## Overview

```
                         user
                          |
                    supervisor (fable)                         depth 0 (main thread)
         ________________|___________________________
        |  Mode 1: full harness                      |  Mode 2: quick tier (haiku)
        |                                            |
  researcher  planner   executor   writer            quick-edit  git-ops  scout   depth 1
   (opus)    (fable)    (opus)     (opus)
      |         |          |          |
      |   N parallel workers (one wave per message)                              depth 2
      |   researcher-worker (sonnet) | executor-worker (sonnet) | writer-worker (opus)
      |
      +--> critic (opus, xhigh; fable when planner calls)                       depth 2
      +--> scope-critic (fable) -- rules on the critic's findings, lists cuts    depth 2
      |
      lead decides -> fix (re-dispatch) -> review delta -> ... (cap 3 rounds)
```

## Mode 1: The Lead Loop

All four leads preload the `lead-loop` skill (`pack/skills/lead-loop/SKILL.md`):

1. **Contract.** Goal, acceptance criteria, in/out of scope, constraints.
2. **Fan-out.** N independent units (1-6) dispatched in one message. Units never share files. Dependent units run in waves.
3. **Integrate.** Merge reports and run cheap validation.
4. **critic.** BLOCKING/SHOULD/NIT findings with evidence, then a PASS/REVISE verdict.
5. **scope-critic.** Rules KEEP/DOWNGRADE/DROP on each critic finding, lists CUTs of existing bloat, and returns a LEAN/TRIM verdict.
6. **Decide.** The lead fixes kept BLOCKING findings and applies CUTs, and logs every overrule.
7. **Loop or stop.** Done, cap (3 rounds), or stalemate (the same finding twice), each followed by a bounded report.

Why two critics? A single critic improves correctness but drifts toward defensive additions: extra validation, caveats, edge cases nobody has, and "for completeness" sections. Each one sounds reasonable, so a lead that accepts every finding grows the artifact every round. `scope-critic` sees the original request and the critic's findings together, and its only job is to say which findings the contract actually needs. It is barred from adding requirements, so it cannot become a third source of growth.

## Mode 2: The Quick Tier

The supervisor dispatches one Haiku specialist directly, with no review loop. Specialists reply with `ESCALATE:` when the task turns out to be larger, ambiguous, or risky. The supervisor then re-routes the task to Mode 1, passing along the specialist's findings.

## Routing

The supervisor picks the mode. An explicit user choice ("quick", "full") wins. Otherwise Mode 2 applies only when the task is fully specified, small, local, needs no design decision, and is cheap to undo. Larger work chains through the leads: `researcher` -> `planner` -> user approval -> `executor`, skipping stages that add nothing.

## Models And Cost

The full assignment is in the README agent table. Fable runs where judgment has the most leverage: the supervisor's routing, the planner's plans, and scope-critic's resistance to reasonable-sounding additions. The critic runs on Opus at xhigh effort, and planner overrides it to Fable for plan reviews. writer-worker runs on Opus because voice matching and AI-tell avoidance need the stronger model, and it usually runs as a single worker. The fan-out workers run on Sonnet and the quick tier on Haiku.

A Mode 1 round costs N worker calls plus three more (critic, scope-critic, and the lead's own turns). Mode 2 costs one Haiku call. Routing small work to Mode 2 is the main cost control.

## Skills

| Skill | Used by | Origin |
|---|---|---|
| lead-loop | all leads (preloaded) | new |
| git-safety | executor, git-ops (preloaded) | old git-expert + conflict-resolver |
| python-env | executor, executor-worker | old python-maintainer |
| agent-authoring | executor, executor-worker, critic | old agent-builder/agent-critic + AGENTS.md |
| writing-rules-persistence | writer, writer-worker (preloaded), critic | ported |
| science-writing-style, presentation-style | writer-worker, critic | ported |
| document-extraction, email-extraction, meeting-summary | researcher-worker, user | ported (meeting-summary merges the old summarizer) |
| project-backup | user | ported |

Anthropic's document skills (docx, pdf, pptx, xlsx) and Claude Code built-ins (web search, `/code-review`, `/security-review`) replace the old `docx`, `pdf`, `pptx`, `xlsx`, `ddgr`, and `code-reviewer`.

## Platform Constraints

- Nesting depth: the default allows 3 levels below the main thread, and this design uses 2. If `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` is below 2, Mode 1 breaks. `scripts/deploy doctor` checks for this.
- An `Agent(type, ...)` allowlist only applies to the main-thread agent. Leads are restricted by their prompts.
- `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` ignores every per-agent model, and `CLAUDE_CODE_EFFORT_LEVEL` overrides every per-agent effort. `doctor` warns about both.
- Subagents cannot ask the user questions directly. Leads return questions to the supervisor, which batches them.
