# Research: workflow lifecycle per task size, and the current end-of-workflow protocol

Scope: how a Supervisor for Claude workflow actually runs from opening prompt to `/clear`, per
tier (small, medium, large), and what the pack at v8.1 (HEAD 8f39071) prescribes for its end:
close-out, teardown, user-run shell steps and clearing context. Input for a planner, then a writer
producing the public `docs/workflow-lifecycle.md`. Pack text is authoritative; transcripts show
practice. Cites: `<session-prefix>:L<n>` (main transcript line), `path:L<a>-<b>` (repo path).
**[obs]** = observed in transcripts or on disk; **[inf]** = inferred.

## Summary

1. In every tier the user typed a close-out phrase, then `/clear` or a new session; what ran varied (small: teardown at most, no curator; medium/large: teardown, curator distill+archive, commit/push/deploy when authorised). The pack trigger (supervisor.md:L88-94) needs no nudge, yet the supervisor waited for one. Nothing signals that clearing is safe. **[obs]**
2. current-epic is not a program but one flat plan with revision slices in a ~19 h session (b44c0efe:L351, L670). Two programs exist: 80cdfdd8 (2 packages, one session, 80cdfdd8:L353) and the hive contrast 022d613f (11 packages, waves, one 8 h session, ~411k tokens, no compaction). **[obs]**
3. No `/compact` and no auto-compaction anywhere; 8 `/clear`s, all after a close-out or before an unrelated task. `/clear` starts a new session id, so the scratchpad path changes; old `/tmp` scratchpads stay on disk (b45c8ff5:L7). **[obs]**
4. The one real ledger teardown (current-epic) failed 4/4: the harness blocked `rm -rf`; the user was asked to delete by hand and the files are gone **[inf]**; the ledgers still say `failed:`. **[obs]**
5. No pack rule governs user-run commands, `/clear`, `/compact` or "safe to clear"; re-entry is defined only for programs (one scout plan-state call, pack/agents/supervisor.md:L79-80). **[obs]**

## Tier tables

### Small: Mode 2, or a single lead with no plan

| Step | Typical user turn (template) | Supervisor answer shape | Evidence |
|---|---|---|---|
| Open | "<task>; <constraint>; push when done" or "in a new worktree, please work on <task>" | Interim one-liner: "Waiting on <agent>." | 84954f6a:L12, b0e2d0f8:L12, bf7aa837:L13 |
| Mid-turn add-ons | Typed while agents run: "also remember <rule>", "once done commit-push-version update", "I'm going AFK, please one-shot it" | Relayed or folded in | 84954f6a:L63, L95 (queued), bf7aa837:L51 (queued) |
| Result | none, or "so we're all done?" | **Outcome**, **Who did what**, **Validation**, **Worth knowing**, **Next step**, often with an offer "say the word and I'll route it" | bf7aa837:L111, 84954f6a:L156, b0e2d0f8:L450 |
| Decision record | "yes" to an offered memory or CLAUDE.md rule | curator `record` (1 entry), git-ops `chore(memory): ...` | 484f75e2 (a2a22d5), b0e2d0f8:L294 |
| End | "deploy and close out" / "push to both upstreams", then `/clear` | "Deployed and closed out." with bullets Deploy / Residue / Close-out ("no curator pass; nothing for repo memory") | bf7aa837:L119-148, b0e2d0f8:L579 |

Small runs have no plan, so the pack runs no curator close-out. The exception is a run that left
a research artifact or a decision; a decision alone gets `record` (pack/agents/supervisor.md:L88-94).
In bf7aa837 the supervisor still briefed a fixer teardown, which returned `none` (bf7aa837:L145).
**[obs]**

### Medium: one lead cycle, a flat plan or research artifact, then curator close-out

