# Audit: user documentation added since v7

Date: 2026-10-29. Scope: material added or changed since v7.0 (commit 42b57ca) in `README.md`, `CHANGELOG.md`, and `docs/{architecture,deploy,context-engineering,local-memory,workflow-lifecycle}.md`. Audience assumed: an end user who installs the pack and works with it in Claude Code. Suggestions only; nothing in the audited files was edited. Line numbers are current (HEAD). Severity: **blocking** (user is misled or cannot act), **should-fix** (wrong reader, or raises a question it does not answer), **nit**. Categories: audience mismatch, jargon (agent-internal terms leaking), why/when (missing user-facing reason or trigger), example (missing worked example), structure, accuracy, duplication, stale xref.

## Verdict

The hypothesis holds, but unevenly:

- **Holds strongly** for `docs/workflow-lifecycle.md` and the new parts of `docs/architecture.md`. Both are addressed to "you" but describe the agents' internal procedure: ledger fields, which agent appends which log line, report caps, `Review:`/`Path:` tokens, `ESCALATE` blocks, "plan-state reads".
- **Holds in a different form** for `docs/deploy.md`: the new text is in user voice but written for the pack's maintainer, covering every edge case (version-string sanitising, launcher dispatch internals, the live routing check, "verified live on" dates). That breaks the convention *clear and correct, not exhaustive* more than it breaks audience.
- **Holds only locally** for `README.md` (two bullets in Persistence And Memory, a few unexplained terms) and `docs/context-engineering.md` (quantitative mechanics in an otherwise human-facing essay).
- **Does not hold** for `docs/local-memory.md`, whose voice is the model for the others (what you run, what you get). Its problems are accuracy, including the one blocking finding of this audit.

Top five changes: (1) fix the `local-memory.md` "Both exist" repair that can delete another project's memory; (2) rewrite `workflow-lifecycle.md`'s sizes table, ledger paragraph and clearing list in user terms and add one worked example; (3) strip the brief-writer vocabulary from `architecture.md` Mode 1 and Git Work; (4) move the maintainer material out of `deploy.md` (Routing Check, Versions internals, launcher internals, exit codes into their own section); (5) add a short glossary and a reading-order Documentation list to the README.

## Per file

### docs/workflow-lifecycle.md (new, 110 lines)

Purpose as a user reads it: what to type, what comes back, what is on disk, when `/clear` is safe, how to resume. Reads as written for: the user in its tables and the Run Yourself section; for an agent, or for someone who knows the agent prompts, in the sizes table, Temporary Artifacts and Clearing And Compacting. Hypothesis holds most strongly here.

