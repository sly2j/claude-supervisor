# Research: supervisor.md word budget audit (back to 1000 words?)

Scope: a line-by-line audit of `pack/agents/supervisor.md` for words that can go because they are
redundant, spurious, movable or compressible. It also checks cross-prompt duplications and
contradictions among the other agents and skills, and proposes a path to at most 1000 body words.
This is a report only: no file under `pack/`, `docs/`, `tests/` or `VERSION` is edited.

## 1. How the budget is measured (verified)

- Lint: `tests/test_pack_lint.py:22-24` sets `BODY_WORD_CAPS = {"Main": 1040, ...}`.
  `test_agent_body_word_cap` (`:128-134`) gets the tier from the Tiers table in
  `pack/skills/agent-authoring/SKILL.md:10-21`.
- Counting: `body_words()` (`:84-91`) counts the text after the closing `---` of the frontmatter,
  as `len(text.split())`. Headings, table pipes and `|---|` separators each count as words.
- **Current: supervisor.md = 1039 / 1040.** The agent-authoring budget line
  (`agent-authoring/SKILL.md:43`) also says "main 1040". A cap change has to edit both places.
- Cap history: 1000 from `a58849f` to v6.0. Raised to 1030 in `59b920a` (v6.5, writer-on-Opus
  line, +29 words), then to 1040 in `42b57ca` (v7.0, Codex ad-hoc review line, +10 words).
  Earlier features (programs, confined worktree, curator, conflict triage) were absorbed under
  1000 by rewording (`682263d`, `4576a93`, `ce88d2d`).
- Binding memory entry:
  `.supervisor/memory/decisions/2026-10-24-raise-a-pack-word-cap-only-on-the-owner.md` says
  "Existing rules are not trimmed to make room for a rule the owner asked for." Lowering the cap
  back to 1000 by trimming is an explicit owner request, so it reverses that rationale. If the
  owner goes ahead, `curator` should supersede that entry.

Per-section body words: intro 22, Modes 170, Routing Judgment 302, Delegation Brief 124,
Programs 236, Context Preservation 56, User Interaction 81, Final Output 29.

### Other files near or over budget (same counting method)

| File | Words / cap | % |
|---|---|---|
| supervisor | 1039 / 1040 | 100% |
| git-ops | 350 / 350 | 100% |
| curator | 399 / 400 | 100% |
| lead-loop SKILL | 1371 / 1380 | 99% |
| clerk | 335 / 350 | 96% |
| critic | 569 / 600 | 95% |
| repo-workflow SKILL | 1298 / 1380 | 94% |
| project-memory SKILL | 1293 / 1380 | 94% |
| writer-worker | 349 / 400 | 87% |

Everything else is at 77% or below (researcher 222/700, scout 179/350, planner-worker 198/400).

## 2. What the supervisor actually reads (this decides REDUNDANT)

- `supervisor.md` has no `skills:` field (lines 1-7). The supervisor runs as the main thread
  through `settings.json` `"agent": "supervisor"` (`deploy:598`). It preloads no skill.
  `lead-loop`, `project-memory`, `git-safety`, `repo-workflow` and `plan-writing` reach it
  only if it loads them on demand.
- It does see every agent's frontmatter `description` in the Agent tool's agent listing. That is
  Claude Code built-in behaviour, and the listing shown in this session matches the pack
  descriptions verbatim. The Agent tool text it sees also says "When you launch multiple agents
  for independent work, send them in a single message".
- So a line is REDUNDANT only if it repeats an agent description or built-in tool guidance, or
  if it describes what another agent does on its own and the supervisor's routing or briefing
  would not change without it. "The lead already knows X" is not enough when the supervisor has
  to put X into the brief.

## 3. Line-by-line audit of supervisor.md

Savings are measured with `body_words` on a simulated copy, available at
`/tmp/claude-1002/-home-sjoosten-projects-claude-supervisor/7a436f1c-13d8-4a67-a649-f584d83bf33f/scratchpad/cuts.py`.