| Step | Template | Answer shape | Evidence |
|---|---|---|---|
| Open | "<goal>; check how, then start planning" or "draft <doc>, no push yet" | Interim: "I'll bring you the plan summary" | b44c0efe:L60, 1b968aa2:L12 |
| Research gate | Answers the open questions in prose or by number | "Key finding" paragraph, "I need your input before planning" and a change map | b44c0efe:L288, L218 |
| Plan approval | Explicit AskUserQuestion approval (28cd1fe4:L166, 80cdfdd8:L283), or implicit approval by feedback ("maybe too aggressive") | Plan path, line count and critic rounds, then Approach, Decisions taken, Slices; no explicit approval question in b44c0efe | b44c0efe:L351, L383 |
| Batched questions | "all as proposed", or corrections by number | Numbered list, each with a best guess: 'reply "all as proposed" or correct the numbers' | 1b968aa2:L320, L326 |
| Review rulings | Rulings by finding id ("C1-C15 ...") | Findings relayed as ids with a recommendation | 1b968aa2:L526, L530 |
| Execution result | "fix this", "ship it", "you may push to a feature branch" | **Done**, then commits, Validation, "Who did what", "nothing pushed" | b44c0efe:L589, L962, L992 |
| Close-out offer | none | "Say 'tear down' when you want the scratch builds removed and the memory store closed out" (offered twice) | b44c0efe:L1115, L1243 |
| Close-out | "nice work, commit and push and close out" / "do the teardown and close out the work" / "finish closeout" | "Close-out complete." then **Recorded (N entries)**, **Archived**, **Not stored**, **Still yours** | 1b968aa2:L781, b44c0efe:L1431-1500, b0e2d0f8:L469 |
| End | "are we done?", then `/clear` or `/exit` | | b44c0efe:L1505, 28cd1fe4 to cb2b3ec9 |

### Large: a program (`## Work Packages`), waves, often several sessions

| Step | Template | Answer shape | Evidence |
|---|---|---|---|
| Open | Long roadmap request with constraints and autonomy level | AskUserQuestion on scope, naming and autonomy ("merge and push each feature when validated") | 022d613f:L12, L110 |
| Plan approval | One approval of the parent plan; child plans need approval only on major design decisions. Observed: AskUserQuestion plan approval plus a version-bump choice | Pack rule | pack/agents/planner.md:L52-53; 80cdfdd8:L283 |
| Waves | New facts pasted mid-flow; gate results; "Continue please" after a rate limit | Per wave: git-ops squash landing, fixer advances Status and appends Log, git-ops commits plan state | 022d613f:L560, L1187, L1358; supervisor.md:L76-93 |
| Interruption | "Continue please" | The supervisor resumed cut-off leads with SendMessage, from the plan file | 022d613f:L1177-1202 |
| Landing gate | Go/no-go to land, tag and push | AskUserQuestion | 022d613f:L2070 |
| Close-out | "any cleanup to do on <host>?", "kill the loop and remove agent leftovers" | Ad hoc cleanup with a leftover list; the user picked "All". 80cdfdd8: "please do final closeout and worktree removal" | 022d613f:L2151, L2157, L2453; 80cdfdd8:L612 |
| Hand-off | User runs the remaining host steps after the session | "Local leftovers: done. ... not resolved, handed to you ... ready to paste" | 022d613f:L2552 |

Resume across sessions: the pack rule is one `scout` plan-state call, and the supervisor never
reads the plan itself (supervisor.md:L79-80). The scout returns at most 30 lines covering package
Status, Deps, Artifacts, open Todo, the last 5 Log lines and goal summaries
(pack/agents/scout.md:L21-22, L32). **No multi-session program resume appears in the corpus**:
022d613f ran in one session, and b44c0efe stayed live through a 9-hour gap without re-reading
anything. **[obs]** The 8 `/clear`s all came after a close-out or before an unrelated task
(484f75e2:L7, fe60c73a:L8, 12387cd0:L7, bf7aa837:L7, b45c8ff5:L7, 28cd1fe4:L9, 343444d0:L7,
cb2b3ec9:L7). After a `/clear` with a terse follow-up, the supervisor had to hunt for the repo
(12387cd0:L37). **[obs]**

## Close-out and teardown

### Current protocol (pack)

- **Trigger.** Close-out runs when every package is `done`, a flat plan's `## Todo` is complete, or a
  plan-less run's last change set has landed, if it left a research artifact or a decision; teardown
  runs first (pack/agents/supervisor.md:L88-94).
