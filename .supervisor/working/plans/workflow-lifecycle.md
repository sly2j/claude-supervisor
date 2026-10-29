# Plan: workflow lifecycle doc, lifecycle prompts and the close-out state line (v9.0)

## Goal

Document the life of a Supervisor for Claude workflow per task size (small, medium, large) in a
new `docs/workflow-lifecycle.md`, linked from README, and make the pack behave the way the doc
promises: every close-out and every fully booked wave ends with a `Session state:` line that
says whether `/clear` is safe and how to resume; steps only the user can run appear in one fixed
`Run yourself:` block; two lifecycle prompts ship as user-invoked skills (`/close-out`,
`/pick-up`); flat plans get the resume rule programs have; a harness-blocked teardown is
actionable (the failed `remove` command is reported, `teardown retry` is documented). The new
`supervisor.md` rules fit under the unchanged 1000-word cap through the trims in D9, which move
routing scope from the supervisor's tables into the agent descriptions; two tests guard that
move (D13, D14). The change set is major: v9.0 (D12).

Non-goals: the close-out trigger itself (`pack/agents/supervisor.md:88-94`), residue mechanics
beyond the report line, scratchpad cleanup, lesson proposals that arrive after close-out, program
logs for flat plans (roadmap item 3), and anything in the externalize-memory change set
(`.supervisor/working/plans/externalize-memory.md`).

Expected change size: about 480 lines. `docs/workflow-lifecycle.md` about 170 (new); two
skills about 30 each; `supervisor.md` about 45 lines changed (rules plus trims); `researcher.md`
and `executor.md` 1 each; `residue` 2; `tests/test_pack_lint.py` about 30;
`tests/test_live_routing.py` about 120 (new); `docs/deploy.md` about 15; `CLAUDE.md` 1; README
about 15; `docs/architecture.md` about 6; `docs/context-engineering.md` 1; `CHANGELOG.md` 1 and
`VERSION` 1 in the squash commit only.

## Approach

Input: `.supervisor/working/research/workflow-lifecycle.md` (tier tables, protocol vs practice,
user-run steps, no-memory case, clear/compact ranking, friction list, slash-command finding).