| ID | Line | Snippet | Sev | Cat | Suggested change |
|---|---|---|---|---|---|
| WL-1 | 11-15 | "One quick specialist (Mode 2)", "test residue, if any, is in the ledger", "`curator` runs only if", "A program", "a plan-state commit", "teardown for finished packages" | should-fix | jargon | Rewrite rows as what you see. Small: "One agent, no plan file. On disk: only the changed files. At close-out: test leftovers removed; memory updated only if there was something to record." Medium: "One lead with a plan or research file in `.supervisor/working/`, a worktree for code. At close-out: leftovers removed, decisions recorded, plan archived." Large: "A plan split into work packages, run in waves, often over several sessions. On disk: the parent plan with each package's state. After each wave: leftovers of finished packages removed and the plan committed; at the end, full close-out." |
| WL-2 | 29 | "it has needed a typed nudge in practice, in many phrasings"; "After a harness-blocked teardown" | should-fix | audience mismatch | Development history. "Close-out does not start by itself: type `/close-out` when the work is done. If a plan is still open it says so and stops. If a removal was blocked, `/close-out retry` tries again (next section)." |
| WL-3 | 33-41 | The `Session state:` format with three bracketed fields and no key | should-fix | why/when | Keep the format (the user sees it verbatim) and add a three-line key: first field, where the work stands (closed out, or wave N of a large plan finished and recorded); `residue`, whether test leftovers were removed; `store`, whether the memory store was committed, is uncommitted, or does not exist here. |
| WL-4 | 15, 43, 89, 100 | "program", "fully booked wave" | should-fix | jargon | Define once at first use: "a program (a plan split into work packages)"; "booked" means the wave's results are written into the plan and committed. Both words stay, since the state line uses them. |
| WL-5 | 58 | "`fixer` tears them down after each wave ... Each entry has a `remove` command and a `check`; the entry is deleted when the check passes" | should-fix | jargon | The ledger's schema and scheduling belong to the pack. "Things tests leave behind (temp dirs, config files, background processes, files on remote hosts) are listed in `.supervisor/working/residue/`, which git ignores, and removed at the end of the work. You see only the ones that could not be removed." Keep `remove`/`check` in L61 only, where the user acts on them. |
| WL-6 | 79-84 | "a lead's report that `fixer` has not yet appended to the plan log"; "any `not stored:` note" | should-fix | jargon, structure | "a finished step whose result is not yet written into the plan file (the state line says `not safe to /clear` then)". `not stored:` is explained only at L104; add "(see Without A Memory Store)" or move that explanation up. |
| WL-7 | 86-92 | "The plan log and status are updated, teardown for finished packages has run, the plan state is committed ... needs only a plan-state read" | should-fix | jargon | "After a wave of a large plan is recorded. The plan file holds everything the next session needs; nothing is waiting on your answer." |
| WL-8 | 98 | "It asks `scout` for one plan-state read, of the plan you name or otherwise of `.supervisor/working/plans/`"; "open `## Todo` items" | should-fix | jargon | "It reads the plan you name, or finds the live one in `.supervisor/working/plans/`, and reports in at most ten lines: the plan, its packages or open items, the last log lines and any pending questions." |
| WL-9 | whole page | README L159 promises "the prompts to type and the answers to expect"; no end-to-end example exists | should-fix | example | Add one worked example of a medium task, about 15 lines: the opening prompt; the supervisor's "dispatched `planner`"; the plan path and a two-question batch; "1 yes, 2 as proposed"; the result; `/close-out`; the state line; `/clear`; `/pick-up`. Place it after Prompts And Answers. |
| WL-10 | 110 | "This page quotes wording from the pack ... and must be updated when that wording changes." | should-fix | audience mismatch | A maintainer note. Move to this repo's `CLAUDE.md` or an HTML comment. |
| WL-11 | 56 | "Anything that must outlive a step is recorded in the residue ledger instead." | nit | jargon | Phrased at the agent. "Nothing you need is kept there." |
| WL-12 | 61 | "The Claude Code harness sometimes refuses a removal outright"; "marked `failed:`" | nit | jargon | "Claude Code's permission system sometimes refuses a removal"; drop the marker name. |
| WL-13 | 75 | "Nothing you need to do is asked for in prose elsewhere in the answer" | nit | audience mismatch | Reads as a prompt rule. "Everything you need to do is in that block." |
| WL-14 | 94 | "/compact ... keeps the invoked skills attached, within a token budget per skill" | nit | jargon | Claude Code internals; cut the clause. |
| WL-15 | 104 | one-off defined as "outside git, with no `.supervisor/` ... here or above" | should-fix | accuracy | `$HOME` and its ancestors never count (project-memory SKILL.md); most users have `~/.claude/`, so the sentence as written makes every folder under home a project. Add "(your home directory and what is above it never count)" as README L176 does. |
| WL-16 | 61 | "the retry reruns each failed entry's `remove` and `check`" | nit | accuracy | Retry runs every eligible entry, not only the failed ones (residue SKILL.md Teardown). "reruns the teardown, failed entries included". |
| WL-17 | 108 | "Inside a git repository you are asked first whether the store is tracked or local" | nit | accuracy | In a section about non-projects this is near-vacuous: a git work tree is always a project. Move the sentence to the README's Tracked-or-local bullet, or drop it. |

Where the hypothesis does not hold: the Prompts And Answers table (L45-52), Run Yourself (L63-75), the first half of Resuming (L98), and the "how to make it a project" paragraph (L108) are in the right voice and should be the model for the rest.

### docs/architecture.md (modified; 95 changed lines)

Purpose as a user reads it: the reference page, every agent and skill, the two modes, git behaviour, memory layout. Reads as written for: whoever writes briefs. The new Mode 1 and Git Work text restates agent instructions as reference: report caps, `Review: full|light|none`, `Path: minimal`, "when the brief names its SHA", `ESCALATE` block fields. Internal vocabulary is legitimate on a reference page if it is explained once and the user has a reason to care; here it is mostly neither.