| Lines | Text (short) | Tag | Saving | Evidence / proposal |
|---|---|---|---|---|
| 9-10 | intro "...coordinator of a two-mode agent system..." | COMPRESSIBLE | 5 | Drop "of a two-mode agent system"; `## Modes` defines it. `agent-authoring:41` needs only "You are ...". |
| 14-15 | "Dispatch one lead, which runs `lead-loop` until the contract is met, or one round under `Path: minimal`." | COMPRESSIBLE | 11 | → "Dispatch one lead; it runs `lead-loop`." The supervisor does not run the loop. Loop length is defined in `lead-loop/SKILL.md:110-111,116-118`. "One round" also misstates `Path: minimal`, which means `Review: light` and iterates on BLOCKING findings (`lead-loop:119-125`). |
| 17-22 | Mode 1 lead table | REDUNDANT (decision) | see C11 | Each row restates the lead's description (`researcher.md:3`, `planner.md:3`, `executor.md:3`, `writer.md:3`), which the supervisor sees in the agent listing. Only two things are unique: the writer/executor documentation boundary ("project docs that are not entailed by a code change", against `executor.md:24`, which the supervisor does not read), and "code tracing, literature/web" for researcher. |
| 24 | "Mode 2: quick tier (Haiku)... No critic loop." | KEEP | 0 | Mode semantics are stated only here. |
| 26-30 | Mode 2 specialist table | REDUNDANT (decision) | see C11 | The `clerk` row is close to verbatim with `clerk.md:3`, the `git-ops` row with `git-ops.md:3`, and the `scout` row with `scout.md:3`. |
| 34-35 | explicit user choice wins | KEEP | 0 | Sole routing override. |
| 36-37 | Mode 2 four conditions | KEEP | 0 | Core routing rule. |
| 38-39 | `Path: minimal` when... | KEEP | 0 | Sole definition of when to route minimal (v6.0). `lead-loop:123-125` defines what it does, not when to choose it. |
| 40-41 | answer directly | KEEP | 0 | |
| 42-43 | `ESCALATE` → Mode 1 | KEEP | 0 | Three agents escalate (`clerk.md:36-44`, `git-ops.md:30-37`, `scout.md:25-28`), and only this line says what the supervisor does with an escalation. |
| 44 | "`git-ops` escalates a conflict as a block (operation, branches, per-file hunks, mechanical flag). Triage:" | COMPRESSIBLE | 9 | → "Triage a `git-ops` conflict block:". The supervisor receives the block itself; its fields are defined in `git-ops.md:41-50`. |
| 45-49 | easy → `executor` light; hard → chain | KEEP | 0 | Sole triage rule. `conflict-resolution.md` is the executor's side. |
| 50-51 | when to set `Review: light/full/none` | KEEP | 0 | The supervisor's choice. `lead-loop` defines the levels, not when to pick each. |
| 52-53 | writer on Fable; `model: opus` for short prose | KEEP | 0 | Recent (v6.5). `agent-authoring:23-25` has it, but the supervisor does not load that skill. |
| 54-55 | lead chain and skip rule | KEEP | 0 | |
| 56-58 | Ad-hoc review via clerk/codex-critic | KEEP (minor COMPRESSIBLE, 3) | 0-3 | Recent (v7.0). `clerk.md:23-28` holds the mechanics (probe, timeout, verbatim output), and the supervisor still has to know to brief clerk and then fall back to `critic`. A 3-word squeeze is possible but not worth churn. |
| 59 | "Dispatch independent work in one parallel message." | REDUNDANT | 8 | Built-in Agent tool guidance says the same ("send them in a single message with multiple tool uses"). Low risk. |
| 60 | no built-in agents unless asked | KEEP | 0 | The supervisor sees those agents in its listing. `lead-loop:42` binds leads only. |
| 64-69 | request verbatim, contract, inputs/outputs | KEEP | 0-1 | `lead-loop:9-15` turns the brief into the contract, so the brief must carry it. |
| 70-71 | "`Review: full \| light \| none` (default `full`) and, if routed, `Path: minimal`, as `lead-loop` defines them." | COMPRESSIBLE | 11 | → "`Review:` and, if routed, `Path: minimal`." Values are at lines 50-51, the default is at `lead-loop:118`, and minimal is at line 38. |
| 72-73 | attribution: only the git-safety trailer; no model trailers... | KEEP | 0 | Sole guard. `git-safety/SKILL.md:44` says "Add other trailers only when your brief supplies them, exactly as given", so a forwarded harness trailer in a brief would be obeyed. |
| 74-75 | confined worktree token | KEEP | 0 | Sole place the supervisor learns to emit `Confined to worktree: <path>; push to <default> authorized`. The consumer is `repo-workflow/references/landing-from-worktree.md:14`. |
| 77 | Mode 2 brief shape | KEEP | 0 | |
| 81 | program definition | KEEP | 0 | |
| 82-83 | "...one `scout` call on resume or project start, which also returns the `## Log` tail and active goals; never read the plan." | REDUNDANT (partial) | 9 | `scout.md:21-23` already returns the Log tail and goals' `summary:` lines whenever it is asked for plan state. → "...or, on resume or project start, one `scout` plan-state call; never read the plan." |
| 84-85 | wave rule | KEEP | 0 | Sole scheduler rule (memory: supervisor-runs-packages-in-waves). |
| 86 | package brief | KEEP | 0 | Researcher and writer do not load `plan-writing`, so the "block and Scope Notes bind" rule must reach them in the brief. |
| 87-89 | clerk bookkeeping (Status, Amend parent, Log, decision lines) | KEEP (not MOVABLE) | 0 | Checked: `clerk.md` carries only "Write `## Log` lines exactly as briefed" (`:22`), and nothing about `Status`, `Amend parent:` or `decision:`. `curator.md`, `planner.md` and `project-memory` carry none of it either. `plan-writing:31-35,69` has the formats, but the supervisor does not load it. Moving the procedure into `clerk` (15 words free) would not remove the supervisor's need to trigger and brief it. Haiku clerk works from exact briefs. |
| 90 | `blocked:` and re-run | KEEP | 0 | Sole trigger. Schema is at `plan-writing:69`. |
| 91-92 | curator close-out trigger | KEEP | 0 | Sole definition of when close-out runs. It is not in `planner`, `plan-writing` or `curator.md`, whose Scope lists only the brief form. |
| 92-94 | "It also handles a single-stage run's user decision and 'remember X', 'forget X' or 'make this a project', briefed with the user's words verbatim and no kind (a bare reply ...)" | REDUNDANT + COMPRESSIBLE | 18 | The task list repeats `curator.md:3` (description: "to record a user decision from a single-stage run, to handle 'remember X', 'forget X' and 'make this a project'"). "no kind" is moot: `curator-procedures.md:97` says "a kind named in the brief does not bind". → "Brief its other tasks with the user's words verbatim (a bare reply to a `not stored:` line quotes the unstored items)." |
| 94-95 | relay `not stored:` once; never ask | KEEP | 0 | `project-memory/SKILL.md:101` says "The supervisor relays it once", but the supervisor does not load that skill, so supervisor.md is the operative copy. See X7. |
| 96-97 | curator/clerk never commit → brief git-ops | KEEP | 0 | Both agents say they never commit (`curator.md:37`, `clerk.md:32-33`). The supervisor still needs the follow-up dispatch and the commit-message form. |
| 98-99 | `make this a project` before the first store-writing stage | KEEP | 0 | Sole trigger. "(idempotent)" matches `curator-procedures.md:107-108` and tells the supervisor it need not check first. |
| 103-105 | context preservation | COMPRESSIBLE | 4 | Drop "Repository context is expensive:"; the imperative that follows carries the rule. |
| 106 | write only memory files | KEEP | 0 | `agent-authoring:12` says it, but the supervisor does not load that skill. |
| 110-116 | user interaction | KEEP | 0 | No duplicates found. |
| 120-121 | final output | KEEP | 0 | |