- **Curator steps.** Distill into at most 5 new entries; supersede or retire; archive met goals;
  re-verify stale entries; trim the roadmap and append `history.md`; `git mv` plan and research to
  `archive/working/`. Overflow reports `follow-up: curator close-out <plan>`; the report ends
  `recorded N` (pack/skills/project-memory/references/curator-procedures.md:L3-12, L17-61; pack/agents/curator.md:L42-47).
- **Commits.** curator and fixer only stage; git-ops commits `chore(memory): ...`, per wave in a
  program (supervisor.md:L95-96). A local store is never staged; a plan branch lands only after
  close-out on the branch (project-memory/SKILL.md:L45-56; repo-workflow/SKILL.md:L84-86, L106-107).
- **Teardown.** The supervisor briefs fixer `teardown [done: <ids>]` after each wave for done
  packages, and when a plan or plan-less run ends, before close-out (supervisor.md:L85-89). Each
  entry: run `remove`, then `check`; failure appends `failed: <date> <reason>`; `sudo`, `/`, `~`,
  `$HOME` targets are refused; report `residue: removed N, failed M` (pack/skills/residue/SKILL.md:L43-58;
  pack/agents/fixer.md:L24).
- **Ledger.** `.supervisor/working/residue/<agent>-<id>.md` in the main checkout, git-excluded, never
  archived (residue/SKILL.md:L21-28).

### Practice

- **Close-out counts.** b44c0efe: 5 entries (4 decisions, 1 fact), plan and research archived by
  plain `mv` (local store), sections **Not stored** and **Still yours** (L1500). 1b968aa2: `recorded 5`
  (3 new, 2 superseded). 80cdfdd8: 4 decisions, 1 superseded, roadmap trimmed, 2 lesson proposals
  relayed; the user's "keep" stored one, the other became a roadmap task (L455, L479, L502). No
  `follow-up:` line in any session. **[obs]**
- **Commit wrinkles.** 1b968aa2's close-out commit missed two rename deletions (fix-up 6fd21b8 then
  3043f9d); in 84954f6a an executor's plain `git commit` swept a staged memory rename into a docs
  commit (0fc63d4). **[obs]**
- **Ledger teardown (only real run).** b44c0efe:L1450 briefed teardown; the result was `removed 0,
  failed 4`. The reason, as written in the ledgers, was "removal blocked by built-in safety check
  before running". The 4 ledgers held about 24.6 GB of scratch builds and container images, and
  their `remove` lines contain unexpanded `$(ls -d ...)` globs
  (`<epic>/.supervisor/working/residue/*.md`, line 3). The supervisor asked the user to run the
  `rm -rf` (L1475, repeated at L1500 and L1510). On disk now, the scratchpad is down to 100K (no
  `sup-*` left) and all 4 ledgers still carry `failed:` **[obs]**. Inferred: the user ran the
  deletion, and nobody re-ran `teardown retry` afterwards. **[inf]**
- **Teardown before the ledger.** Sessions before v7.24 (5ca37940, 1b968aa2, 484f75e2 and the
  hive) had no ledger. Worktrees were removed by the landing executor or by git-ops. Hive cleanup
  (93 stale tmux sockets, a test profile, config entries) was ad hoc and only on user prompting
  (022d613f:L2089, L2151). **[obs]**
- **Scratch left in place.** Critic scratch (briefs and diffs) stays in the session scratchpad,
  sometimes with "say if they should go" (bf7aa837 subagent afe74:L78). Non-ledgered files stayed in
  b44c0efe's scratchpad (ci.sh, body.md, calibrations/). **[obs]**

## User-run shell steps

The pack has no rule on how to present a command the user must run. Related rules: the
supervisor has no Bash (supervisor.md:L5); outward actions need confirmation unless already
authorised (supervisor.md:L114-115); `project-backup` is user-invoked only
(pack/skills/project-backup/SKILL.md:L4-6). Observed cases:

