# Research: folding subagents into the main loop (Anthropic article vs Supervisor for Claude)

Date: 2026-10-24. Pack version at time of writing: 5.1 (branch `worktree-fold-subagents-review`).

## Scope

- Digest the Anthropic article "Building agents: When to fold subagents into your main agent loop"
  (Diane Sarkis, 2026-10-22,
  https://claude.com/resources/articles/building-agents-when-to-fold-subagents-into-your-main-agent-loop).
- Map each of its recommendations against the pack as it is in this repo.
- Audit past session transcripts for where the design spends effort.
- Rank what to adopt and what to reject.

Out of scope: edits to `pack/`, README or docs, and any plan. Abbreviations used below:
- SUP = `pack/agents/supervisor.md`
- LL = `pack/skills/lead-loop/SKILL.md`
- AA = `pack/skills/agent-authoring/SKILL.md`
- ARCH = `docs/architecture.md`

## 1. Article digest

Provenance caveat:
- The page was read through two WebFetch calls. WebFetch summarizes with a small model, so no raw text was obtained, and every paraphrase below is unconfirmed as verbatim.
- Per the fetch, the article gives no quantitative threshold for "context bloat".

| ID | Recommendation (paraphrase) | Article's reasoning |
|---|---|---|
| A1 | Default to one main loop with skills and tools loaded progressively. | The authors saw a single agent with skills often beat both one-prompt and subagent designs on quality, cost and latency. Subagents remain valid for verification, parallel work and permissioning. |
| A2 | Keep a subagent only when: (a) a single loop shows measurable context-bloat degradation; (b) the work is parallel and needs fresh, discardable context; (c) the agent struggles with tool selection or has conflicting instructions. | These are the three conditions under which separation pays for itself. |
| A3 | Anti-pattern: one subagent per team or problem type. | The architecture copies the org chart (Conway's law), giving inconsistent output and added latency. |
| A4 | Anti-pattern: classifier, pipeline and orchestrator stacks. | One clear prompt, 4-5 thin data tools and output guardrails usually suffice. |
| A5 | Failure modes: lossy handoffs, subagent sprawl, "Frankenprompt", localized evals, latency. | One customer saw about 2x faster runtime with a single loop. |
| A6 | Prefer shared context. | One loop that saw every step can connect them, with fewer lossy handoffs. |
| A7 | Prevent bloat by progressive disclosure, not by splitting. | Claude Code's system prompt was cut by over 80% for advanced models. |
| A8 | Newer models (Opus 4.5 and later) manage far more in one loop. | Some harness parts become redundant, and rigid multi-agent structure can block new models. |
| A9 | A single loop needs disciplined prompt, description and memory management. | Not given beyond the statement itself. |
| A10 | A small central team owns the prompt and end-to-end quality. | Domain teams own skills and tools instead of agents. |
| A11 | If multi-agent, use the simplest pattern and split by context, not problem type. | Subagents should return compact results. Problem-type splits create a "telephone game". |
| A12 | Target design: one open-ended tool loop with budgets and write gates, parallel tool batches, a self-written plan and an optional verifier. | The planner and the executor are the same loop. |
| A13 | Move procedure to skills, hard limits and lookups to tools, and keep code only for cheap preloading. | Not given beyond the statement itself. |
| A14 | Build an end-to-end eval first: 10 golden examples suffice. Add per-skill evals. Track routing accuracy. | Nothing can be folded safely without a baseline. |
| A15 | Reduce subagents over time, the highest-use ones first. | Not given beyond the statement itself. |
| A16 | Merge specialists that chain, share data or are called together. | Heavy specialist-then-specialist traffic means merge. |
| A17 | Intermediate step: call subagents as tools. Use a full handoff only when the subagent must talk to the user. | The main loop keeps the conversation. |
| A18 | Fold one subagent at a time. Compare evals, inspect which tasks flipped, and run each task more than once. | The article's example is a regression that showed in one run out of two. |
| A19 | Decision rule: keep a subagent only if the folded version scores worse. Measure and change one thing at a time. | Not given beyond the statement itself. |
| A20 | Group tools by intent. | Tool choice degrades past 30-50 definitions. Use tool search, and put preconditions and permissions in tools. |
| A21 | Skills hold team procedures. | Owners, evals and `/skill-doctor` prevent sprawl. |
| A22 | Put knowledge behind lookup tools or skill reference files. | Avoid code that pastes context into prompts. |
| A23 | Named tooling: `/claude-api` build-eval, prompt-audit, hillclimb, cost-optimize, and a migration kit. | Not given beyond the statement itself. |

## 2. Mapping against the pack

### Framing (inference)

The article targets customer-facing product agents built on the API, with many teams each owning a subagent. This pack serves one user in Claude Code, where Claude Code is already the single loop and skills are already disclosed progressively. That weakens or removes:
- A3, because there is no org chart to copy;
- A5's org-level failure modes;
- A10;
- A20-A23, because the pack defines no MCP tools.

The eval items (A14, A18, A19) transfer fully. The pack makes cost, latency and quality trade-offs it has never measured.

### Item table (verified facts unless marked)

| # | Status | Evidence | What a change would look like |
|---|---|---|---|
| A1 | Violated by design | Mode 1 is one lead plus workers, critic and scope-critic (SUP:14-15). Fan-out is the default (LL:32-35). | Record why multi-agent is kept, or test a single-lead variant on small Mode 1 jobs against an eval. |
| A2 | Partial | Condition (b) is the de facto rationale: parallel units (LL:32-33) and worker reports capped in the worker agent files. Condition (a) is asserted, not measured: "Repository context is expensive" (SUP:98). (c) is not cited. | Name A2's three conditions in AA as the test for adding an agent or spawning a worker. |
| A3 | Partial | The four leads split by artifact type (SUP:17-22). Workers split by bounded unit of context. Handoffs go through files (research and plan artifacts). | Keep for now. Leads differ in model, tools and preloaded skill, so they are context splits as well as type splits. |
| A4 | Partial | Routing is a prose rule, not a classifier (SUP:34-39). The researcher -> planner -> executor chain plus review is a pipeline, softened by "skip stages that add nothing". | No change. Mode 2 and direct answers are the short path. |
| A5 | Partial | Handoff loss is limited by the verbatim contract to critics (LL:24-25), files as state, and `diff -u` deltas (LL:61-68). Sprawl is controlled: 15 agents, one owner, lint tests. No latency figure exists. | Measure latency and handoff loss. This needs A14. |
| A6 | Violated by design | The supervisor does not see source (SUP:98-100). Leads see worker reports only. Workers never search memory (LL:20-22). | Accept the trade-off. The log audit (section 3) shows it buys a small main-thread context. |
| A7 | Satisfied | Skills load on demand. Agent bodies are word-capped by lint (`tests/test_pack_lint.py`). | None. |
| A8 | Partial | No audit for rules written around weaker models. LL:34-35 explicitly overrides the Agent tool's spawn-sparingly guidance. | Run a prompt-audit pass over LL and SUP for rules that may now cost more than they save. |
| A9 | Satisfied | Short supervisor prompt. Plans, memory and research artifacts carry state (SUP:72-94). | None. |
| A10 | Not applicable | One owner. | None. |
| A11 | Mostly satisfied | Worker reports are capped at 400-600 words. Lead reports are bounded (LL:112-127). Nesting stops at depth 2 (AA:25-26). The pattern is not the simplest one. | Name the smallest Mode 1 path (one lead, N=0 or 1, `Review: light`) as an explicit middle tier. |
| A12 | Partial | Round cap of 3 (LL:93-94). Parallel batches. The verifier is optional only on user request: `none` "only when the user asks" (SUP:48-49). Planner and executor are separate, with approval between. | Make the second reviewer conditional (see R2) rather than make the critic optional. |
| A13 | Satisfied | Procedures are skills (lead-loop, plan-writing, git-safety, repo-workflow). Limits are frontmatter tool restrictions. The "own workers only" rule is prompt-only (ARCH:106). | None. |
| A14 | Violated | `tests/` holds only test_deploy.py, test_pack_lint.py and test_version.py. All are static. No graded agent runs, and no "eval" or "golden" anywhere in tests, pack or docs. | About 10 golden tasks spanning small edit, research, plan, prose and conflict, graded on the final artifact and rerun after each architecture change. |
| A15 | Not addressed | The trend has been to add agents (curator, scout, git-ops). There is no fold history, and no decision entry covers folding or fan-out cost. | Revisit after A14 exists. |
| A16 | Partial | Built-in chains: critic then scope-critic every round (LL:51-59); ESCALATE -> Mode 1 redo (SUP:40-41); git-ops conflict -> executor. | See R2. Log data says the ESCALATE chain is rare (section 3). |
| A17 | Satisfied | The supervisor alone talks to the user. Subagents return bounded reports. | None. |
| A18 | Violated | No fold has been done or compared. Blocked on A14. | Once an eval exists, fold one thing (e.g. scope-critic into critic) and compare per-task flips. |
| A19 | Violated | As A18. | Adopt as the rule for future structural changes once an eval exists. |
| A20 | Not applicable | The pack defines no MCP tools. | None. |
| A21 | Satisfied | Skills preferred over agents (AA:51-52). No per-skill evals exist. | Covered by A14. |
| A22 | Satisfied | The project-memory store is retrieved by leads and passed in briefs (LL:17-22). | None. |
| A23 | Not applicable | The pack uses none of the named tooling. prompt-audit and build-eval are candidate means for A8 and A14. | Optional. |

### The five focus areas

1. **Mode 1 / Mode 2 routing.** Sound.
   - Mode 2 requires all four conditions (SUP:36-37).
   - ARCH:80 calls Mode 2 "the main cost control".
   - Gap: anything not clearly small gets the heavy path. The pack has no named middle tier, although `Review: light` plus N=0 or 1 already approximates the article's single loop (inference).
2. **Lead -> worker fan-out.** In tension with A1 and A6, but defensible under A2(b).
   - The trigger is structural ("two or more independent units", LL:32-33), not need-based.
   - There is no "when not to spawn" rule beyond N=1 and the glue allowance (LL:42-43).
   - Counterweights exist: writer uses a single drafter, researcher uses one worker for an obvious location, and planner drafts its own plan.
3. **critic + scope-critic.** The most reasoned extra in the pack: ARCH:58 explains the drift that scope-critic counters.
   - It is an always-chained pair (A16).
   - The ARCH:58 drift claim is untested (inference).
   - The log data in section 3 makes this the strongest candidate for a conditional change.
4. **Supervisor "do not read files yourself".** Matches A2(a) and A7 in intent and gives up A6.
   - The stated reason is one phrase (SUP:98).
   - Exceptions: one or two small reads (SUP:38-39), conflicting reports, a surviving ambiguity, or a user request (SUP:100).
   - The log data supports it (section 3).
5. **Haiku quick tier with ESCALATE.** Split by cost and risk tier with a bounded context, which fits A11.
   - Each ESCALATE is a wasted call plus a redo (A16).
   - The log data shows ESCALATE is rare, so the tier is cheap (section 3).

### Relevant memory

- `.supervisor/memory/decisions/2026-10-22-supervisor-runs-packages-in-waves.md` rejected a coordinator agent in favour of the plan file as the only state. That is consistent with A1/A15 and with files as state against A5.
- None of the 19 decision entries concerns evals, folding or fan-out cost.

## 3. Session-log efficiency audit

### Method

- Corpus: 27 sessions dated 2026-10-14 to 2026-10-24.
  - 19 came from `~/.config/claude-supervisor/projects/`.
  - 8 came from `~/.claude/projects/` and dispatched pack agents.
  - They span 9 project directories (count only). This session is excluded.
- Subagents: 816 subagent transcripts across 21 sessions. Each was matched to its parent through `meta.toolUseId` against every Agent tool_use id, and the result agrees with `spawnDepth`. All subagents ran in the background, and their results are `SubagentHandback` calls.
- Tokens: deduplicated by message id. "Non-cache" means input + output + cache_creation. About 85% of all volume is cache_read.
- Only structure was measured. Scripts are outside the repo, in the session scratchpad (`logaudit/audit.py`, `followup.py`).
- `quick-edit` (37 dispatches) is the pre-v2.0 name of `clerk` (commit b3db943). The sessions span pack versions.

### Verified measurements

**Dispatch and nesting**
- Depth is exactly 2, never deeper: 256 depth-1 and 560 depth-2 transcripts.
- No dispatch used `general-purpose`, `Explore`, `claude`, or an omitted `subagent_type`.
- Planner leads dispatched researcher-worker 11 times. All 11 predate commit ae6d00f, which introduced planner-worker; before it, planner.md named researcher-worker. This was compliant at the time.

**Main-thread dispatches**
- Mode 1 leads: 89 (executor 51, planner 17, researcher 12, writer 9).
- Mode 2: clerk/quick-edit 60, git-ops 64, scout 25, curator 15.

**Token share**

| | Total tokens | Non-cache tokens |
|---|---|---|
| Subagents | 645M (85%) | 57.6M (92%) |
| Main thread | 113M | 5.3M |

- By model, subagents only, total and non-cache tokens: Opus 429M and 27M, Sonnet 144M and 18M, Fable 48M and 8.5M, Haiku 25M and 4.3M (Haiku includes the built-in claude-code-guide).
- By tier, largest non-cache consumers: critic 10.7M, executor-worker 8.3M, executor lead 7.8M, researcher-worker 5.9M, planner lead 5.7M, main thread 5.3M, scope-critic 5.1M, all quick-tier agents together 4.3M.
- Main-thread context grew a median 1.7x over a session (one example: 42k to 289k), with a median final size of 66k tokens.
- The largest main-thread context, 352k, came from the one long session that used no subagents. The largest with subagents was 289k, in a session with 96 subagents.

**Supervisor no-read rule**
- The main thread used Read 12 times across 27 sessions, in 5 sessions, and never used Grep or Glob.
- Bash use by the main thread was 42 calls, 30 of them read-like. Inference: these came from main threads not running as the supervisor (the secondary-store sessions), since the supervisor has no Bash.

**Lead tree cost (total tokens, lead plus its workers and reviewers)**

| Lead | Tree total | Lead's own share |
|---|---|---|
| executor | 339M | 205M (60%; on non-cache tokens the lead used 7.8M and its workers 8.3M) |
| researcher | 146M | 45.5M |
| planner | 94M | 53M |
| writer | 40M | 19M |

- The executor lead's own Bash calls total 1206: 218 test runs, 346 git commands and 642 other.

**Fan-out**
- Mean workers per run: researcher 5.1, planner 4.6, executor 3.1, writer 2.9. The largest single wave was 7.
- 9 runs had zero workers (executor 7, planner 2).
- 8 runs had one worker (writer 5, which is by design; executor 2; planner 1).

**Duplicate reads**
- 38 files were read by two or more workers of the same lead run, giving 85 excess reads.
- 25 of 89 runs were affected, and executor runs account for 30 of the 38 files.

**Critic loop**
- 138 critic and 97 scope-critic dispatches.
- Rounds per run (0/1/2/3): 3/45/33/8.
- Round-1 critic verdict was PASS in 62 of 88 handbacks (70%). For executor it was 44 of 52 (85%), against researcher 4 of 12 and planner 7 of 15.
- Rounds 2 and later returned PASS in 45 of 49. All 41 runs that reached round 2 ended on PASS.
- 47 of 56 BLOCKING tokens appear in round 1.
- 95 of 135 critic rounds were followed by no Edit/Write before the next round or the end of the lead run (executor 71 of 77). This undercounts fixes, because agents often write through Bash.
- Scope-critic ruling tokens: KEEP 443, DOWNGRADE 62, DROP 97, CUT 5. 19 of 96 handbacks downgraded or dropped nothing.
- Briefs carried `Review: full` 52 times and `light` 36 times. `none` never appears.

**Quick tier**
- ESCALATE appears in 5 of 165 quick-tier handbacks (about 3%): clerk 1, git-ops 4.
- The Haiku agents (clerk/quick-edit, git-ops, scout) used about 24M total tokens. Curator runs on Sonnet and used under 1M. Scout median runtime is 52 s; git-ops 32 s.

**Executor change size (noisy)**
- 36 of 51 executor runs show zero Edit/Write by workers.
- Agents often write through Bash, and many runs are verification or git work, so "small change" could not be measured reliably.
- The flag "at most 1 file and 30 lines via Edit/Write" covers 42 runs and is only a lower bound on edit activity.

### Anonymized examples

1. One executor run dispatched 11 workers over 99 minutes for 29M tokens, with one visible worker Edit of about one line. Most work went through Bash.
2. The largest executor tree used 49.7M tokens for 5 workers and 2 critic rounds, almost all cache_read on long lead context.
3. One executor reached the 3-round cap with all 9 edits made by the lead itself and none by workers.

### Inferences from the audit (not verified)

- **The executor lead carries much of the work.** It holds 60% of executor tree tokens in total volume, mostly cache reads of its long context. On non-cache tokens the split with its workers is roughly even, and its test and git work is assigned to it by design. Executor workers add duplicate reads, which suggests many executor units are not independent enough to justify separate contexts. This matches A6.
- **The executor review loop mostly confirms.** An 85% round-1 PASS rate means most executor review runs pay for a critic plus a scope-critic that changes little. The high scope-critic DROP count on executor (57) suggests scope-critic earns its keep mainly when the critic does find something.
- **The supervisor no-read rule works as intended.** The main thread stays small relative to the work it coordinates.
- **The quick tier is cheap and rarely escalates.** The A16 worry about ESCALATE redo traffic does not show in the data.
- **Research and planning gain more from review.** They show higher round-1 REVISE rates (58% and 53%), so review buys more there than in execution.

## 4. Conclusions

### Evidence summary

- **Effort concentrates in Mode 1 executor runs.** They account for 339M of 619M lead-tree tokens and are mostly lead-context cache reads.
- **Review findings concentrate in round 1 and in research and planning work.**
- **The supervisor's context stays bounded.** The Haiku tier is cheap with about 3% escalation.
- **No end-to-end eval exists**, so A18 and A19 cannot be applied yet.

### Recommendations, ranked

1. **R1 Adopt A14: build a small end-to-end eval.**
   - Write about 10 golden tasks across modes (Mode 2 edit, Mode 1 small edit, research, plan, prose) and grade the final artifacts.
   - Record tokens and wall-clock from the transcripts, reusing this audit's scripts.
   - Everything below that changes structure should be judged against it (A18/A19).
   - Highest value: it turns every other item from argument into measurement.
2. **R2 Adapt A16 and A12: make scope-critic conditional on the critic finding something.**
   - Skip scope-critic when the critic returns PASS with no BLOCKING or SHOULD findings.
   - Support: 70% round-1 PASS overall and 85% for executor. A PASS means only that there are no BLOCKING findings, so the rate for R2's exact condition (no BLOCKING and no SHOULD) is unmeasured. Scope-critic's job, per ARCH:58, is to rule on findings, so with none it has nothing to rule on.
   - This is a small LL step-4 and step-5 change.
   - Risk: see section 5.
3. **R3 Adapt A2 and A6 for executor fan-out.**
   - Let the executor lead do a single unit of a few lines itself (N=0) instead of dispatching a worker. Dispatch workers only when units are independent and large enough to need fresh context.
   - Support: 30 of 38 duplicate-read files are in executor runs, and 7 runs already went N=0. The lead already holds most of the long-context volume, though the non-cache split with workers is even, so the token saving is unproven.
   - A rule change in LL Fan-Out ("Fan-out is the default" -> conditioned on A2(b)), possibly executor-only.
4. **R4 Adopt A11 and A1: name the smallest Mode 1 path.**
   - One lead, N=0 or 1, `Review: light`, chosen by the supervisor for well-specified one-file Mode 1 work that fails the Mode 2 test only on "cheap to undo" or "no design decision".
   - Mostly a SUP routing sentence. It overlaps R3.
5. **R5 Adopt A8 cheaply: a one-time prompt-audit pass over LL and SUP.**
   - Look for rules that override model defaults, such as LL:34-35's override of spawn-sparingly. Recheck after model changes.

### Consciously reject (record the reasons)

- **A1 and A12 as a whole (fold everything into one loop).** Delegation keeps the supervisor at a median 66k tokens of context. Inference from one uncontrolled session with an unknown task: the corpus's one long no-subagent session reached 352k, though a delegating session also reached 289k. R1 is what can measure this. The pack's users run long multi-stage programs (SUP:72-94) where a bounded coordinator context matters. A2(a) and (b) are the conditions that hold here.
- **Folding the Haiku quick tier into the supervisor.** About 3% ESCALATE, about 24M tokens in total, and the supervisor deliberately has no Bash. The tier is the cheap path the article would otherwise want the main loop to be.
- **Dropping the supervisor no-read rule (A6).** The data shows it keeps the coordinator small, at the cost of extra scout calls. Keep the one-or-two-small-reads allowance as the relief valve.
- **A3, A10 and A20-A23 as written.** They target multi-team product agents with MCP tool catalogs. Nothing in this pack corresponds.
- **Merging the four leads into one lead with skills (A3 or A15).** The leads differ in model, tools and preloaded skills (ARCH:78), and they hand off through files. Revisit only after R1 can measure it.

## 5. Risks, open questions, coverage gaps

- **Article text not verbatim.** The digest rests on WebFetch paraphrase. Confirm the exact wording before citing the article in a decision entry.
- **Small, mixed corpus.** 27 sessions over 10 days, across several pack versions (pre- and post-v2.0) and 9 projects. Rates are indicative, not stable.
- **Change size not measurable.** Bash writes could not be separated from scratch writes. The question of "Mode 1 used for a one-file change" stays open.
- **Verdicts by token match.** PASS/REVISE and KEEP/DROP were counted from the text of handbacks, so legend or rubric lines could inflate them.
- **Wall-clock is inflated.** It includes idle time and waiting on background workers. No latency comparison between modes was possible.
- **Unexamined runs.** Why 9 lead runs dispatched zero workers was not examined.
- **R2 depends on an untested claim.** It rests on scope-critic adding little after a clean PASS. The audit did not measure how much scope-critic CUT from the artifact itself in those runs.
- **Open question for the owner:** should the rejections above be recorded as decision entries, so a later reader knows why the article's single-loop default was not adopted?