| ID | Line | Snippet | Sev | Cat | Suggested change |
|---|---|---|---|---|---|
| AR-1 | 48 | "reports within caps: a summary normally under 800 words with at most 20 file paths and 5 excerpts ... at most 12 findings" | should-fix | audience mismatch | "The lead reports back in a short summary with paths to the full output." Drop the worker and critic caps; `context-engineering.md` already carries one illustrative number. |
| AR-2 | 50, 76, 78 | "`Review: light` ... `Review: none`"; "`Review: light` alone changes only the review depth; `Path: minimal` also fixes that shape" | should-fix | audience mismatch, why/when | These are brief tokens. Replace with what the user controls: "The supervisor picks the review depth. You can ask for it: 'quick' or 'just do it' skips review; 'full', 'thorough' or 'with review' forces a lead with review" (README L68, supervisor.md L21). Delete L78's sentence. |
| AR-3 | 66 | "or a fully booked wave ends with a `Session state:` line", with fixer, git-ops and `Amend parent:` mechanics | should-fix | jargon | "After each wave you get a status table and the leads' questions; the plan file is updated and committed so a later session can resume; the answer ends with a `Session state:` line." Keep `Amend parent:` in one clause as the plan-file field, or move it to the plan-writing skill pointer. |
| AR-4 | 76 | "returns an `ESCALATE` block (operation, both sides, conflicted files with hunk counts and a mechanical flag)" | should-fix | jargon | "`git-ops` never resolves conflicts: it hands them back, and the supervisor sends simple ones to `executor` and the rest through research and planning." |
| AR-5 | 86 | "without stopping on unrelated changes ... when the brief names its SHA and the operation" | should-fix | jargon | "`git-ops` commits memory updates and other quick edits, raises `VERSION` when your repo uses `X.y`, and amends or resets a commit made in this session only when you ask for it." |
| AR-6 | 102 | "so the rest of this paragraph applies to a tracked store. A local store can be externalized ..." | should-fix | structure | Split: (1) your choice, tracked or local, with the externalize link; (2) commits: "memory changes land as `chore(memory): ...` commits, with your branch's work or on their own". Cut the curator/fixer/lead commit routing. |
| AR-7 | 33, 66, 68, 113 | "a `fixer` teardown removes the test residue recorded in ..." | should-fix | why/when | Define residue at first use (L33): "test residue: the temp dirs, config files, background processes and remote files that tests and smoke runs create; recorded as made, removed when the run ends; you see only failures". Later mentions then need no gloss. |
| AR-8 | 68 | "Field rules: `pack/skills/...`; split rules: `pack/agents/planner.md`; run rules: ..." | nit | audience mismatch | One pointer: "Plan format: `pack/skills/plan-writing/SKILL.md`." |
| AR-9 | 100 | "Leads read matching entries at contract time" | nit | jargon | "when they start a task". |
| AR-10 | 118, 120 | "model invocation disabled" | nit | jargon | "you run it; agents cannot". |

Where the hypothesis does not hold: the Overview (L16) defines lead, worker and Mode 1/2 once and well; Models And Cost (L94) speaks to the user's bill.

Terms used in the new material without explanation are in the glossary below; the plan-file fields (`Status`/`Deps`/`Owns`/`Stages`/`Artifacts`, L58-63) and "depth" (L16) are the ones found only here.

### docs/deploy.md (modified; 152 changed lines)

Purpose as a user reads it: install, maintain, switch model or provider, enable Codex, migrate. Reads as written for: the user, with long stretches for the pack's maintainer. Agent voice appears in three places (the labelled Notes For Claude, which is legitimate; the Codex permission-rule paragraph; one clause in Memory). The larger problem is exhaustiveness against the *clear and correct, not exhaustive* convention.