The doc describes one lifecycle (open, mid-course, approval or questions, close-out, clear,
resume) and shows how each tier walks it, with the prompt the user types and the answer shape the
supervisor gives at each step. The pack changes are the minimum that makes the doc true: rules
in `supervisor.md` (the only copy of its output rules, since it preloads no skill:
`.supervisor/memory/facts/2026-10-25-supervisor-preloads-no-skills-so.md`), one actionable
failure line in `residue`, and the two prompts that every observed flow needed and phrased
differently, shipped as skills. The rest stays prose in the doc. Routing safety: a static test
pins every scope phrase the dropped tables carried to an agent description (free, always on),
and an env-gated live test asks the deployed supervisor for its routing decision on canonical
requests (costs money, owner's go).

Rejected: a single `/lifecycle <verb>` skill (a verb mini-language); `/session-state`, "open" and
`/tear-down` skills (a plain question gets the line, the task is the prompt, teardown is a step
of `/close-out`); a state line after plan approval (its residue and store clauses are empty
there; the doc names it as a cheap clear point); a `lead-loop` field and a `scout` edit (leads
already report user questions and next actions; `scout.md:21-23` already returns unticked
`## Todo` and last Log lines); a lint test for the new literals (no observed failure); a cap
raise (D9); a `writer` stage for the doc (entailed by the pack change; `executor` writes it);
`claude plugin eval` for the live test (it needs a plugin manifest and runs cases against a
plugin, not a config dir with an `agent` setting, per the plugin-evals docs); `--max-turns 1`
(a tool call then exits with an error) and `--bare` (skips agent and skill discovery) in the
live test.

## Decisions

- D1 Tiers as the user fixed them: small = Mode 2 or a single lead with no plan; medium = one
  lead cycle with a flat plan or a research artifact, closed out by `curator` after one
  teardown; large = a program across waves and possibly sessions. The doc's tier table says per
  tier what runs, what sits on disk meanwhile, and what close-out does.
- D2 `Session state:` line, exact form, printed as the last line after (a) a close-out and (b) a
  wave whose bookkeeping is done (fixer Log and Status, teardown of done packages, git-ops
  commit, no package `blocked:` on an answer):
  `Session state: <closed out | wave N booked>; residue <removed | N failed>; store <committed | uncommitted | not stored>; safe to /clear, resume with "<prompt>"`,
  or `Session state: <state>; not safe to /clear: <why>`. The `store` clause reports what
  `git-ops` or `curator` reported, so an externalized store committed in another repo
  (externalize-memory D11) reads `committed` with no change here. The resume prompt is
  `/pick-up <plan path>` when a plan is live, else the next task.
- D3 `Run yourself:` block: when any step can only be run by the user (a push the user did not
  authorize, a removal the harness blocked, a deploy of another profile, an account or UI step),
  the supervisor ends the answer with one block headed `Run yourself:`, shell commands verbatim
  in a fenced block, manual steps one line each, never asked for in prose elsewhere. `fixer`'s
  teardown report names the failed entry's `remove` command (D8), so the supervisor copies
  commands rather than reconstructing them.
- D4 Skills shipped (frontmatter `disable-model-invocation: true`, no `context: fork`, since the
  body must run in the supervisor's own context where it dispatches agents; `argument-hint`;
  `$ARGUMENTS`): `/close-out [retry]` and `/pick-up [<plan path>]`. Reasons: close-out needed a
  typed nudge in every observed flow, in three phrasings, and the state line and teardown-retry
  path hang off it; re-entry after `/clear` had no flat-plan rule and a terse follow-up sent the
  supervisor hunting. Not shipped: open, approve, state and tear-down prompts, and option
  grammars such as `push` or `go` arguments (said in prose, as today). `resume` is a built-in
  command and would be shadowed; `pick-up` is free. Such skills cost no per-turn tokens
  (description out of the model's context).
- D5 `/close-out` body (prose, about 20 lines): if a plan is still open, print the state line as
  `not safe` and stop; otherwise brief `fixer` `teardown` (`teardown retry` when `$ARGUMENTS`
  contains `retry`), then `curator` `close-out <path>` per finished plan or working artifact,
  `record` for a bare decision; in a one-off, `curator` creates the store first
  (`pack/agents/curator.md:28`; inside git, after the tracked-or-local question,
  `supervisor.md:97-100`); `git-ops` `chore(memory): ...` for staged paths; end with
  `Run yourself:` if anything remains and the `Session state:` line.
- D6 `/pick-up` body (about 15 lines): one `scout` plan-state call on the named plan, else on
  `.supervisor/working/plans/` (never read the plan yourself); report at most 10 lines: plan,
  packages or open `## Todo`, last Log lines, pending questions; propose the next step (next
  wave; `executor` on the open slices; `/close-out` when the Todo is complete) and wait; with
  no live plan, say so and ask what to pick up.
- D7 Flat-plan resume is in scope and is one edit: `supervisor.md:79-80` becomes package or
  flat-plan `## Todo` state from the lead's report or one `scout` plan-state call on resume.
- D8 Teardown failure: `residue/SKILL.md:57-58` failure line becomes "(host, resource, reason,
  `remove` command)", word-neutral by shortening `:54` "and the file once it is empty" to "and
  the file when empty" (`test_residue_skill_caps` holds the skill at 350, now 349). The doc
  tells the user to run the command and then `/close-out retry`, after which the entry is
  deleted. No other residue change.
- D9 Word budget: no cap raise (owner, 2026-10-28); trims instead. `supervisor.md` is at 999
  body words (`tests/test_pack_lint.py:23, 84-91`, `str.split()` after the frontmatter). The new
  rules cost 71: D2 44, D3 22, D7 +5. The trims T1-T8 (Outline) take the body to 872, so it
  lands at 943 with 57 to spare; verified on a scratch copy, with the linted literals "harness
  attribution reminders" and "teardown" intact. Reasoning: the rules dropped (the two Owns
  tables, "distill, then archive") duplicate the agent descriptions the Agent tool already
  lists in the supervisor's context (`researcher.md:3`, `planner.md:3`, `executor.md:3`,
  `writer.md:3`, `fixer.md:3`, `git-ops.md:3`, `scout.md:3`) or `curator`'s own procedure
  (`curator.md:16, 38-40`); `researcher.md:3` gains "code tracing, literature/web research" and
  `executor.md:3` gains "refactors" and "skill" (D13) so nothing the tables said is lost. Not
  adopted: the five judgment-only compressions (J1-J5 of the trim proposal), which the owner
  did not approve and the budget does not need. Trims never touch `supervisor.md:95-96`
  (externalize-memory edits them) or `:79-80` beyond D7.