SPURIOUS/OBSOLETE: none found. Every name and token the supervisor uses exists: `Path: minimal`,
`Review:`, `ESCALATE`, `VERDICT:`, `review --round`, `Amend parent:`, `blocked:`,
`not stored:`, `Confined to worktree:`, `make this a project`, `chore(memory):`. Each was checked
by grep in `pack/`. The only inaccuracy is the "one round under `Path: minimal`" clause at
lines 14-15, which C3 removes.

## 4. Path to at most 1000 words (ranked, safest first)

Simulated with `body_words` (scratch `cuts.py`); cumulative counts start at 1039.

| # | Cut | Tag | Saving | Cumulative | Behaviour change? |
|---|---|---|---|---|---|
| C1 | scout plan-state clause (82-83) | REDUNDANT | 9 | 1030 | No |
| C2 | curator duty list and "no kind" (92-94) | REDUNDANT | 18 | 1012 | No: triggers live in `curator.md:3`, which the supervisor sees |
| C3 | Mode 1 loop clause (14-15) | COMPRESSIBLE | 11 | 1001 | No (removes a slight misstatement) |
| C4 | Review/Path brief bullet (70-71) | COMPRESSIBLE | 11 | **990** | No |
| C5 | conflict block field list (44) | COMPRESSIBLE | 9 | 981 | No |
| C6 | "Dispatch independent work in one parallel message." (59) | REDUNDANT (built-in) | 8 | 973 | Very low risk; relies on Claude Code's Agent tool text |
| C7 | intro "of a two-mode agent system" | COMPRESSIBLE | 5 | 968 | No |
| C8 | "Repository context is expensive:" | COMPRESSIBLE | 4 | 964 | Faint loss of the rationale |
| C11 | replace both Mode tables with two lines and "Agent descriptions say what each owns" | REDUNDANT, **user decision** | 114 | 850 | Possibly: routing then rests on the frontmatter descriptions |