| ID | Line | Snippet | Sev | Cat | Suggested change |
|---|---|---|---|---|---|
| DP-1 | 87 | "Without a terminal, both need `--yes` (exit code 2 otherwise)." | should-fix | accuracy | Contradicts L85 and L346: launcher `update` without a terminal skips the `claude update` question and succeeds (`deploy:1805-1807`); exit 2 applies to `uninstall`, and to `update` only on a downgrade. "Without a terminal, `uninstall` needs `--yes`; `update` runs and skips the Claude update question." |
| DP-2 | 73-80 | Launcher command block omits `critic` | should-fix | accuracy | The launcher handles `critic enable|disable|status` (`deploy:62, 98`) by running the install's `codex-critic` script directly (`deploy:139`), not the deploy tool copy. Add `claude-supervisor critic enable|disable|status` to the block with a pointer to Codex As Critic; leave L83's tool-copy list as it is. |
| DP-3 | 265-275 | Routing Check: "it is run when the owner asks for it" | should-fix | audience mismatch | Needs a checkout and matters only to someone editing agent descriptions. Move it to a contributor section (or `tests/README`), or open with "If you edit agent descriptions in your checkout, run ..." and drop "owner". |
| DP-4 | 60 | "In the branch name, characters other than letters ... Nothing needs editing after a rebase." | should-fix | audience mismatch | "A `main` install shows `X.y`. A branch install shows e.g. `2.3+my-feature.7.g8b1d7de` (base version, branch, commits ahead, commit, `.dirty` if uncommitted)." Cut the sanitising and rebase sentences. |
| DP-5 | 174 | Argo bullet: "verified live on 2026-10-29 ... a provider profile's seeding drops it ... so `update --yes` never prompts" | should-fix | why/when, structure | Split into steps (VPN, `--username`, optional argo-proxy URL). Replace "seeding" with "the first install's copy of `settings.json`". Drop the verification date and the `update --yes` clause. State why `CLAUDE_CODE_AUTO_MODE_SERVER=0` is exported (reason not stated anywhere; see Open questions). |
| DP-6 | 219 | "so the lead's probe and review calls never prompt, in either mode" | should-fix | jargon | "Install allows the review script's `review` command, so Codex reviews never ask you for permission. `enable`, `disable` and `status` are not allowed, so turning Codex on from a session costs one prompt and no agent can do it unasked." |
| DP-7 | 233 | "Per-domain overrides ... `enable` keeps them." | should-fix | accuracy | `disable` drops the whole `critic` section, overrides included (`codex-critic:106-107`); after disable and re-enable they are gone. Add: "`disable` removes them; set them again after a re-enable." |
| DP-8 | 140 | "`planner` also names `model: fable` when it dispatches `critic`. Deployed files always say `model: fable`, byte for byte" | should-fix | audience mismatch | "Four agents, and `critic` when it reviews plans, run on Fable." Drop "byte for byte". |
| DP-9 | 83 | "run the deploy tool copy under the launcher's own prefix (`<prefix>/state/...`) ... their help and usage errors name `claude-<tag>`" | should-fix | audience mismatch | Lead with the rule: "The launcher handles `update`, `uninstall`, `status`, `list`, `memory`, `-v` and `-h` for its own profile, and `critic` through the install's Codex script. Anything else goes to `claude`, so `claude-supervisor --resume` works as usual. Use `./deploy` for other installs." Cut the path and help-naming detail. |
| DP-10 | 261 | "the launcher fixes the install, so the pack's store README template is read from it" | should-fix | why/when | Replace with the reason: "Use this to keep a local memory store outside the repo, shared by all its worktrees. Run it inside a git project." Link `local-memory.md`. |
| DP-11 | 349 | Exit codes listed only under Notes For Claude Running This | should-fix | structure | Users who script installs need them. Short "Exit Codes" section; a pointer from the Notes. |
| DP-12 | 314 | "Uninstall removes the unmodified managed files and keeps the ones you edited; `--force` removes those as well." | nit | accuracy | Holds only for `--global` (a profile uninstall removes the whole dir, `deploy:1555`); L310 says so, L314 reads as general. Prefix with "For `--global`:". |
| DP-13 | 85, 114 | `--all` "lists the registered installs, one per line" | nit | accuracy | Two lines per install (path, then remote and branch; `deploy:1714-1716`). |
| DP-14 | 108, 114 | "(removed when the source has no `VERSION`)"; "shallow for `main`; full history for other branches, so the merge-base ..." | nit | audience mismatch | Cut the parentheticals. |
| DP-15 | 249 | "a Codex review may report that tests were not independently run" | nit | why/when | Say it is expected and harmless (Codex runs read-only), or give the remedy. |
| DP-16 | 333-342 | "Before 1.0 ... Before 1.6 ..." | nit | structure | Consider cutting migration notes for installs older than the oldest you still expect to meet. |

Where the hypothesis does not hold: the provider rationale at L176 ("so a real Anthropic key in your environment never reaches the provider") and L158 ("try a candidate on a small task first") are exactly the user-facing why the rest lacks. Terms without explanation are in the glossary below; the ones found only here are seeding (174), store README template (261), writing verbs (263), owner (275), managed/unmanaged (206, 329) and preset-exported variable (202, 299). Outside the delta: the Codex "domain" at L233 never lists the valid domain names.