- D10 Cross-links: `docs/context-engineering.md:18` gains one sentence after "auto-compaction"
  pointing to the doc's clear guidance; `docs/architecture.md:68` gains the state line and a
  link; the architecture `## Skills` table gains one row for the two skills, and the
  `researcher` row (`:23`) gains "code tracing, literature/web research" (inventory sync for
  the description change; the `executor` row `:25` already names refactors-class work, so it
  gains "skill definitions" only). README gets a `## Workflow Lifecycle` section (one
  paragraph plus link) after `## Larger Work`, two lines in "Skills you run yourself", a
  docs-list line and the layout line.
- D11 One change set, one executor, one squash on `main`; separate from externalize-memory,
  which lands first as 8.2. This branch rebases on it: its word-neutral `supervisor.md:95-96`
  edit becomes the base the trims surround, so after each rebase the executor re-checks that
  T1-T8 touch no line of that hunk (`git diff -U0 main~1 main -- pack/agents/supervisor.md`
  names it) and that the body count still reads 943. Shared files and touch points:
  `supervisor.md` (theirs 95-96, ours 14-29, 48-52, 69-70, 79-80, 90-92, 97-100, 104-106,
  119-123), `residue/SKILL.md` (theirs 26-28, ours 54 and 57-58), `README.md` docs list and
  layout line (both add a line), `docs/architecture.md` (theirs 102, ours 23, 25, 68 and the
  Skills table). Conflicts are adjacent-line only.
- D12 Version (owner, 2026-10-29): this change set is v9.0. Work runs on a feature branch
  (`feat/workflow-lifecycle`, cut from `main`, worktree per `repo-workflow`) that rebases on
  `main` frequently and never touches `VERSION` (`tests/test_version.py:71-74` skips off
  `main`). The squash-merge commit sets `VERSION` to `9.0` and adds the `CHANGELOG.md` line in
  the same commit (`tests/test_changelog.py`). Draft line:
  `- **v9** (YYYY-MM-DD): workflow lifecycle: a `Session state:` line after every close-out and booked wave that says whether `/clear` is safe and how to resume, a fixed `Run yourself:` block for steps only you can run, `/close-out` and `/pick-up` commands, routing on agent descriptions with a static scope test and an optional live routing check. See [docs/workflow-lifecycle.md](docs/workflow-lifecycle.md).`
- D13 Static routing-scope test (owner, 2026-10-29), always on, in `tests/test_pack_lint.py`: a
  `ROUTING_SCOPE` fixture of (agent, phrase) pairs covering every cell of the dropped Owns
  tables, each phrase asserted case-insensitively in that agent's frontmatter `description`;
  plus one assertion that `supervisor.md` still names every fixture agent in backticks. Pairs:
  `researcher`: investigat, code tracing, literature/web research, research artifact;
  `planner`: decision-and-outline plan, plan annotation cycles, checklist sync; `executor`:
  code, script, test, config, refactors, agent and skill definitions, git conflicts, Python
  environments; `writer`: scientific documents, proposals, reports, presentation content,
  emails, project docs; `fixer`: small, fully specified edits, running a given command or
  script, reporting its output; `git-ops`: status, diff, log, commit, branch, push, pull,
  stash, tag; `scout`: read-only, quick lookups. Two descriptions change to satisfy it:
  `researcher.md:3` (D9) and `executor.md:3`, whose list becomes "code, script, test, config,
  refactors, agent and skill definitions, git conflicts, and Python environments". Frontmatter
  only; body caps unaffected.