Proposed C11 text. It keeps the documentation boundary. It drops "code tracing, literature/web", which `researcher.md:3` ("investigates") covers only implicitly. After C11, the choice between `researcher` for literature research and `scout` for a "quick web fact" rests on the descriptions alone.

```
**Mode 1: full harness.** Dispatch one lead: `researcher`, `planner`, `executor` (also
documentation a code change entails), or `writer` (other prose); it runs `lead-loop`.

**Mode 2: quick tier (Haiku).** Dispatch one specialist directly: `clerk`, `git-ops`, or `scout`.
No critic loop. Agent descriptions say what each owns.
```

**Strictly lossless floor: 981 words (C1-C5); 964 with the low-risk C6-C8.** Getting to 1000 or below
needs no behavioural change. C1-C4 alone give 990, which leaves 10 words of headroom.

Where cutting starts to cost something: past C8, the only large reservoir is the Mode tables
(C11). That cut is defensible because the descriptions duplicate the tables almost word for word.
It is a design choice, though, not just wording: the agent-authoring guidance (`:44-45`) names
"routing tables" as a legitimate use of the budget. Everything else is KEEP: Programs
bookkeeping, triggers, the confinement token, attribution, conflict triage, the writer model
override and the Codex ad-hoc review are each defined only in supervisor.md for this reader.

Moving the Programs section into a skill the supervisor loads on demand was considered and not
recommended. `plan-writing` has room (795/1380), but it is marked "Not for direct use", and an
on-demand load is less reliable than the always-present body for wave scheduling.

## 5. Cross-prompt redundancy and contradictions

Verified by me against file text: X1-X4, X7 and X8. The rest come from worker reports, with
paths and lines spot-checked.

Contradictions or tensions:
- X1. **`writer.md:54-56` vs `lead-loop/SKILL.md:112-114` (stalemate).** lead-loop says the lead
  "decide[s] it yourself"; writer stops and offers the user four options. The writer behaviour
  looks intentional (prose voice belongs to the user), but it is not marked as an override.
  `writer.md:48` ("Iterate on BLOCKING findings only") also departs from `lead-loop:110` (apply
  kept SHOULD and NIT findings). Suggest marking both as overrides.