### docs/context-engineering.md (new, 123 lines)

Purpose as a user reads it: why the pack is built as one supervisor plus fresh-window agents and files. Reads as written for: a human reader who wants the rationale; the essay form, the cited sources and the trade-offs section are not agent-voiced. The leak is quantitative mechanics the user never touches.

| ID | Line | Snippet | Sev | Cat | Suggested change |
|---|---|---|---|---|---|
| CE-1 | 121 | "the frontmatter withholds tools ... a lint test caps the length of every agent body ... an `Agent` allowlist applies only to the main thread" | should-fix | audience mismatch | Two sentences in user terms: "Most of these rules are instructions the agents follow, not limits the platform enforces, so an agent can deviate. What is enforced: which tools each agent has, and a length cap on every agent file." Keep the Platform Constraints link. |
| CE-2 | 91 | "at contract time" | should-fix | jargon | "when it starts a task". |
| CE-3 | 123 | The closing paragraph says when to use the pack but not what the design asks of you | nit | why/when | Extend it by one sentence (give paths rather than pasting large inputs; expect short answers with paths to the detail) and link `workflow-lifecycle.md` for clearing and resuming. |
| CE-4 | 49-55, 81 | Report caps (800/600/12/20/5) in the diagram and again in prose | nit | duplication | Accurate today (lead-loop:136, workers, critic:66) but they drift. Keep the diagram labels, make L81 qualitative. |
| CE-6 | 89 | "a 25-word summary and a body of at most 150 words" | nit | jargon | Pack constants. "a one-line summary and a short body". |
| CE-7 | 95 | Per-agent tool lists | nit | duplication | Duplicates the Agents table; keep "The supervisor has no Bash" and link the table. |
| CE-8 | 119 | "about 1,700 words (`researcher`) to over 4,000 (`planner`)" | nit | accuracy | Supervisor at 1,024 words is accurate; the lead figures drift. "several thousand words". |

Where the hypothesis does not hold: The problem, Ways to control context, and most of The design and Trade-offs. The closing paragraph (L123) is the best user-facing statement of when to use the pack in all six files.

### docs/local-memory.md (new, 70 lines)

Purpose as a user reads it: keep memory outside a repo you cannot commit to; share it across worktrees and machines. Reads as written for: the user; the voice to copy. Problems are accuracy and a few agent names.

| ID | Line | Snippet | Sev | Cat | Suggested change |
|---|---|---|---|---|---|
| LM-1 | 56-57 | "**Both exist:** ... Decide which to keep and remove the other." and "**Same-name projects:** ... the second `externalize` stops at the existing store ... do not follow the `link` hint" | blocking | accuracy | When a second same-name project already has a local store, `externalize` raises `both exist` (`deploy:2282`), not the `link` hint (which appears only when the project has no store, `deploy:2286`). Following the "Both exist" repair then deletes the other project's memory. Rewrite "Both exist": "either an interrupted move, or another project with the same default name already uses `<root>/<name>`. Look at `<root>/<name>/README.md` before removing anything; for a name clash re-run with `--name`." Rewrite "Same-name projects" to cover both cases (no store here: you get the `link` hint, do not follow it; a store here: you get `both exist`). |
| LM-2 | 29 | "`git-ops` commits the project's directory at close-out and after program waves, with `chore(memory): <name>: <what>`" | should-fix | jargon | "The pack commits memory changes there at close-out and after each wave of a large plan, as `chore(memory): ...` commits. It never pushes or pulls." |
| LM-3 | 7 | "`curator` ends its report with a hint" | should-fix | jargon | "When you choose a local store, the answer ends with a hint to run ...". |
| LM-4 | 43 | `link` refuses "when nothing exists at the external path" | nit | accuracy | It refuses when `<external>/.supervisor` is not a directory, and also when `CLAUDE.local.md` is a real file in the project (`deploy:2316, 2324`). |
| LM-5 | 19 | Heading "What The Tool Did" | nit | structure | "What `externalize` Does". |
| LM-6 | 23 | "`.supervisor/working/residue/`, so test leftovers never enter the memory history" | nit | jargon | Good gloss already; add "(the residue ledger, see workflow-lifecycle.md)". |
| LM-7 | 47 | "When `executor` cuts a worktree it recreates the two symlinks" | nit | jargon | "Worktrees the pack creates get the two links automatically." |

### README.md (modified; 100 changed lines)