- D14 Live routing test (owner, 2026-10-29), `tests/test_live_routing.py`, under 150 lines,
  skipped unless `SUPERVISOR_LIVE_ROUTING=1` and `claude-supervisor` is on `PATH`. Mechanics
  (planner-worker, Claude Code CLI reference, headless and sub-agents pages, `deploy:137, 158,
  628-651`): the launcher exports `CLAUDE_CONFIG_DIR` and execs `claude "$@"`, and the deployed
  `settings.json` `"agent": "supervisor"` makes the supervisor the main thread; `-p` passes
  through. Each case runs
  `claude-supervisor -p "<wrapper + request>" --agent supervisor --disallowedTools "<denies>" --permission-mode dontAsk --max-turns 4 --max-budget-usd 0.5 --output-format json`
  and parses `result` for one line `MODE: <1|2|direct>; AGENT: <name|none>`; the wrapper says
  "Routing check only: do not dispatch or call tools; answer from your routing rules; reply
  with exactly one line `MODE: ...; AGENT: ...`". `<denies>` is one scoped rule per pack agent,
  `Agent(<name>)` for each `pack/agents/*.md` stem, joined by commas: a scoped rule denies the
  matching calls and leaves the tool, and with it the agent catalogue the supervisor routes on,
  in context, while a bare `Agent`, `Task` or `Agent(*)` would remove the tool and the
  descriptions (CLI reference, `--disallowedTools`; sub-agents, "Disable specific subagents").
  Backstop: a case also fails when `num_turns` (SDK result field) is above 2 or no `MODE:` line
  parses; `--max-budget-usd` bounds a disobedient case, and the test prints each case's
  `total_cost_usd` and model plus the total. 14 cases, request -> (mode, agent): typo fix in a
  named file -> (2, fixer); commit staged changes with a given message -> (2, git-ops); which
  file defines a named function -> (2, scout); "/clear vs /compact?" -> (direct, none); "find
  out how deploy registers profiles and write it up" -> (1, researcher); "plan a `--json` flag
  for `deploy status`" -> (1, planner); "add a `--json` flag to `deploy status` with tests" ->
  (1, executor); "draft the overview section of our proposal from these notes" -> (1, writer);
  rename one variable across three named files -> (2, fixer); a quoted `fixer` report
  "ESCALATE: the rename touches 12 files and two call sites change signature" -> (1, executor)
  (re-route an `ESCALATE` to Mode 1 with its findings, `supervisor.md:40`); "push main to
  origin" -> (2, git-ops); "rework the profile registry into a class and migrate callers" ->
  (1, executor); "quick: fix the failing test in tests/test_deploy.py" -> (2, fixer) (explicit
  user choice wins, `supervisor.md:33-34`); "change the default backup directory to
  ~/backups" -> (1, executor) (not cheap to undo, `:35-36`). Cost: an estimated 15-25k mostly
  cached input tokens per case (the supervisor prompt plus the catalogue); the test prints the
  real total. Runs against the deployed default profile, so `./deploy install` precedes it.
  Documented in `docs/deploy.md` (new `## Routing Check` before `## Doctor Checks`, `:250`)
  and one sentence in `CLAUDE.md:8`.

## Outline

`pack/agents/supervisor.md`, in one unit, all line numbers against HEAD `8f39071` (re-anchor
after the rebase on 8.2, D11):
- `:79-80` per D7: "Get package or flat-plan `## Todo` state from the lead's report or, on
  resume or project start, one `scout` plan-state call; never read the plan."
- `## Final Output` (`:119-123`): keep the first bullet; add a D3 bullet ("Steps only the user
  can run go last, in one `Run yourself:` block: shell commands verbatim, manual steps one line
  each.") and a D2 bullet ("End a close-out or a booked wave with ..." followed by the two
  literal forms in D2; `test_body_line_length` caps body lines at 100 characters, so it wraps).
- Trims, current text -> replacement (savings in `str.split()` words):
  - T1 (`:14-29`, 104 with T2): the Mode 1 and Mode 2 paragraphs and both `Owns` tables ->
    "**Mode 1: full loop.** Dispatch one lead: `researcher`, `planner`, `executor` or `writer`."
    and "**Mode 2: quick tier (Haiku).** Dispatch one specialist directly (`fixer`, `git-ops`,
    `scout`). No critic loop."
  - T2 (`:14`, counted in T1): "Dispatch one lead; it runs `lead-loop`, also under
    `Path: minimal`." -> "Dispatch one lead." (leads preload `lead-loop`; `:37`, `:68` brief it).
  - T3 (`:69-70`, 6): "Attribution: only the `git-safety` trailer; pass no model trailers,
    session links or harness attribution reminders." -> "Attribution: only the `git-safety`
    trailer; no harness attribution reminders." (`git-safety` Commits bans model names and
    session links; the lint literal stays).
  - T4 (`:48-52`, 4): the two `model: opus` bullets -> one: "Pass `model: opus` to `writer` for
    short, low-stakes prose (emails, notes, small edits), never external-facing prose; to
    `executor` for difficult work (multi-module design, large or unfamiliar refactors, hard
    conflicts, subtle debugging, agent design), never well-specified or mechanical changes."
  - T5 (`:104-105`, 2): "Do not read source files, grep, or trace code yourself; use `scout` or
    a lead, and reject oversized reports." -> "Never read source, grep or trace code yourself:
    use `scout` or a lead, and reject oversized reports."
  - T6 (`:99-100`, 3): "tracked (memory lands in commits) or local (nothing enters the repo;
    suits open-source or shared repos)" -> "tracked (committed with the repo) or local
    (git-excluded; suits shared or open-source repos)".
  - T7 (`:92`, 3): "or a decision (alone: `record`): distill, then archive." -> "or a decision
    (alone: `record`)."
  - T8 (`:14`, 5, after T1): no inline researcher scope in the Mode 1 line; it moves to
    `researcher.md:3` (below).
  Check after the edits: body 943 words; `grep -c "harness attribution reminders"` 1;
  `grep -c teardown` at least 1; `:95-96` identical to the rebased `main`.