- X2. **`git-ops.md:33-35`** grants the gated-operation exception when the brief "names its target
  as this session's commit". `git-safety` allows only a narrow amend or reset of an unpushed
  session commit by SHA. The `git-ops` wording is broader; worth tightening. (Worker finding; not
  re-read in full.)
- X4. **`critic.md:51`** cites "`writing.md`'s leadless procedure"; "leadless" occurs nowhere else
  in `pack/`. The procedure exists as "A critic with no lead ..." at
  `project-memory/references/writing.md:47`. Rename to match.

Removable duplicates (the reader loads the other file):
- X5. **`git-ops.md` (at cap) vs `repo-workflow`**, which git-ops preloads:
  - the fetch and `pull --rebase --autostash` sequence (`git-ops.md:19-20` vs
    `repo-workflow:86-91`)
  - push order and origin-first (`git-ops.md:24-25` vs `repo-workflow:92`)
  - VERSION self-bump (`git-ops.md:27-28` vs `repo-workflow:51-52`)
  - attribution (`git-ops.md:26` vs `git-safety:39-44`)
  These free about 50-60 words in git-ops if replaced by pointers.
- X6. **`curator.md` (at cap) vs `project-memory`** and its `curator-procedures.md`, both of which
  curator loads:
  - five-entry cap (`curator.md:32-33` vs `curator-procedures.md:4-5`)
  - repoint `source:` (`:35-36` vs procedures `:9-10`)
  - the procedure list (`:44-50`), which restates the procedures headings and the Scope brief list
  About 40-60 words are recoverable.
- X7. `project-memory/SKILL.md:101` "The supervisor relays it once." The supervisor does not load
  the skill, so this sentence instructs nobody. It is harmless documentation (5 words); the
  operative rule is `supervisor.md:94-95`.
- X8. `planner.md:59` "An explicit round cap from the caller still applies" repeats
  `lead-loop:116-117`, which planner preloads (about 9 words).
- X9. Lead Fan-Out restatements of `lead-loop:32-34` ("single unit yourself; two or more to
  workers"): `researcher.md:29`, `executor.md:46-47`, and part of `planner.md:28-30`. Keep the
  `subagent_type` literals, which `test_leads_name_worker_subagent_type` lints.
- X10. `writer.md:36-37` "mark gaps [TODO]" and "match the author samples" repeat the style skill
  the writer loads before drafting (about 15 words).

Needed duplicates (the reader does not load the other file); keep:
- `critic.md` round-2 delta inputs vs `lead-loop:77-81`
- `scope-critic` inputs vs `lead-loop:70-72`
- the shared worker report shapes in `researcher-worker`/`planner-worker`
- `scout.md:21-23` plan-state fields
- `clerk.md:32-34` VERSION clause (clerk does not load `repo-workflow`)
- the `git-ops` conflict block

Rejected worker claim: that `project-memory:135-136` ("`clerk` and `git-ops` never read it")
contradicts clerk preloading `project-memory`. "It" there is the memory store
(retrieval), not the skill, so there is no contradiction.

lead-loop (1371/1380) has its own small reservoir: the dispatch whitelist at `:41-42` overlaps
with `:39-40`, and the "once you fan out" rule at `:43-44` overlaps with `:32`. Before cutting the
whitelist, check that no test lints it.

## 6. How to move forward

1. Apply C1-C5. That gives 981 words with no behaviour change, then set the Main cap back to 1000
   in `tests/test_pack_lint.py:23` and `agent-authoring/SKILL.md:43`
   (`docs/architecture.md` does not state the cap; checked by grep). The remaining 19 words are
   headroom for the next feature. Add C6-C8 for 964 if more headroom is wanted.
2. Decide C11 separately. It is the only cut that buys real room (about 114 words), at the cost of
   leaning on agent descriptions for routing detail.
3. Have `curator` supersede the "never trim rules to fit" entry with the new owner rule.
4. Optionally, in the same change set, fix X1, X2 and X4, and reclaim the at-cap budgets in
   `git-ops` (X5) and `curator` (X6) the same way.
