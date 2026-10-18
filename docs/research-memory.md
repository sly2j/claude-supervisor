# Research: Persistence And Long-Term Memory (ROADMAP Item 1)

Scope: evidence and a recommendation for expanding ROADMAP item 1 ("Persistence for long programs
(v2.0)") into a staged plan for persistence and long-term memory in the pack. Covers current
practice, fit to the pack, a scribe/librarian agent, storage location, lifecycle, the lightweight
path, and the baseline in `pack/` today. Out of scope: the science-artefacts feature (mentioned
only where it constrains memory), and implementation. Gathered 2026-10-17 on macOS with Claude
Code 2.1.302, pack v1.21. Labels: **[V]** verified (official docs, primary paper, repo path:line,
or local experiment), **[I]** inference, **[C]** community or secondary source. Web pages were
read through WebFetch, which summarizes, so re-check numbers against the primary page before
quoting them elsewhere.

## Summary

- The working core that most systems share is small. It has three parts: (1) a small set of
  curated entries, cheap to load; (2) on-demand detail retrieved with plain file tools; (3)
  contradictions handled by supersession, not silent edits. Vector and graph stores do not fit a
  service-free pack. The evidence also says they are not needed: Letta's filesystem agent beat
  Mem0's reported best on LoCoMo (section 1.7).
- Stale memory is a measured harm, not a hypothetical one: error propagation (arXiv 2505.16067),
  the knowledge-update failures in LongMemEval, and poisoning (MINJA). The best-documented
  mitigation is GitHub Copilot's: every memory cites code locations, and the cited code is
  checked against the current branch before use.
- The pack has no memory today. Persistence means plans and research in `docs/` plus
  `docs/writing-rules.md`. The supervisor's "memory files" clause points at nothing the pack
  defines, and user decisions made mid-program are lost (section 3).
- Recommendation: a **hybrid** of three stores, sorted by lifetime and kept in the project repo:
  a working set (short-term), a long-term store of one file per entry, and an archive. A new
  `scribe` agent owns close-out: distilling, superseding and archiving. The existing post-wave
  `quick-edit` records mid-program decisions. Leads retrieve memory with one
  grep. Claude Code's own auto memory stays for personal preferences. The work lands in **five
  stages**, and the first two deliver the current ROADMAP candidates without the scribe (sections
  8-9).

## 1. Current Practice (Q1)

### 1.1 Claude Code Native Features

- **CLAUDE.md hierarchy** [V] https://code.claude.com/docs/en/memory:
  - Four scopes: managed, user (`~/.claude/CLAUDE.md`), project (`./CLAUDE.md` or
    `./.claude/CLAUDE.md`), and local (`./CLAUDE.local.md`, gitignored, not deprecated).
  - At launch, ancestor files load root to cwd. Subdirectory files load on demand when Claude
    touches a file there.
  - `@path` imports expand at launch (max four hops) and "don't reduce context cost".
  - `.claude/rules/*.md` either load unconditionally or, with `paths:` globs, when a matching
    file is read.
  - Size guidance: "target under 200 lines per CLAUDE.md". The project root CLAUDE.md is re-read
    after compaction (https://code.claude.com/docs/en/context-window).
  - Subagents get the full hierarchy unless `omitClaudeMd` is set
    (https://code.claude.com/docs/en/sub-agents).
- **Auto memory** [V] (memory docs):
  - On by default. It can be disabled with `autoMemoryEnabled: false`,
    `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, or the `/memory` toggle. `autoMemoryDirectory`
    relocates it.
  - Stored at `<config dir>/projects/<project>/memory/`. The `<project>` key is derived from the
    git repository, so "all worktrees and subdirectories within the same repo share one auto
    memory directory".
  - It is "machine-local ... not shared across machines".
  - Layout: a `MEMORY.md` index with one line per memory, plus topic files with `type:
    user|feedback|project|reference` frontmatter.
  - Only the first 200 lines or 25KB of `MEMORY.md` load at startup. Claude Code tells the agent
    to shorten the index when it is over that limit.
  - It skips anything derivable from code or already in CLAUDE.md. There is no TTL, and memory is
    excluded from the `cleanupPeriodDays` sweep.
  - The `/memory` toggle cannot turn auto memory on in "a session that another Claude Code
    session started".
- **Subagent `memory:` frontmatter** [V] (sub-agents docs):
  - Three scopes:
    - `user`: `~/.claude/agent-memory/<agent>/`.
    - `project`: `.claude/agent-memory/<agent>/`, "shareable via version control".
    - `local`: `.claude/agent-memory-local/<agent>/`.
  - The first 200 lines or 25KB of that agent's `MEMORY.md` are injected into its system prompt.
    Read, Write and Edit are auto-enabled.
  - It has no effect when auto memory is disabled, and the main session's auto memory is not
    loaded into subagents.
  - Consulting and updating memory are prompt-driven: the docs tell you to instruct the agent to
    read memory first and update it at the end.
- **Hooks** [V] https://code.claude.com/docs/en/hooks:
  - Relevant events: SessionStart, SessionEnd, PreCompact, PostCompact, Stop, SubagentStart,
    SubagentStop, UserPromptSubmit, InstructionsLoaded.
  - SessionStart (matchers startup/resume/clear/compact) and SubagentStart can inject
    `additionalContext`.
  - SessionEnd cannot block and gets 1.5 s unless a per-hook `timeout` is set (up to 60 s).
  - PreCompact can block compaction. PostCompact receives `compact_summary`.
  - SubagentStop receives `agent_type` and `last_assistant_message`.
  - Hook types: `command`, `http`, `mcp_tool`, `prompt` (single-turn), and `agent` (experimental,
    Read/Grep/Glob, 60 s).
  - Subagent and skill frontmatter may define `hooks:`. Frontmatter hooks fire when the agent
    runs as a subagent and "when the agent runs as the main session via `--agent` or the `agent`
    setting" (sub-agents docs). Skill hooks register on invocation and run for the rest of the
    session. [I] Hooks could therefore ship in `supervisor.md` frontmatter with no deploy change.
- **Local observation** [V]:
  - `~/.config/claude-supervisor/projects/-Users-sjoosten-Work-claude-agents/memory/` exists and
    is empty (`ls -la`). So is every `~/.claude/projects/*/memory/` dir that was checked.
  - There is no `agent-memory/` dir and no `memory:` key in `pack/`.
  - This session's environment has `CLAUDE_CODE_CHILD_SESSION=1`.
  - [I] Child sessions, plus the docs' caveat about sessions started by another session, are a
    plausible reason that auto memory never writes here. The cause is not established.

### 1.2 Anthropic API Memory Tool, Context Editing, Harness Posts

- [V] https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool:
  - Tool `memory_20250818`, client-side, with commands view/create/str_replace/insert/delete/
    rename under `/memories`.
  - The injected prompt says "ALWAYS VIEW YOUR MEMORY DIRECTORY BEFORE DOING ANYTHING ELSE ...
    ASSUME INTERRUPTION".
  - The application is told to validate paths, strip sensitive data, cap file and view sizes, and
    expire files that have not been accessed for a long time.
  - Suggested prompt: keep memory "up-to-date, coherent and organized ... rename or delete files
    that are no longer relevant".
- [V] https://platform.claude.com/docs/en/build-with-claude/context-editing:
  - `clear_tool_uses_20250919` (trigger, keep, `clear_at_least`) and `clear_thinking_20251015`.
  - Near the clear threshold the model is warned to save to memory first.
- [V] Anthropic engineering, "Effective harnesses for long-running agents"
  (https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents):
  - An initializer session, a progress file plus `git log` as memory, and a JSON feature list in
    which only `passes` may change.
  - A session-start routine: read progress and git log, then run a basic check.
- [V] Anthropic engineering, "Effective context engineering for AI agents"
  (https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents): structured
  note-taking
  outside the window, subagents that return condensed summaries, and just-in-time retrieval
  through file-path pointers.

### 1.3 Memory Frameworks

- **Letta/MemGPT** [V] https://arxiv.org/html/2310.08560,
  https://docs.letta.com/guides/core-concepts/memory/memory-blocks,
  https://www.letta.com/blog/sleep-time-compute, https://docs.letta.com/concepts/memfs:
  - Core memory blocks are always in context and each has a character `limit`. Recall memory
    holds searchable message history and archival memory holds long-form text.
  - The agent pages data in and out with tool calls.
  - Sleep-time agents consolidate the primary agent's memory in the background, and the primary
    agent cannot edit it.
  - Letta Code's MemFS is a git-backed directory of Markdown files with frontmatter. Files in
    `system/` load every turn and the rest load on demand.
- **Mem0** [V] https://arxiv.org/abs/2504.19413:
  - An LLM extracts candidate facts. Each candidate is compared with the top 10 similar memories,
    and the LLM picks ADD, UPDATE, DELETE (on contradiction) or NOOP.
  - The graph variant marks contradicted edges invalid instead of deleting them.
  - On LoCoMo, full context still scored highest (72.9% at about 26k tokens), against Mem0's
    66.9% at 1.8k. Memory is mainly a cost lever.
- **Zep/Graphiti** [V] https://arxiv.org/abs/2501.13956:
  - A bi-temporal graph: each fact edge carries `t_valid`/`t_invalid` plus ingestion times.
  - On contradiction the old edge is invalidated ("prioritizes new information"), never deleted.
  - Separate episodic and semantic subgraphs.
- **LangGraph/LangMem** [V] https://langchain-ai.github.io/langmem/concepts/conceptual_guide/:
  - Short-term memory is per-thread checkpoints. Long-term memory is a namespaced store.
  - Memory types: semantic, episodic, procedural.
  - Hot-path writes are immediate but add latency. Background writes allow deeper consolidation.
  - Over-extraction hurts precision.
- **Generative Agents** [V] https://arxiv.org/abs/2304.03442:
  - Retrieval score = recency (0.995 decay per hour) + importance (1-10) + relevance.
  - Reflection runs when summed importance exceeds 150 and writes cited insights.
- **A-MEM** [V] https://arxiv.org/html/2502.12110: Zettelkasten notes with LLM-made links. New
  notes rewrite their neighbors' attributes ("evolution"), so history is lost. Mem0's independent
  run scored it lowest (48.4%).

### 1.4 Coding Assistants

- **GitHub Copilot Memory** [V] https://docs.github.com/en/copilot/concepts/agents/copilot-memory,
  https://github.blog/ai-and-ml/github-copilot/building-an-agentic-memory-system-for-github-copilot/:
  - Record shape: subject, fact, citations (`file:line`), reason.
  - "Before applying any memory, the agent is prompted to verify its accuracy and relevance by
    checking the cited code locations."
  - When a memory is contradicted, the agent stores a corrected version. A memory that checks out
    is re-stored, which refreshes it.
  - Unused memories are deleted after 28 days.
  - GitHub chose just-in-time verification over offline curation as cheaper.
  - Reported result: PR merge rate rose from 83% to 90%. Seeded false memories self-healed.
- **Cursor** [V] https://cursor.com/docs/context/rules:
  - `.cursor/rules/*.mdc` rules are committed and carry `alwaysApply`, `globs` and
    `description`.
  - Memories (2025) were per-user and stored outside the repo. Background-proposed memories
    needed user approval [C].
  - The Memories UI was reportedly removed in 2.1.x, with export to Rules as the migration [C,
    unconfirmed officially].
- **Windsurf/Cascade** [V] https://docs.devin.ai/desktop/cascade/memories: auto-generated memories
  are local and "not committed to your repository". The docs steer durable knowledge to committed
  rules or AGENTS.md.
- **Cline Memory Bank** [V] https://docs.cline.bot/features/memory-bank:
  - Committed markdown (`projectbrief.md`, `activeContext.md`, `progress.md`, ...).
  - "I MUST read ALL memory bank files at the start of EVERY task." It has no staleness check.
- **OpenAI Codex** [V] https://learn.chatgpt.com/docs/customization/memories:
  - Memories are local, off by default, and generated in the background.
  - "Treat memories as a helpful recall layer, not as the only source for rules that must always
    apply."

### 1.5 Architecture Decision Records

- [V] Nygard (cognitect.com/blog/2011/11/15/documenting-architecture-decisions):
  - Sections: Title, Context, Decision, Status, Consequences.
  - "If a decision is reversed, we will keep the old one around, but mark it as superseded."
- [V] MADR 4.0 (https://adr.github.io/madr/):
  - Sections include Decision Drivers, Considered Options, "Chosen option X, because ...", and
    Consequences.
  - Statuses: proposed, rejected, accepted, deprecated, and "superseded by".
  - "The collection of ADRs ... constitute its decision log."
- [V] log4brains (https://github.com/thomvaill/log4brains): "an ADR is immutable. Only its status can change". Dropping required
  sequence numbers "avoids git merge issues". Its examples use date-prefixed names.
- [V] Numbering collisions: a local experiment produced two `0002-*.md` files from parallel
  branches that merged silently (section 4).

### 1.6 Taxonomy

- [V] CoALA (https://arxiv.org/abs/2309.02427) defines four memories:
  - working memory;
  - episodic memory (experiences);
  - semantic memory (facts);
  - procedural memory (agent code or prompts). The paper notes that writing procedural memory is
    riskier than writing episodic or semantic memory.
- [I] Mapped onto the pack:
  - working memory: plans, research, and program state;
  - episodic: run logs;
  - semantic: decisions and learned facts;
  - procedural: `pack/agents`, `pack/skills`, CLAUDE.md, and `docs/writing-rules.md` Standing
    Rules. These stay human-gated.
- [C] A 2025 survey, "Memory in the Age of AI Agents" (https://arxiv.org/abs/2512.13564), was seen
  through its abstract only.

### 1.7 Harms Of Stale Memory, And Simple Versus Complex

- [V] https://arxiv.org/abs/2505.16067:
  - Retrieved erroneous memories are copied and re-stored, and the error compounds.
  - Selective addition with deletion beat naive growth by about 10 points absolute.
- [V] LongMemEval (https://arxiv.org/abs/2410.10813) tests knowledge updates explicitly and
  reports about a 30% accuracy drop for commercial assistants over sustained interactions.
- [V] MINJA (https://arxiv.org/abs/2503.03704) poisons agent memory through ordinary queries
  alone. [C] Its attack rates came from idealized conditions, and existing legitimate memories
  reduce them (arXiv 2601.05504).
- [V] https://www.letta.com/blog/benchmarking-ai-agent-memory: a filesystem-tools agent scored
  74.0% on LoCoMo against Mem0's reported 68.5%, and "even simple filesystem tools are
  sufficient". [I] This is a vendor benchmark set against the competitor's self-reported numbers.

### 1.8 Patterns Extracted

| Phase | Pattern | Seen in |
|---|---|---|
| Write | Working agent writes in the hot path when it learns something | Letta tools, LangMem, API memory tool, Copilot |
| Write | Separate consolidator pass in the background | Letta sleep-time, LangMem background, Letta "dreaming" |
| Write | Auto-proposals need approval; required rules stay human-written | Cursor, Codex, Windsurf, ADR review |
| Consolidate | Compare candidate with neighbors, then ADD/UPDATE/DELETE/NOOP | Mem0 |
| Consolidate | Threshold-triggered reflection with citations | Generative Agents |
| Retrieve | Small always-loaded core plus on-demand detail | Letta core/MemFS `system/`, auto memory index, Cursor/Copilot path-scoped rules |
| Retrieve | Agentic search with file tools | Letta filesystem, API memory tool |
| Expire | Unused deletion after a fixed period (28 days) | Copilot |
| Expire | Expire long-unaccessed files (application's job) | API memory tool docs |
| Staleness | Citations validated against current code before use | Copilot |
| Staleness | Supersede with validity interval, never silently edit | Graphiti, Mem0g, ADRs |
| Staleness | Cap and prune the index | Claude Code auto memory, Letta block limits |

## 2. Fit To The Pack (Q2)

The constraints: file-based subagents and skills, no external services by default, a stdlib-only
`deploy` on Python 3.9, and per-tier word caps (section 3).

| Pattern | Verdict | Reason |
|---|---|---|
| Hot-path write by the working agent | Fits in simplified form | Many writers make conflicts and duplicates. Keep two writers with disjoint jobs: `quick-edit` records, `scribe` curates (section 8). |
| Background consolidator | Fits in simplified form | No daemon exists. Make it a dispatched agent run at program close-out and on request [I]. |
| ADD/UPDATE/DELETE/NOOP against neighbors | Fits in simplified form | Find neighbors by grep on `affects:` and `summary:`, not vector top-k. "UPDATE" becomes supersede [I]. |
| Importance-scored retrieval, recency decay | Does not fit as specified | Needs embeddings or scores. The `verified:` date plus a git-change check is the cheap substitute [I]. |
| Always-loaded small core | Fits in simplified form | A committed single index file conflicts on merge (section 4). Derive the index with one grep over frontmatter [I]. |
| Agentic search with file tools | Fits as-is | Grep and Glob are already available to every lead. The Letta benchmark supports it. |
| Vector, graph, hybrid rerank | Does not fit | Needs a service or embeddings. |
| Citation validation (Copilot) | Fits as-is | `affects:` paths plus `git log --since=<verified> -- <paths>` is stdlib-free and cheap [I]. |
| Supersede, never edit (ADR, Graphiti) | Fits as-is | Status line on the old file and a pointer to the new one. Git keeps history. |
| Fixed-period unused deletion | Fits with care | Decisions are few and long-lived, so supersession suits them better. A period may suit learned facts (D6). |
| Procedural writes by agents | Does not fit | The owner's rule (`ROADMAP.md:16-18`) adds rules only for observed failures. Lessons that imply a rule go to the user as proposals. |
| Claude Code `memory:` frontmatter | Fits poorly | It is per agent name, depends on auto memory being on (unverified in child sessions), auto-enables Write/Edit (breaks read-only `scout`/`critic`), and keeps a single `MEMORY.md` index [V]/[I]. |
| Hooks (SessionStart and others) | Defer | Shippable through `supervisor.md` frontmatter, which also fires for the main session [V], and deploy copies frontmatter as-is (`deploy:281-353`). Deferred under the owner's observed-failure rule, not for feasibility [I]. |

## 3. Baseline: How The Pack Persists Today (Q7)

- **Research** [V]: `docs/research-<topic>.md`, written by `researcher`
  (`pack/agents/researcher.md:16`). `planner` treats anything under `docs/archive/` as never fresh
  (`pack/agents/planner.md:41`).
- **Plans and program state** [V]:
  - Plans are `docs/plan-<topic>.md`, with required sections at `planner.md:24-32`.
  - Work-package blocks (Goal/Owns/Deps/Stages/Status/Artifacts) are at `planner.md:54-62`.
  - After each wave, `quick-edit` advances `Status` (`supervisor.md:86-87`). `executor` ticks
    `## Todo` (`executor.md:28-31`).
  - The supervisor never reads the plan. It gets state from `planner`'s report or one `scout`
    call (`supervisor.md:82`).
- **Archive** [V]: at completion, `quick-edit` moves the plan, its child plans and its research to
  `docs/archive/` (`supervisor.md:89-91`).
- **Writing rules** [V]: `docs/writing-rules.md` has three sections: Standing Rules, Session
  Decision Log, Pending Verification (`pack/skills/writing-rules-persistence/SKILL.md:14-22`).
  - Precedence is at `SKILL.md:26-32`.
  - Only the writer lead edits the file, after per-item user approval
    (`references/lead-procedures.md:35-44`).
  - [I] This is the pack's existing precedent for a committed per-project memory file with a
    schema and gated writes.
- **Supervisor memory** [V]: `supervisor.md:100` says "You may write and edit only your memory
  files." No pack file defines them, and the auto-memory dir is empty (section 1.1). [I] In
  effect this means Claude Code's auto memory for the main thread.
- **Lead decision log** [V]: per run, in the lead's report only (`lead-loop/SKILL.md:110`). It is
  not persisted.
- **What ROADMAP item 1 found lost** [V, line refs re-checked]:
  - The mid-program `--prefix` decision exists only in the archived plan's ad hoc `## Decisions`
    (`docs/archive/plan-install-lifecycle.md:408-415`).
  - The glue Todo items at L422, L428, L433 and L437 are unticked with no reason given. L438 is
    also unticked.
  - `docs/archive/plan-wbs.md:276` explicitly excluded persistence features.
  - Stale ROADMAP pointers: README "Larger Work" is L83-149, not L74-140, and the package block is
    near L90-99, not L78-91.
- **Budgets** [V] (`tests/test_pack_lint.py:21`):
  - Caps: Main 1000, Lead 700, Review 600, Worker 400, Quick 350. Skills 1300 words and 300
    lines.
  - Body-word headroom: supervisor 42, planner 87, critic 17, git-ops 17, writer-worker 50,
    executor 326, researcher 511, quick-edit 130, scout 206, lead-loop skill 298.
  - [I] The supervisor is the binding constraint. Memory logic belongs in a skill or a new agent,
    with at most one routing line in the supervisor.
- **Deploy** [V]: `collect_source` (`deploy:281-353`) ships only `pack/agents/*.md` and
  `pack/skills/**`, and deploy never touches project repos (`docs/deploy.md`). Tests: 315 passed,
  5 skipped, in 58.6 s.

## 4. Storage Location (Q4)

Git experiments (git 2.54.0, scratch repo):
- [V] Two branches appending to one `log.md`: `CONFLICT (content)`.
- [V] One file per entry merged cleanly. Sequential numbers collided silently (two `0002-*`
  files).
- [V] `merge=union` merged appends, but reordered inserts and kept both versions of a line edited
  on both sides. Git's own docs: union "tends to leave the added lines in the resulting file in
  random order" (https://git-scm.com/docs/gitattributes). It does not fit an index or structured
  file.
- [V] A new worktree contains only tracked files: ignored and untracked files are absent.
  `.git/info/exclude` is shared through the common dir.
- [V] https://code.claude.com/docs/en/worktrees: `.worktreeinclude` copies matching gitignored
  files into new Claude Code worktrees.

| | A: committed project dir | B: gitignored project dir | C: user-global, keyed per repo | D: hybrid (shared memory committed, personal global) |
|---|---|---|---|---|
| Privacy | Weak; persists in history [I] | Good, but `project-backup` zips it [V] | Best [V] | Shared part needs a no-secrets rule [I] |
| Collaborators | Shared [V] | No [V] | No [V] | Decisions shared [I] |
| Multiple machines | Via git [V] | No [V] | No; auto memory is machine-local [V] | Shared part via git [I] |
| Merge conflicts | Clean with one file per entry, no sequence numbers [V] | None [I] | None [I] | As A [V] |
| Worktrees (dev flow) | Tracked, so present in a worktree once merged into its branch [V] | Absent unless `.worktreeinclude` [V] | Shared per repo (auto memory) [V] | As A for shared [V] |
| Audit | Diffable, reviewable [V] | Local only [I] | Hidden, not diffable [I] | Shared part diffable [I] |
| Repo noise | Highest [I] | One ignore line [I] | None [V] | Moderate [I] |
| Non-git dirs | Works as files, no history [I] | Works [I] | Keyed by project root [V] | Works [I] |

- Security [V]:
  - The workspace trust dialog gates permission rules, MCP servers and external imports. It is
    never shown for `-p` or SDK runs (https://code.claude.com/docs/en/security).
  - OWASP LLM01: "Separate and clearly denote untrusted content"
    (https://genai.owasp.org/llmrisk/llm01-prompt-injection/).
  - [I] A committed memory dir is a persistent injection channel from collaborators or cloned
    repos. Entries must be read as claims to check, never as instructions.
- Precedent [V]:
  - Shared, durable guidance is committed: CLAUDE.md, `.cursor/rules`, Copilot instructions,
    Cline `memory-bank/`, ADRs.
  - Personal or auto-generated memory is local or per-user: CLAUDE.local.md, Claude Code auto
    memory, Cursor and Windsurf memories, Codex.
  - [I] The industry split is the hybrid D.
- [I] Dot-directories are hidden in Finder and, by default, in Obsidian, which the user's
  `project-backup` skill anticipates. A hidden working set would make plans awaiting approval
  less visible. This is unverified for Obsidian and bears on D2.

## 5. Scribe/Librarian Design (Q3)

The hypothesis, a dedicated memory owner, is supported in simplified form: Letta sleep-time
agents, the LangMem background manager. Copilot's evidence favours just-in-time checks over a
curation pass. At this pack's scale (a few entries per program) a curation pass is cheap [I].
The split between the scribe, which owns memory, and the readers, which retrieve it, is
supported. The variant where scout serves as every agent's retriever is not.

- **Responsibilities** [I]:
  - At program close-out, distill the plan's decisions, assumptions, log and research into
    long-term entries. Allowed kinds: user decisions, decisions taken by leads that bind later
    work, and verified facts with a source.
  - Before writing, grep for neighbors and choose new, supersede, or no-op (Mem0's operations,
    with supersession in place of edits).
  - Re-verify entries whose `affects:` paths the program changed: confirm them or supersede them.
  - Archive the working set, which absorbs the current `quick-edit` archive step
    (`supervisor.md:89-91`).
  - Handle explicit "remember X" and "forget X" requests from the user.
  - Return lessons that imply a procedural change as proposals for the user. It never edits
    `pack/`, CLAUDE.md, or writing rules.
- **Not its job** [I]:
  - Retrieval for others. Leads grep the store themselves at contract time. That costs one tool
    call, and a scout hop would add a dispatch.
  - Per-wave bookkeeping, including mid-program decision entries, which stays with the existing
    post-wave `quick-edit`.
- **Scout's role** [I]: on resume, the supervisor's existing `scout` call on the plan
  (`supervisor.md:82`) also returns the summaries of active entries that touch the program. This
  matches the user's "scout retrieves" idea only for the supervisor. The supervisor is told not to
  read files itself (`supervisor.md:95-99`) and never reads the plan (`supervisor.md:82`).
- **Triggers**:
  - Program close-out (main).
  - An explicit user request.
  - Optionally, a single-stage Mode 1 run whose report carries a user decision.
  - Hooks are a poor trigger for now [V/I]: SessionEnd has a 1.5 s default budget, and `agent`
    hooks are experimental and read-only, so neither can run a distillation.
- **Model and tier** [I]: distillation and contradiction checks need judgment beyond a "fully
  specified edit" (the `quick-edit` contract), so Sonnet is the natural fit. Tier-table rows
  assign models (`agent-authoring/SKILL.md:10-19`, tested), and tiers already mix models, so a
  Sonnet quick specialist needs a new row (D4).
- **Cost** [I]: one Sonnet dispatch per finished program, reading one plan plus its research and
  grepping the store. That is about one worker call against a Mode 1 program of many calls.
  Mode 2 costs nothing.
- **Failure modes and mitigations** [I]:
  - It drops something important: every entry keeps `source:` pointing at the archived plan, and
    git keeps the archive.
  - It writes wrong or over-general entries (error propagation): only user decisions and verified
    outcomes, never raw traces, with a small per-program cap.
  - It never runs (abandoned program): the working set stays, and resume shows it, so nothing is
    lost, only not distilled.
  - It contradicts an existing entry silently: the neighbor grep plus supersede rule.
  - Poisoned entries from collaborators: entries are data, readers verify `affects:`, and changes
    show in diffs.
  - It duplicates auto memory: the scope split in D8.

## 6. Lifecycle (Q5)

```
  working set (short-term)            long-term store             archive (cold)
  research, plan, Assumptions,  --->  decisions, facts      --->  superseded entries stay in place
  log, Status                 distill (status, affects,           (status line); working sets
            |                  scribe   verified, source)         are moved here and never read
            +-------------------------------------------------->  by default (planner.md:41)
                              archive (scribe, git mv)
```

- **Short-term** [I]:
  - The plan gains `## Assumptions` (one line each, with how each will be checked) and a `## Log`
    (one line per top-level dispatch, with deferrals and why). Both are ROADMAP item 1
    candidates.
  - Mid-program user decisions are written straight to the long-term store when made, because a
    later stage depends on them. The plan's Scope Notes list them as links.
- **Entry schema** [I], one file per entry, named `YYYY-MM-DD-<slug>.md` with no sequence numbers
  (section 4):

  ```
  ---
  kind: decision            # decision | fact
  status: active            # active | superseded by <file>
  summary: <one line>       # the index line
  affects: [deploy, pack/agents/planner.md]
  verified: 2026-10-17
  source: docs/archive/plan-install-lifecycle.md#decisions
  ---
  Decision. Why (drivers, rejected options). Consequences.
  ```
- **Staleness controls** [I], borrowing the Copilot and ADR patterns:
  - A reader checks `affects:` before relying on an entry. If paths are gone, or `git log
    --since=<verified> -- <affects>` shows changes, the entry is a claim to re-check, not a fact.
    The git-change check targets `fact` entries. `decision` entries change only through the
    close-out sweep or supersession, because the program that records a decision usually edits
    its `affects:` paths.
  - Supersede rather than edit.
  - At close-out the scribe re-verifies entries the program touched.
  - Archived working sets are never read by default.
  - [I] Outside git (non-repo vaults) the check degrades to file mtime.
- **Migration from `docs/`** [I]:
  - Relocation is separable from the memory model. Stage 4 moves new programs' working sets out
    of `docs/` and leaves existing files where they are.
  - Before relocation, the long-term store reads existing `docs/` plans as `source:`. That avoids
    a big-bang move of paths referenced across agents, README and architecture (Stage 4 lists
    them).

## 7. Lightweight Path And Invisibility (Q6)

- **Mode 2**: no memory reads and no writes. The one exception is an explicit "remember" or
  "forget", which routes to the scribe [I]. This keeps the one-Haiku-call cost
  (`docs/architecture.md`, Models And Cost).
- **Single-stage Mode 1 without a plan**:
  - The lead runs one grep over the store's `summary:`/`affects:` lines during its contract step,
    and only if the store exists.
  - The rule lives in `lead-loop` (298 words of headroom, outside the agent body caps) [V/I].
  - No scribe runs unless the run produced a user decision.
- **Invisible to the user** [I]:
  - The store is created lazily on first write, and the user never edits it.
  - The supervisor adds one line to its answer ("recorded 2 decisions").
  - The only prompts are the ones that exist today: user decisions, plus scribe proposals that
    would change procedure. Those batch with the supervisor's normal questions.
- **Cost guard** [I]: summary lines and a cap per program keep reads small. There is no
  always-loaded index to grow, unlike Cline's load-everything model.

## 8. Recommended Architecture

1. **Three project stores, sorted by lifetime** [I]:
   - working set (short-term; plans, research, program log);
   - long-term (`decision` and `fact` entries, one file each);
   - archive (cold).
   All are committed (storage option D's shared part), and the location is D1/D2.
2. **Personal memory stays in Claude Code auto memory**: user preferences and routing feedback.
   This gives the supervisor's existing "memory files" clause a concrete meaning. No project
   decisions go there [I].
3. **Two writers with disjoint jobs** [I]:
   - At every stage, the existing post-wave `quick-edit` writes the mid-program decision entries
     that the supervisor dictates.
   - The `scribe` (from Stage 3) owns close-out distillation, re-verification and supersession,
     It also runs on explicit request and after a single-stage run that produced a user
     decision.
4. **Readers retrieve just in time**:
   - Leads grep at contract time and pass relevant entries to workers in briefs.
   - The supervisor gets entry summaries from its existing resume `scout` call.
   - Workers never search memory.
5. **Validate before use, supersede rather than edit**: `affects:`, `verified:` and `source:` on
   every entry, and git as history.
6. **Unchanged**:
   - `docs/writing-rules.md`, a proven per-draft precedence model.
   - Procedural memory (`pack/`, CLAUDE.md), which stays human-gated.
   - The supervisor-lead-worker nesting (`plan-wbs.md:278`).
7. **Science artefacts constraint** [I]: that item is not in ROADMAP.md yet. `affects:` should
   accept any repo path (data files, figures), not only code. The staleness check should work on
   paths in general so that a later artefacts feature can reuse it.

## 9. Staged Roadmap Proposal

Each stage is useful alone and lands with the minimum rule text. ROADMAP's current candidates map
to Stages 1 and 2.

**Stage 1: Decision records.**
- Goal: no user decision, or lead decision binding later stages, is lost between sessions or
  packages.
- Scope:
  - A new `project-memory` skill holding the entry schema, naming, the supersede rule and the
    validate-before-use rule.
  - The long-term store directory (D1/D2).
  - The supervisor has the post-wave `quick-edit` write an entry when a user answer or lead
    decision binds later stages (about one supervisor line, within the 42-word headroom).
  - `lead-loop` contract step: grep the store if it exists.
- Done when:
  - On the dev tag, a program's mid-program decision is recorded as an entry.
  - A new session's planner cites it unprompted.
  - The suite passes with no cap raised.
- Dependencies: D1, D2, D5, D11.
- Departs from the ROADMAP's single-file `docs/decisions.md` (D11; D11 also covers the log). A plain merge of parallel
  appends conflicts. `merge=union` merges them but needs a `.gitattributes` entry and leaves the
  lines in random order (section 4). A one-line entry has no room for reasons or `affects:`.

**Stage 2: Program state that explains itself.**
- Goal: a resumed session can say what ran, what was deferred, and why.
- Scope:
  - `## Assumptions` and `## Log` in plans (`planner.md` Artifact; 87 words of headroom).
  - The post-wave `quick-edit` appends one log line per top-level dispatch, including deferrals
    such as the unticked glue items.
  - The supervisor's resume `scout` call returns the log tail.
  - The log lives in the plan, not in the separate logbook index the ROADMAP sketched. It is
    distilled and archived with the plan.
- Done when: on a replay of an install-lifecycle-style program, `scout` answers "why is L422
  unticked" from the plan alone.
- Dependencies: none (it uses Stage 1 links if present).

**Stage 3: Scribe close-out.**
- Goal: finished programs leave distilled knowledge behind, and nothing stale in view.
- Scope:
  - A new `scribe` agent covering distill, neighbor check, supersede, the re-verify sweep,
    archive, and remember/forget. It replaces the archive `quick-edit` step.
  - Tier table and `docs/architecture.md` inventory updates. `fact` entries start here.
- Done when:
  - Closing a dev-tag program yields a few entries, each with `source:` and `affects:`, plus an
    archived plan.
  - A seeded contradictory entry ends up superseded.
  - An entry whose `affects:` file changed gets re-verified or superseded.
- Dependencies: Stage 1 (store). D4, D6, D7. Supervisor text for scribe routing, remember/forget
  and the "recorded N" line needs either a swap of the archive `quick-edit` text
  (`supervisor.md:89-91`) for the scribe dispatch, or a Main cap raise with owner approval.

**Stage 4: Move the working set out of `docs/`.**
- Goal: agent working state is separate from the project's human documentation.
- Scope:
  - New programs write research, plans and logs under the working-set dir. The scribe archives
    them to the memory archive.
  - Path updates in `researcher`, `planner`, `supervisor`, `executor`, README and architecture.
  - No automatic migration of existing `docs/plan-*`.
- Done when: a full program writes nothing to `docs/` except documents the user asked for, and
  the suite passes.
- Dependencies: Stage 3 (archive owner). D2, D3.

**Stage 5 (conditional): Retrieval automation.**
- Goal: relevant memory arrives without an explicit lookup step.
- Scope:
  - A SessionStart or SubagentStart hook injecting active summaries, shipped in `supervisor.md`
    frontmatter.
- Done when: an observed failure from Stages 1-4 (a relevant entry missed) is fixed by it. Per
  the owner's rule, this stage starts only on such a failure.
- Dependencies: Stages 1-3. D10.

## 10. Decisions For The User

| ID | Decision | Options | Recommendation |
|---|---|---|---|
| D1 | Where long-term memory lives | (a) project dir, committed; (b) project dir, gitignored; (c) user-global per repo; (d) Claude Code `memory: project` dir `.claude/agent-memory/scribe/` | (a). (a) and (d) are the options that serve both collaborators and multiple machines (section 4). Entries are branch-scoped, visible in other worktrees after merge. (d) depends on auto memory and keeps a single `MEMORY.md` |
| D2 | Directory name | `.supervisor/`; `supervisor/` (visible); `docs/supervisor/`; `.claude/supervisor/` | `.supervisor/` for the long-term store. Revisit for the working set at Stage 4 if hidden plans hurt review (an Obsidian or Finder visibility check is open) |
| D3 | Move research and plans out of `docs/` | yes, new programs only; yes with migration; no | Yes, new programs only, as Stage 4 after the scribe exists |
| D4 | Scribe model and tier | Haiku Quick tier; Sonnet with a tier-table change; no new agent (a skill applied by `quick-edit`) | Sonnet as a new agent. Distillation exceeds `quick-edit`'s fully-specified contract. This also moves the archive step from `quick-edit` to the scribe, revising `plan-wbs.md:278` |
| D5 | Who writes mid-program decision entries (ROADMAP leaves this to planner) | supervisor via post-wave `quick-edit`; the deciding lead; the scribe, once per decision | `quick-edit`, at every stage. The post-wave dispatch already exists, so it adds no dispatch |
| D6 | Expiry | none (supersede only); flag on `affects:` change; also archive `fact` entries unverified for N months | Flag on change. Add time-based archiving for `fact` entries only if staleness is observed |
| D7 | What long-term memory holds | decisions only; decisions plus verified facts; plus lessons | Decisions in Stage 1, facts in Stage 3. Lessons only as proposals for the user |
| D8 | Relation to auto memory and writing rules | separate scopes (personal vs project; writing rules untouched); fold writing rules into the store | Separate scopes |
| D9 | Release packaging | Stages 1-2 as v2.0, later stages 2.x; everything in one v2.0 branch | Stages 1-2 as v2.0. They cover the ROADMAP candidates, and 3-5 follow as 2.x |
| D10 | Hooks | never; only after an observed retrieval failure; now (in `supervisor.md` frontmatter) | Only after an observed failure |
| D11 | Format of the ROADMAP candidates: `docs/decisions.md` (one line per decision) and the run logbook index | Decisions: single append-only file, optionally with `merge=union`; or one file per entry. Log: separate logbook index file; or a `## Log` in the plan, archived with it | One file per decision entry: it has room for reasons and `affects:`, and it merges cleanly without union's reordering. Log in the plan, so the run history travels with the program it describes |

## 11. Risks, Open Questions, Gaps

- Risks [I]:
  - A committed store leaks secrets or personal notes into history. `git-safety` secret checks
    apply only at commit time.
  - Collaborator or cloned-repo entries carry injected instructions.
  - Readers skip the validate step, and stale entries mislead them.
  - Rule text eats scarce headroom: supervisor 42 words across Stages 1-3, and planner 87.
- Open questions:
  - Does auto memory write in child or nested sessions? `CLAUDE_CODE_CHILD_SESSION=1` was
    observed. To check: run a plain sandbox session and look for files under
    `projects/*/memory/`.
  - Does Claude Code gate edits under `.claude/` in some permission modes? This matters only if
    D2 picks `.claude/supervisor/`.
  - Does Obsidian hide dot-directories by default? Relevant to D2.
- Gaps:
  - Rename and move behavior of `projects/<key>/` is undocumented and untested.
  - Cursor Memories' current status is unconfirmed.
  - MINJA figures were not checked in the paper.
  - The 2512.13564 survey was read through its abstract only.
  - Git experiments ran on git 2.54.0, macOS only.