`pack/agents/researcher.md:3` and `pack/agents/executor.md:3`: description changes per D13
(frontmatter, no body-word cost).

`tests/test_pack_lint.py`: after `test_leads_dispatch_only_own_workers` (`:158-163`), a module
constant `ROUTING_SCOPE = {agent: [phrases]}` (D13) and two tests in the file's shape:
`test_routing_scope_in_description(agent)` (parametrized over the dict; lower-cased
`description` contains each phrase) and `test_supervisor_names_routed_agents()` (each
`` `agent` `` literal in `supervisor.md`).

`tests/test_live_routing.py` (new): module docstring stating the cost and the gate;
`pytestmark = pytest.mark.skipif(os.environ.get("SUPERVISOR_LIVE_ROUTING") != "1" or
shutil.which("claude-supervisor") is None, reason=...)`; `CASES` list of
`(request, mode, agent)` (D14); `WRAPPER` string; `DENIES` built from the `pack/agents/*.md`
stems as `Agent(<name>)` joined by commas (D14); `run_case(request) -> dict` via
`subprocess.run([...], capture_output=True, text=True, timeout=300)` and `json.loads`;
`parse(result) -> (mode, agent)` with `re.search(r"MODE:\s*(1|2|direct);\s*AGENT:\s*(\S+)")`;
one parametrized test asserting both fields and `num_turns <= 2` when the field is present,
and a session-scoped fixture that sums
`total_cost_usd` and prints `routing check: N cases, $X, model M` at teardown. No fixtures
that write files; residue none.

`pack/skills/residue/SKILL.md:54, 57-58`: D8.

`pack/skills/close-out/SKILL.md`, `pack/skills/pick-up/SKILL.md` (new; shape of
`pack/skills/supervisor-config/SKILL.md:1-12`): frontmatter `name`, `description` (what and
when: "Use when the user runs `/close-out ...`"), `argument-hint`,
`disable-model-invocation: true`; body per D5 and D6, key instruction first (a `/compact`
re-attaches only the first 5k tokens of a skill). No `scripts/`, no `references/`.

`docs/workflow-lifecycle.md` (new, about 170 lines, written for users per the conventions in
Scope Notes; prose and tables, no agent-prompt tone). Sections, in order:
1. The lifecycle in one paragraph and the three sizes (D1): tier, what runs, what is on disk
   meanwhile, close-out.
2. Prompts and answers per step, per tier: open, mid-course additions, questions and plan
   approval (numbered answers, "all as proposed"), result, close-out (`/close-out`), end; per
   row what you type and what the supervisor answers (outcome first, who did what, validation,
   next step, the `Session state:` line). Templates from the research tier tables, generalized.
3. Temporary artifacts: scratchpad (per session, left to the OS), worktrees (removed at
   landing), residue ledger (torn down after each wave for done packages and at run end, before
   close-out), plans and research (archived at close-out); a failed teardown and what to do (D8).
4. `Run yourself:` (D3): what lands there, typical items, how pushes get authorized (opening
   prompt, mid-turn message, or the question).
5. Clearing and compacting: what survives `/clear` (store, plan files and ledgers, worktrees and
   branches, git history) and what does not (the conversation, a lead's report not yet in the
   plan Log, unanswered question batches, `not stored:` or lesson proposals, in-flight agent
   results, the scratchpad as a working location); cheap points in order (after close-out, after
   a booked wave, after plan approval once the plan is on disk) and unsafe ones; `/compact`
   versus `/clear` in two sentences; the state line as the signal.
