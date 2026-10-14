# Research: Porting opencode-agents to a Claude Code supervisor ecosystem

Scope: what to keep, drop, and redesign when moving `../opencode-agents` (OpenCode, Argo-routed
models) to Claude Code 2.1.29x with Fable 5.1 / Opus 5.5 / Sonnet 5.5 / Haiku 5.5.
Sources: the old repo (`src/core`, `src/writing`, `scripts/deploy-agents`, `AGENTS.md`, `docs/`)
and the Claude Code docs (code.claude.com/docs/en/sub-agents, /skills, /settings-reference,
/plugins, /agent-teams, /model-config), read 2026-10-14.

## 1. Old system in one paragraph

22 agents (18 core, 4 writing) and 12 skills. A read-only `supervisor` routed each request to one
specialist per domain (researcher, planner, editor, git-expert, doc-writer, python-maintainer,
meeting-summarizer, agent-builder, ...). Each producer was paired with its own critic
(research-critic, planning-critic, implementation-critic, code-reviewer, agent-critic,
science-critic), and the supervisor ran up to 3 critique rounds. Workers did all the work
themselves; there was no fan-out below the supervisor except in `genius`/`genius-worker`.
Deployment was a 3600-line stdlib Python script. Most of it was Argo provider management; the
rest was manifest-tracked copying with 3-way hash reconciliation. A TOML profile tool rewrote
`model:` lines per profile.

## 2. Claude Code capabilities that change the design