| Case | Phrasing and placement | Evidence |
|---|---|---|
| `./deploy install` after a pack edit | `**Next step**: run ./deploy install ...`; the user later typed "deploy and close out" and a fixer ran it | bf7aa837:L111, L119 |
| Deploy across profiles | `deploy update` touched only the default profile; "update those separately" | b0e2d0f8:L563, 28cd1fe4:L327 |
| Teardown blocked by harness | "That's a permission that has to come from you ... run it yourself", with a shell block, repeated in **Still yours** and **Left for you** | b44c0efe:L1475, L1500, L1510 |
| Write blocked in a forked session | `cp` line in a code block inside a long answer; the user ran it later | f2bc4449:L679, b44c0efe:L1415 |
| Manual UI step | Bold **For you:** line: drag the figures into the PR | b44c0efe:L1243 |
| External account setup | "This step is yours, not an agent's", in section 1 of a multi-section answer | b4875d50:L44 |
| Remote host action denied by harness | Procedure handed over "ready to paste on <host>" | 022d613f:L2535, L2552 |

Push was authorised in three ways: in the opening prompt, as a mid-turn queued message ("Push when
done", 84954f6a:L173), or by answering "Want me to push origin then public?" (484f75e2:L134).
Agents always ran the push; the user never did. **[obs]**

## No-memory case (one-off directory)

- **Detection.** Walk up from the cwd, stopping at the git toplevel and never at `$HOME` or above;
  outside git, `.supervisor/`, `.claude/`, `CLAUDE.md` or `AGENTS.md` marks a project
  (pack/skills/project-memory/SKILL.md:L94-103).
- **Behaviour.** Nothing is persisted or asked. A would-be store write reports exactly
  `not stored: no project store here; say *remember* to keep it`, relayed once and never asked
  about (SKILL.md:L105-108; supervisor.md:L93-94). curator `record`/`migrate` write nothing; the
  writer keeps decisions in the run (curator.md:L28-29; pack/agents/writer.md:L66).
- **Ledger.** None: agents remove everything before reporting and list what failed
  (residue/SKILL.md:L40-41), so a failed removal appears only in that one report. **[inf]**
- **Becoming a project.** "remember ...", "make this a project" or a close-out creates the store in
  the cwd (SKILL.md:L108-111). Since v8.1, inside git the supervisor first asks once: tracked or
  local (supervisor.md:L97-100); before, it created a tracked store silently.
- **What survives.** Only the user's files, git, and Claude Code's transcripts and `/tmp`
  scratchpads; with no plan file, nothing pack-level is recoverable after `/clear`. **[inf]**
- **Transcripts.** Nearest example 5ca37940 (writer task, nothing stored, no close-out). No
  observed true one-off `not stored:` line. **[obs]**

## Clear and compact

**Survives a `/clear` or new session** (on disk): the store, `.supervisor/working/` plans and
research, residue ledgers, worktrees (`.claude/worktrees/<slug>`), branches, git history. Plans hold run state "in this or a later session" (docs/architecture.md:L66; repo-workflow/SKILL.md:L67-68).

**What does not survive:**

- **Conversation context.** That includes a lead's report the fixer has not yet appended to the
  plan Log, unrelayed `not stored:` or lesson proposals, and the user's batched answers not yet
  logged as `decision:` lines (plan-writing/SKILL.md:L31-37). **[inf]**
- **The session scratchpad as a working location.** `/clear` creates a new session id
  (b45c8ff5:L7), so later agents write to a new scratchpad. The old files stay in `/tmp` until the
  OS removes them, so anything kept past a step must be in the ledger. **[obs]**
- **In-flight background agents.** No pack rule; behaviour across `/clear` is unverified in the
  corpus. In 12387cd0 the executor's report still arrived after `/exit` (L85, L87). **[inf]**

**`/compact` vs `/clear`.** `/compact` summarises the conversation in the same session and re-attaches
invoked skills, within a 5k-token budget per skill and 25k in total (https://code.claude.com/docs/en/slash-commands). `/clear` empties the conversation. **[inf]** Its behaviour is not
documented on the fetched page, but the observed new session id is consistent with it. The pack
does no compaction of its own (docs/context-engineering.md:L18). That doc also cites advice to reset
a context near 200-300k tokens (L18). Observed
peak context (from assistant usage fields): ~411k tokens in 022d613f (L2552), with no compaction. **[obs]**

**Cheapest clear points, in order** **[inf]**, reasoned from the re-entry rule above:

1. After curator close-out and its commit. All state is on disk or archived.
2. In a program, after a wave is fully booked: the fixer has appended the Log and advanced Status,
   teardown for done packages has run, git-ops has committed the plan state, and no package is
   `blocked:` waiting on an answer. The next session needs only the scout plan-state call.
3. After plan approval, once the plan is written to disk. For a flat plan there is no pack re-entry
   rule (the scout rule is for programs), so the user's next prompt must name the plan path.
   **[inf]**

**Unsafe points:** mid-wave; between a lead's report and the fixer's Log append; while a question
batch is pending; before a `not stored:` or lesson proposal is answered.

## Friction worth fixing (one line each)

1. **No safe-to-clear signal.** Close-out answers should end with an explicit line such as "safe to
   /clear; resume with <prompt>".
2. **Close-out needs a typed nudge every time** (b0e2d0f8:L469, 80cdfdd8:L612, b44c0efe:L1431),
   even after the supervisor offers it, although the pack trigger (supervisor.md:L88-94) needs none.
   Document a canonical close-out prompt.
3. **User shell steps vary in form and placement** (table above). Use one fixed "You run" block.
4. **Harness-blocked teardown.** The failure reason is not actionable, and after the user's manual
   `rm` the ledgers stay `failed:` (epic ledgers). Document `teardown retry` after manual removal.
5. **No re-entry rule for a flat plan after `/clear`.** A terse follow-up made the supervisor hunt
   for the repo (12387cd0:L37).
6. **Lesson proposals can arrive after the close-out has committed** (80cdfdd8:L479-509), which needs
   a second curator round.
7. **Non-ledgered scratch stays in old scratchpads** (critic briefs and diffs, b44c0efe extras),
   and no one removes it.

## Slash commands in the pack

The pack ships only `agents/` and `skills/`, no `commands/`; `deploy` installs `agents/*.md` and
`skills/*` (deploy:L372-440). User-only skills already ship via
`disable-model-invocation: true` (`project-backup`, `supervisor-config`); protocol skills are hidden
with `user-invocable: false` (pack/skills/agent-authoring/SKILL.md:L60-61). So lifecycle prompts
could ship as `disable-model-invocation` skills with no deploy change. **[inf]**

## Coverage gaps

- Hive subagent transcripts were sampled only through their dispatch and hand-back text.
- No true one-off directory session was in the corpus.
## Sources

| Session (profile) | Lines | Date (UTC) | Tier |
|---|---|---|---|
| b44c0efe-090f (max, current-epic) | 1520 | 10-28 01:49-20:42 | medium-plus (flat plan, revisions, close-out) |
| f2bc4449-be8a (max, current-epic) | 702 | 10-28 | fork of b44c0efe; diverges at L519 |
| b45c8ff5-4100 (max, current-epic) | 316 | 10-28 17:47-17:59 | small; opens with `/clear` |
| b4875d50-7df1 (max, current-epic) | 59 | 10-28 | Q&A only |
| bf7aa837-cb91 (default) | 155 | 10-28 17:17-20:41 | small (v8.1 work) |
| 12387cd0-66cd (default) | 96 | 10-28 | small, interrupted |
| 84954f6a-2314 (default) | 257 | 10-27 23:32-23:47 | small |
| 484f75e2-8745 (default) | 354 | 10-26/27 | small (v7.22 work) |
| 1b968aa2-f40e (default) | 859 | 10-26 17:48-23:52 | medium (research, writer, close-out) |
| 5ca37940-c3ce (default) | 194 | 10-26 | small, nothing stored |
| 80cdfdd8-c759 (max) | 648 | 10-27 21:26-23:18 | large (2-package program, v8.0) |
| b0e2d0f8-96d4 (max) | 595 | 10-27 21:33-22:03 | small (v7.23) |
| 28cd1fe4-b4f8 (max) | 339 | 10-27 22:03-23:02 | medium (flat plan, v7.24) |
| 022d613f-8d89 (default, hive) | 2557 | 10-27 14:52-22:51 | large program, contrast |

Stubs (`/clear`, `/exit` or empty only): ce18d372 (7), 36116c44 (9), fe60c73a (11), 983ed179 (9),
343444d0 (10), cb2b3ec9 (10), 7243eb4d (7, bot); 666feee9 (35, bot) was abandoned and re-run as
80cdfdd8. Excluded: 4bc6b0b5 (live session). The pack was read at HEAD 8f39071.