6. Resuming: `/pick-up [plan]` for a program and for a flat plan; with no plan file, state the
   task.
7. Without a memory store: nothing persisted, the single `not stored:` line, no ledger (agents
   remove what they made before reporting and list what they could not), what survives, how to
   opt in ("remember ...", "make this a project", or `/close-out`, which creates the store; the
   tracked-or-local question inside git); to end a one-off without storing anything, `/clear`.

`docs/deploy.md`: `## Routing Check` before `:250`, about 15 lines: what it checks, the exact
command (`SUPERVISOR_LIVE_ROUTING=1 python3 -m pytest -q tests/test_live_routing.py -s`), that
it calls the model about 14 times against the deployed default profile, costs money (the run
prints the total) and needs the owner's go, and that it skips by default. `CLAUDE.md:8`: one
sentence after the pytest line pointing there.

`README.md`: `## Workflow Lifecycle` section after `:153`; `:70-74` two bullets; `:213-215` one
line; `:278` the file. `docs/architecture.md`: `:23` researcher row, `:25` executor row, `:68`
one sentence (state line, link), one Skills row after `:119`. `docs/context-engineering.md:18`:
one sentence. `CHANGELOG.md`: the D12 line, in the squash commit only, with the date filled in.

## Slices

1. Resume path: the state line, flat-plan state, trims, `/pick-up`.
   Delivers: the supervisor prints `Session state:` with a resume prompt that works; the lint
   is green under the unchanged caps.
   Units: (a) `pack/agents/supervisor.md` (D2 bullet, D7, T1-T8) with `pack/agents/researcher.md:3`
   and `pack/agents/executor.md:3` (one agent: T8 and D13 depend on the descriptions);
   (b) `pack/skills/pick-up/SKILL.md`.
   Tests:
   - pack_lint: `python3 -m pytest -q tests/test_pack_lint.py` -> passes with `BODY_WORD_CAPS`
     unchanged; `test_skill[pick-up]` collected and green.
   - budget: the lint's `body_words` on `supervisor.md` -> 921 after this slice (943 minus the
     D3 bullet's 22), and `git diff -U0 main -- pack/agents/supervisor.md` shows no hunk at the
     externalize-memory lines (`:95-96` at HEAD `8f39071`).
   - pick_up_frontmatter: `grep -c "disable-model-invocation: true" pack/skills/pick-up/SKILL.md`
     -> 1; `grep -c "context: fork"` -> 0.
   Checkpoint: `python3 -m pytest -q tests/test_pack_lint.py`.