Purpose: entry point; what it is for, install, how to use it, where the rest is. Reads as written for: the user. The hypothesis holds only in two bullets of Persistence And Memory and a handful of terms.

| ID | Line | Snippet | Sev | Cat | Suggested change |
|---|---|---|---|---|---|
| RM-1 | 173 | "The `fixer` agent logs user-provided information into the short-term memory (a plan's `## Log`)" | should-fix | jargon | "What you decide while a plan runs is written into the plan's log, so it survives `/clear`." |
| RM-2 | 177 | One six-line bullet covers tracked, local and external stores | should-fix | structure | Three sub-bullets: tracked (committed, in PRs, reaches collaborators); local (git-excluded, this checkout only); external (`claude-supervisor memory externalize`, link). |
| RM-3 | 253 | API-provider paragraph sits in Maintaining An Install after the CHANGELOG line | should-fix | structure | Move to Choosing An Install as a fourth row or a paragraph after the Fable/Opus one. |
| RM-4 | 284 | "`deploy ... migrate \| critic`" | should-fix | accuracy | `./deploy --help` also lists `memory`. |
| RM-5 | 174 | curator bullet repeats L51 and L173 | nit | duplication | Merge into L173. |
| RM-6 | 50, 73 | "residue" first use, unexplained | nit | jargon | Keep the word (the state line uses it) and gloss it once: "test residue (what tests leave behind)". |
| RM-7 | 145, 155 | `Amend parent:` in the diagram edge and the prose | nit | jargon | Drop from the README; it is a plan-file field. |
| RM-8 | 198 | "all four tiers" | nit | jargon | "the four model tiers (see API Providers)". |
| RM-9 | 215 | "the lead's report names which engine reviewed each round" | nit | jargon | "the answer names which engine reviewed". |
| RM-10 | 237 | "`update` asks once" vs deploy.md L85 "with no question" | nit | accuracy | Not a real drift (the one question is `Run claude update?`); say so: "asks once, whether to run `claude update`". |
| RM-11 | 217-223 | Documentation list: `context-engineering.md` blurb is vague; order is not a reading path | nit | structure | See the doc map below. |
| RM-12 | 253, 198 | "a token or a token helper"; "picked from its list ... or given as `--model-<tier>` flags"; "all four tiers map" | nit | accuracy | Argo takes `--username` and ships default tiers (no picker); with `--base-url` and no preset the tiers can stay unmapped. "usually" or "for the presets" suffices. |

Where the hypothesis does not hold: Using It, How It Works, Larger Work, Codex As Critic, Maintaining An Install and Troubleshooting are in the right voice.

### CHANGELOG.md

| ID | Line | Snippet | Sev | Cat | Suggested change |
|---|---|---|---|---|---|
| CL-1 | 5 | "routing on agent descriptions with a static scope test and an optional live routing check" | should-fix | audience mismatch | Test and maintainer facing. "the supervisor routes on each agent's description" or drop the clause. |

The v8 line's three presets were accurate for v8.0; Argo arrived in 9.5, a minor bump with no entry by policy. No other issue.

## Cross-cutting

### Terms that only mean something inside the pack

| Term | Where it leaks | Recommendation |
|---|---|---|
| `Session state:`, `Run yourself:`, `not stored:` | README, lifecycle, architecture | Keep: the user sees these strings. Explain each once in the lifecycle page with a key (WL-3); README links there. |
| residue, ledger, teardown | README 50/73, lifecycle 13/56-61, architecture 33/66/68/113, local-memory 23 | Keep "residue" (the state line says `residue <removed | N failed>`) and gloss it once at first use in README L50, lifecycle Temporary Artifacts and architecture L33; "ledger" only where the directory is named; "removed" for teardown. |
| program, work package, wave, booked | lifecycle, architecture 54/66 | README already explains packages and waves; add "program" there as the name for a plan with packages. Keep "booked" (the state line says `wave N booked`) and define it once in the lifecycle key (WL-3). |
| flat plan, `## Todo`, `## Log`, `Status`/`Deps`/`Owns`/`Stages`/`Artifacts`, `Amend parent:` | architecture 58-68, README 145/155/173, lifecycle 81/98 | Move to the plan-writing skill pointer; the user sees plan files but needs only "the plan holds its own state and log". |
| brief, handback, report caps, contract, contract time, unit, delta, round, suppression list | architecture 42-50/86/100, context-engineering 35/81/91 | Internal doc. Keep "brief" and "capped report" in context-engineering (explained there); replace elsewhere with "when it starts a task", "a short summary". |
| `Review: full|light|none`, `Path: minimal`, shape | architecture 50/76/78 | Replace with the user's levers: "quick", "full", "with review" (AR-2). |
| `ESCALATE`, session commit, versioned paths, plan-less run, single-stage run | architecture 72-88 | Replace with plain descriptions (AR-4, AR-5); "versioned paths" can stay with one gloss. |
| Mode 1 / Mode 2, lead, worker, quick tier | everywhere | Keep: defined in the README Using It section and architecture Overview. |
| profile, tag, launcher, tracked/local/external store | README, deploy, local-memory | Keep: defined where introduced. |
| tier (model tier), seeding, registry, tool copy, probe, domain | deploy, README 198/253 | Define "tier" once in deploy API Providers and gloss in README; cut seeding/tool copy/probe from user text; list the Codex domain names once. |
| harness, scratchpad | lifecycle 56/61/84 | "Claude Code" and "Claude Code's temporary directory". |