| Capability | Fact (docs) | Consequence |
|---|---|---|
| Nested subagents | A subagent with `Agent` in `tools` can spawn subagents, up to 3 layers below the main thread (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`). The type allowlist `Agent(a,b)` is ignored inside subagent definitions; it works only for the main-thread agent. | supervisor (0) -> lead (1) -> workers/critics (2) fits the default limit. Leads are restricted by prompt; the supervisor is restricted by `Agent(...)`. |
| Main-thread agent | `"agent": "<name>"` in settings.json or `claude --agent <name>`. The agent's model, tools, and prompt replace the defaults. | The supervisor can be the global default and runs on Fable. |
| Per-agent model and effort | Frontmatter `model` (alias `fable/opus/sonnet/haiku`, full ID, or `inherit`) and `effort` (`low..max`). | No profile tool is needed. |
| Dispatch-time override | The Agent tool takes per-call `model` and `effort`. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` disables both overrides. | One `critic` file is enough: the planner dispatches it with `model: fable`. |
| Skills | `skills/<name>/SKILL.md`, loaded on demand. Agents can preload skills with the `skills:` frontmatter field. `context: fork` runs a skill in a subagent. | Shared protocols (lead loop, git safety) become preloaded skills, so the prompt text is not duplicated across agents. |
| Plugin agents | Namespaced `plugin:name`; `permissionMode`, `hooks`, and `mcpServers` are ignored. | Install into `~/.claude/{agents,skills}` instead, which gives short names and full frontmatter. |
| Built-in tools/skills | WebSearch/WebFetch, `/code-review`, `/security-review`, `/simplify`, and Anthropic document skills (docx/pdf/pptx/xlsx via the `anthropics/skills` marketplace). | Drop `ddgr`, `docx`, `pdf`, `pptx`, `xlsx`, and `code-reviewer`. |

## 3. Keep / drop / transform

### Agents (22 -> 13)

| Old | New | Why |
|---|---|---|
| supervisor | `supervisor` (Fable) | Same role. Adds the two-mode routing and the main-thread role. |
| researcher, planner, editor | `researcher`, `planner` (Fable), `executor` leads + workers | Leads fan out to parallel workers. |
| writer, science-writer, genius-science-writer | `writer` lead + `writer-worker` (Opus) | Same loop on the shared harness. "Genius" becomes a per-call `model: fable` override. |
| research-/planning-/implementation-critic, code-reviewer, agent-critic, science-critic | `critic` (Opus, xhigh) | One critic. Domain criteria come from the brief and from skills. |
| (new) | `scope-critic` (Fable) | Second-layer review against bloat and scope creep. |
| diff-editor, small editor tasks | `quick-edit` (Haiku) | Mode 2. |
| git-expert | `git-ops` (Haiku) + `git-safety` skill | Mode 2. |
| (new) | `scout` (Haiku) | Mode 2 read-only lookups. |
| conflict-resolver | `git-safety` skill (conflict procedure), used by executor | Resolving conflicts needs judgment; Haiku git-ops escalates them. |
| python-maintainer | `python-env` skill | A procedure, not a role. |
| meeting-summarizer | `meeting-summary` skill | Merged with meeting-extraction. |
| agent-builder, agent-critic | `agent-authoring` skill, used by executor and critic | A procedure and conventions, not a role. |
| doc-writer | `writer` (prose docs) / `executor` (docs entailed by code) | Removes overlap. |
| genius, genius-worker | dropped | Mode 1 on Fable/Opus covers this; per-call model overrides cover the rest. |

### Skills (12 -> 11)

- Ported with small edits: `document-extraction`, `email-extraction`, `project-backup`
  (paths), `science-writing-style`, `presentation-style`, `writing-rules-persistence`
  (agent names).
- Merged: `meeting-extraction` + meeting-summarizer -> `meeting-summary`.
- New: `lead-loop`, `git-safety`, `python-env`, `agent-authoring`.
- Dropped: `ddgr` (WebSearch), `docx`/`pdf`/`pptx`/`xlsx` (Anthropic document skills).

### Principles carried over verbatim in spirit

- Bounded report contract: under 800 words, at most 20 paths, at most 5 excerpts under 30 lines each,
  plus diff, risks, validation, and next action.
- Supervisor context preservation: delegate reading; escalate to direct reading only when
  reports conflict or a critical ambiguity remains.
- Blocking vs. polish: iterate only on blocking findings; at most 3 rounds; report leftovers.
- Stalemate rule from the writer: the same finding in two consecutive rounds escalates to the user.
- Candid assessment first; never substitute your own objective for the user's.
- git guardrails: no force-push to main, no `reset --hard` or `--no-verify`, never amend commits
  you did not create, never commit secrets, never change author identity.
- Writing-rules precedence: hard floor > Standing Rules > Session Decisions > samples > skill defaults.

### Dropped as Argo/OpenCode-specific

`ensure-argo-provider`, `opencode-switch`, `agent-profiles.toml` and the profile tool,
`opencode.json` management, `small_model`, `temperature`/`reasoningEffort`/`mode:` frontmatter,
`~/.config/opencode` paths, and the "no native read on PDFs with Argo" rules.

## 4. Lessons from the old research notes

- `research-hub-agents-concision.md`: the load-bearing parts of hub prompts are the routing table,
  the report contract, and explicit verdict tokens. Keep explicit tokens (`PASS`/`REVISE`,
  `KEEP`/`DOWNGRADE`/`DROP`), because they make the loop machine-checkable.
- `research-skills-best-practices.md`: one skill per workflow; keep it under ~300 lines; spend
  effort on trigger descriptions; treat examples as code.
- Old critic prompts already flagged "scope creep" as a criterion, but nothing checked the critic's
  own scope creep. Critics drift toward defensive additions (extra validation, caveats, hedges,
  "for completeness" sections). `scope-critic` exists to check this.

## 5. Risks

- Cost: each Mode 1 run has at least 4 model calls per round (workers, critic, scope-critic, lead).
  Mitigation: the supervisor routes small work to Mode 2; leads skip fan-out when N=1 is natural.
- Depth: a user who sets `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` breaks Mode 1. `deploy doctor`
  checks for this.
- `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` silently disables tiering. `doctor` warns about it.
- Model aliases float to newer releases. Pinned IDs would be stable but would need edits per
  release. The pack uses aliases; pin with full IDs (`claude-opus-5-5`) if reproducibility matters.