2. Routing safety: the static scope test and the gated live test.
   Delivers: every dropped table cell is pinned to a description; the live check exists, skips
   by default, and is documented.
   Units: (a) `tests/test_pack_lint.py` (`ROUTING_SCOPE`, two tests); (b)
   `tests/test_live_routing.py`; (c) `docs/deploy.md` `## Routing Check` and `CLAUDE.md:8`.
   Tests:
   - routing_scope_green: `python3 -m pytest -q tests/test_pack_lint.py -k routing` -> all
     `ROUTING_SCOPE` parametrizations pass against the slice 1 descriptions.
   - live_skips: `python3 -m pytest -q tests/test_live_routing.py -rs` with the variable unset
     -> every case reported as skipped, zero subprocess calls, under 2 seconds.
   - live_parses: `parse("MODE: 2; AGENT: fixer")` -> `("2", "fixer")`; `parse("no line")` ->
     `None` (a plain `python3 -c` import of the module, no model call).
   Checkpoint: `python3 -m pytest -q tests/test_pack_lint.py tests/test_live_routing.py -rs`.
   The live run itself is not part of the checkpoint (D14: owner's go; `Run yourself:` in the
   executor's report).

3. Close-out path: `Run yourself:`, the actionable teardown line, `/close-out`, inventory.
   Delivers: a close-out ends with the block and the line; a blocked teardown reports its
   command; `/close-out` installs; README and architecture list both skills.
   Units: (a) `pack/agents/supervisor.md` Final Output `Run yourself:` bullet (same agent as
   slice 1's unit a, sequential; body 943 after it); (b) `pack/skills/residue/SKILL.md`;
   (c) `pack/skills/close-out/SKILL.md`; (d) `docs/architecture.md` (`:23`, `:25`, `:68`,
   Skills row) and `README.md:70-74`.
   Tests:
   - residue_cap_and_line: `python3 -m pytest -q tests/test_pack_lint.py -k residue` -> green;
     `grep -n "remove" pack/skills/residue/SKILL.md` -> the report sentence names the command.
   - close_out_frontmatter: as pick_up_frontmatter, for `close-out`.
   - installs: `./deploy install --dry-run` -> lists both skills.
   Checkpoint: `python3 -m pytest -q tests/test_pack_lint.py` and the dry run.

4. The doc, README, cross-links; landing as 9.0.
   Delivers: `docs/workflow-lifecycle.md`, README section and links, context-engineering link;
   the branch ready to land.
   Units: (a) `docs/workflow-lifecycle.md`; (b) `README.md` (section, docs list, layout line);
   (c) `docs/context-engineering.md:18`.
   Tests:
   - links_resolve: open each new link target (file and `#anchor`) in README, `docs/` -> exists.
   - doc_matches_pack: the `Session state:` line quoted in the doc equals the `supervisor.md`
     form; `grep -n "/close-out\|/pick-up" docs/workflow-lifecycle.md` -> both named with the
     skills' `argument-hint`.
   - branch_untouched_version: `git diff main -- VERSION CHANGELOG.md` on the branch -> empty.
   Checkpoint: `python3 -m pytest -q` on the rebased branch (`test_version_bumped_with_changes`
   skips off `main`).

## Verification

After slice 4, on the branch rebased on `main` at 8.2: `python3 -m pytest -q` green;
`./deploy install --dry-run` lists the two skills; `supervisor.md` body is 943 words, and the
trims T1-T8 still touch no line of `supervisor.md:95-96` (D11); `tests/test_live_routing.py`
shows 14 skips with the variable unset; the doc's state line, `Run yourself:` wording and the
two commands match
`supervisor.md` and the skills where quoted; a read of `docs/workflow-lifecycle.md` against the
research tier tables finds every lifecycle step covered for all three tiers plus the no-memory
case; the critic reviews the doc as `prose` against the two doc conventions. Landing
(`repo-workflow` Landing, after the curator close-out on the branch): squash into `main`, set
`VERSION` to `9.0`, add the D12 line to `CHANGELOG.md` with today's date, run
`python3 -m pytest -q` (now including `test_version_bumped_with_changes` and
`test_changelog_has_current_major`), commit. Then, user-run (`Run yourself:`): `./deploy
install`, one real close-out to see the line, and, when the owner wants the live check,
`SUPERVISOR_LIVE_ROUTING=1 python3 -m pytest -q tests/test_live_routing.py -s`.

## Risks

- The state line is a prompt rule, not code: the supervisor may omit it under load; the doc's
  section 5 tells the user to ask for it.
- T1 removes the routing tables: the supervisor routes on the agent descriptions the Agent tool
  lists; a misroute would show as a wrong lead in the first sessions (`executor.md` Scope and
  `writer.md:3` carry the docs split; `researcher.md:3` and `executor.md:3` gain the tables'
  words; D13 pins them; D14 checks live on request).
- Live test mechanics unverified by a model call: whether the `agent` setting reaches `-p`
  runs is implied, not stated, by the sub-agents docs, hence `--agent supervisor` on the
  command; that scoped `Agent(<name>)` denies keep the catalogue in context follows from the
  CLI reference's general scoped-rule sentence, not from an Agent-specific one; `num_turns` is
  documented for the SDK result type, not the headless page; the cost figure is an estimate.
  The first live run confirms all four (the executor's `Run yourself:` names it); the test
  prints the model and cost.
- Two change sets touch `supervisor.md`, `residue/SKILL.md`, README and architecture (D11);
  adjacent-line conflicts on rebase, resolved by `executor`.
- Doc drift: the doc quotes pack wording; a later pack change must update it (one sentence in
  the doc's last section).

## Scope Notes

In: what the Goal lists. Out: the close-out trigger, residue redesign or scratchpad cleanup,
lesson proposals after close-out, program logs for flat plans (roadmap item 3), everything in
externalize-memory, `scout.md` and `lead-loop`, the J1-J5 compressions, any cap change, running
the live routing test (owner's go, `Run yourself:`), deploying to the user's live profile
(the user runs `./deploy install`).
User decisions the executor must not reopen: the tiers (D1); the state line and `Run yourself:`
block in every tier (D2, D3); the doc as `docs/workflow-lifecycle.md` plus a README paragraph
(D10); no cap raise, trims T1-T8 exactly (D9, owner 2026-10-28,
`.supervisor/memory/decisions/2026-10-25-raising-a-pack-word-cap-is-owner-only.md`); v9.0 on a
feature branch, `VERSION` and `CHANGELOG.md` in the squash commit only (D12, owner 2026-10-29;
`CLAUDE.md` version rules,
`.supervisor/memory/decisions/2026-10-24-version-is-hand-bumped-no-release.md`); the static
and the env-gated live routing tests (D13, D14, owner 2026-10-29); pack files self-contained
(`agent-authoring`). Doc conventions:
`.supervisor/memory/conventions/2026-10-26-docs-are-for-users-not-prompts.md`,
`.supervisor/memory/conventions/2026-10-26-docs-describe-what-we-do-and-why.md`.

## Assumptions

- A `disable-model-invocation: true` skill without `context: fork` injects its body into the
  supervisor's conversation with `$ARGUMENTS` substituted (Claude Code skills docs, checked by the
  planner-worker); checked live by the user's first `/close-out` after install.
- `deploy` installs any `pack/skills/<name>/SKILL.md` unchanged (`deploy:411-413`); checked by the
  slice 3 dry run.
- The Agent tool lists each agent's `description` in the supervisor's context, so T1 loses no
  routing information; checked by the critic in slice 1 against the removed table cells.
- `claude -p --output-format json` returns `result` and `total_cost_usd` (headless docs);
  checked by the first live run.

## Open Questions

None. Open Question 1 (cap raise) was resolved by the owner on 2026-10-28: no raise, trims
T1-T8 (D9). The owner's 2026-10-29 amendments (v9.0, routing tests) are D12-D14.

## Log

- 2026-10-28 decision: no supervisor word-cap raise; trims T1-T8 (D9) adopted instead (source: user)
- 2026-10-29 decision: this change set is v9.0 on a feature branch that never touches `VERSION`; the squash-merge commit sets `VERSION` to `9.0` and adds the `- **v9** (YYYY-MM-DD): ...` line to `CHANGELOG.md` in the same commit; it rebases on the externalize-memory 8.2 change set and T1-T8 never touch `supervisor.md:95-96`; source: user
- 2026-10-29 decision: routing scope moving from the supervisor's Owns tables into agent descriptions is guarded by a static, always-on scope test in `tests/test_pack_lint.py` and an env-gated live routing test in `tests/test_live_routing.py`; source: user

## Todo

- [ ] S1 `supervisor.md`: `:79-80` flat-plan state; Final Output `Session state:` bullet;
      trims T1-T8; body 921, literals intact, externalize-memory hunk untouched
- [ ] S1 `researcher.md:3` and `executor.md:3` descriptions per D13
- [ ] S1 `pack/skills/pick-up/SKILL.md` per D6; lint green
- [ ] S2 `tests/test_pack_lint.py`: `ROUTING_SCOPE`, `test_routing_scope_in_description`,
      `test_supervisor_names_routed_agents`
- [ ] S2 `tests/test_live_routing.py` per D14; skips by default (`-rs` shows 14 skips)
- [ ] S2 `docs/deploy.md` `## Routing Check`; `CLAUDE.md:8` sentence
- [ ] S3 `supervisor.md` Final Output `Run yourself:` bullet; body 943
- [ ] S3 `residue/SKILL.md:54, 57-58` per D8; residue cap test green
- [ ] S3 `pack/skills/close-out/SKILL.md` per D5
- [ ] S3 `docs/architecture.md` `:23`, `:25` rows, `:68` sentence, Skills row;
      `README.md:70-74` two bullets; dry-run install lists both skills
- [ ] S4 `docs/workflow-lifecycle.md` sections 1-7
- [ ] S4 `README.md` `## Workflow Lifecycle`, docs list, layout line
- [ ] S4 `docs/context-engineering.md:18` sentence; link check; `python3 -m pytest -q` on the
      rebased branch
- [ ] Landing: squash on `main`, `VERSION` 9.0, `CHANGELOG.md` v9 line, full suite, commit