A short "Terms" block (eight lines) at the end of README Using It, or at the top of `workflow-lifecycle.md`, would cover the first four rows; the rest should be rewritten rather than defined.

### Is the README the right entry point, and do the five docs divide the work?

The README is the right entry point: it answers what, for whom, install, daily use, and where the rest is, in that order, in user voice. Two things weaken it: the Documentation list (L217-223) reads as a file list rather than a reading path, and three topics are told twice (README Persistence And Memory against architecture Memory and context-engineering's memory section; README Maintaining An Install and Codex against deploy.md's near-verbatim copies; README Larger Work against architecture Mode 1 and the lifecycle sizes table).

Target doc map, one question per file:

| User question | File | Keep there | Move out |
|---|---|---|---|
| What is it, do I want it, how do I start, what do I type | `README.md` | One paragraph plus link per topic; Troubleshooting | The mechanics bullets in Persistence And Memory (RM-1, RM-2 trimmed); the provider paragraph to Choosing An Install |
| What happens from prompt to `/clear`, what will I see, when is it safe to clear | `docs/workflow-lifecycle.md` | Prompts and answers, state line with key, Run Yourself, Clearing, Resuming, one worked example | The ledger schema and agent scheduling |
| Which agent does what, on which model, with which tools; what the pack does in git; the memory layout | `docs/architecture.md` | Agents table, Mode 1/2 as the user experiences them, Git Work, Memory layout | Brief tokens, report caps, `ESCALATE` fields, commit routing (AR-1 to AR-6) |
| Install, update, switch model or provider, Codex, migrate, fix an install | `docs/deploy.md` | The runbook, API Providers, Codex, Migrate, Exit Codes, Notes For Claude | Routing Check, version-string internals, launcher dispatch internals (DP-3, DP-4, DP-9); README should stop duplicating the consent text and command lists and link instead |
| Keep memory out of the repo | `docs/local-memory.md` | As is, with LM-1 fixed | Nothing |
| Why is it built this way; what does that mean for me | `docs/context-engineering.md` | The essay; a new "What this means for you" | Tool lists and word counts (CE-4 to CE-8) |

README Documentation list in reading order, each with a "read this when": lifecycle (before your first multi-session task), architecture (when you want to know who did what), deploy (when installing on another machine, switching provider, or something broke), local-memory (when the repo cannot hold the store), context-engineering (when you wonder why it works this way).

## Accuracy check

Discrepancies found are listed per file above: LM-1 (blocking), DP-1, DP-2, DP-7, RM-4, WL-15 (should-fix), DP-12, DP-13, LM-4, WL-16, WL-17, RM-10, RM-12 (nit). Claims verified correct against the pack and `deploy`, which a reader might doubt:

- The `Session state:` line and its "not safe" variant match `close-out` SKILL.md step 5 and `supervisor.md:113-115` word for word; `/close-out [retry]` and `/pick-up [<plan path>]` behave as described (stop if a plan is open, ten-line report, three next-step proposals).
- `not stored: no project store here; say *remember* to keep it` matches project-memory SKILL.md exactly.
- Residue ledger location, git exclusion, `remove`/`check` fields, `failed:` mark, and teardown timing match the residue skill.
- `chore(memory): <name>: <what>`, never push or pull, and `executor` re-creating the symlinks match `external-store.md`; the curator's externalize hint and `info/exclude` (never `.gitignore`) match curator-procedures.md.
- Memory root precedence, `--root`/`--name`/`[DIR]`, default name, `status` exit 1, the residue `.gitignore`, the README refusal and the "tracked" repair match `deploy:2100-2380`.
- All four presets (URLs, ALCF helper, Argo `echo NAME`, the `ANL username` prompt, tier defaults, `CLAUDE_CODE_AUTO_MODE_SERVER=0`), the picker prompts and the `--global` refusal of provider flags match `deploy:66-82, 1011-1016`.
- Codex defaults (`gpt-6.1-sol`, `high`), the 540 s timeout, the probe output, the consent text and `status` fields match `codex-critic`; `doctor` always prints `critic backend:`.
- Every quoted Troubleshooting message in README L267-274 exists in `deploy`; the minimum Claude version is 2.1.293 (`deploy:48`). The CHANGELOG v9 claims check out (14 live routing cases, a static scope test).

Not verified: "a numbered list, each with its best guess" (lifecycle L25; `planner.md:73` says "a recommended answer each", no pack file fixes a numbered format); "Waiting on `fixer`" (L21) is illustrative; runtime-only behaviour (live providers, symlink edge cases, `uninstall --all` text). Outside the docs: `./deploy update --help` says "Shallow-clone the branch" but the code clones in full for branches other than `main`; deploy.md L114 is right and the help text is not.

## Prioritised change list

| # | File | Effort | Resolves |
|---|---|---|---|
| 1 | docs/local-memory.md | S | LM-1 (blocking): rewrite "Both exist" and "Same-name projects" so no repair deletes another project's store |
| 2 | docs/workflow-lifecycle.md | M | WL-1, WL-3, WL-4, WL-5, WL-6, WL-7, WL-8: sizes table, state-line key, ledger paragraph, clearing list and resuming in user terms; define program/booked once |
| 3 | docs/workflow-lifecycle.md | S | WL-9: one worked example of a medium task |
| 4 | docs/architecture.md | M | AR-1 to AR-7: strip caps, `Review:`/`Path:` tokens, `ESCALATE` fields and commit routing; define residue at L33; split the Memory paragraph |
| 5 | docs/deploy.md | S | DP-1, DP-2, DP-7, DP-12, DP-13: the five accuracy fixes |
| 6 | docs/deploy.md | M | DP-3, DP-4, DP-9, DP-11, DP-14: move Routing Check to a contributor section, cut version-string and launcher internals, add Exit Codes |
| 7 | docs/deploy.md | S | DP-5, DP-6, DP-8, DP-10: Argo steps, permission-rule paragraph, Fable sentence, memory rationale |
| 8 | README.md | S | RM-1, RM-2, RM-3, RM-4: two memory bullets, provider paragraph placement, `memory` in the layout line |
| 9 | README.md | S | RM-11 plus the glossary: Documentation list in reading order with "read this when"; an eight-line Terms block |
| 10 | docs/workflow-lifecycle.md | S | WL-2, WL-10, WL-15, WL-16, WL-17: close-out sentence, maintainer note out, one-off definition |
| 11 | docs/context-engineering.md | S | CE-1, CE-2: enforcement paragraph, "contract time" |
| 12 | docs/local-memory.md, README.md | S | LM-2 to LM-7, RM-5 to RM-10, RM-12: agent names out of user sentences; small accuracy nits |
| 13 | CHANGELOG.md | S | CL-1 |
| 14 | docs/context-engineering.md, docs/deploy.md, docs/workflow-lifecycle.md, docs/architecture.md | S | Remaining nits: CE-3, CE-4, CE-6 to CE-8, DP-15, DP-16, WL-11 to WL-14, AR-8 to AR-10 |

Items 1 and 5 can land first as a pure accuracy pass; items 2 to 4 are the audience rewrite the user asked about; 6 to 14 are cleanup. Every item is a docs change; none alters pack behaviour.

## Open questions

1. Why does the Argo preset export `CLAUDE_CODE_AUTO_MODE_SERVER=0` (`deploy:79`)? Neither `deploy` nor `docs/deploy.md` says; DP-5 needs the reason in one clause.
2. Two `deploy` strings repeat what the docs get wrong, outside this audit's scope and worth a separate ticket: `./deploy update --help` says "Shallow-clone the branch" while the code clones in full for non-`main` branches (deploy.md L114 is right); and the `both exist` error (`deploy:2282`) gives the same "move or remove one of them" advice that LM-1 flags, without mentioning the same-name case or `--name`.
