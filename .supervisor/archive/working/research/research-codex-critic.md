# Research: Codex CLI as the pack's critic

Scope: evidence for an optional, install-time-selectable mode in which the pack's `critic` runs on
the OpenAI Codex CLI (`gpt-6.1-sol` or astra), with `scope-critic` possibly left on Claude. This
file lays out facts and options. It proposes no single design and contains no plan.

Context: worktree `feat/codex-critic` at `baab586` (v5.1), researched 2026-10-24, codex-cli 0.164.0,
Claude Code 2.1.310. Repo paths are relative to the worktree root. Raw transcripts are in the
session scratchpad (see the Appendix); they are ephemeral, and every load-bearing result is copied here.

Labels: **[V]** verified by reading the file or running the command. **[D]** taken from vendor
docs. **[I]** inference, not verified.

## Summary

- [V] Codex can be driven non-interactively from a Claude subagent's Bash with no TTY: `codex exec`
  with the prompt on stdin, `-s read-only`, `--ephemeral`, `--ignore-user-config`, `-o <file>` for
  the final message, and optional `--json` for a JSONL event stream. Four review runs each took
  16-18 s and returned rc 0.
- [V] Model IDs on this account are `gpt-6.1-sol` (the current config default) and `gpt-6-astra`.
  "astra" alone is not an ID.
- [V] Both models reproduced the critic output block exactly (VERDICT, ROUND, 6-column table,
  VALIDATION, NOTES, no preamble), with the instructions passed either through
  `-c model_instructions_file=<abs>` or inlined in the prompt. The test target had no real defects,
  so every run returned PASS with an empty table. In a clean seeded-defect test (B7; high effort,
  36-57 s, 92-95k input tokens) each model scored 2.5 of 3 with no false positives and ignored
  the red herring. Both caught the correctness and convention defects. Neither recognised the
  bloat as scope creep, and astra under-rated the correctness defect as SHOULD. This is one small
  sample.
- [V] Codex's own read-only Seatbelt sandbox blocked writes and network, and git reads still
  worked. No extra sandbox was needed in this environment. Isolation from the user's
  `~/.codex/config.toml` is one flag (`--ignore-user-config`), and auth still works through it.
- [V] The pack has no hooks, no permission allowlists, no `bin/`, and no variant-file mechanism.
  `deploy` copies `pack/agents/*.md` byte for byte. Lint tests pin `model:` to Anthropic aliases
  and let leads dispatch only `critic` and `scope-critic` as reviewers.
- [I] The seam that changes the least is the `critic` subagent itself. Keep its name and output
  contract, and have it run `codex exec` through a pack-shipped script. Leads and `scope-critic`
  then need no change. Section C compares this with the other surfaces.

## A. Critic plumbing in the pack

### A1. Dispatch sites, inputs, outputs

Dispatch sites [V]:
- `pack/skills/lead-loop/SKILL.md:51-59` defines review step 4. The lead dispatches `critic` with
  the contract, the artifact location (paths, a draft path, or a diff file path), the domain
  (research | plan | code | prose | agent-definition), the round, the suppression list, and either
  the convention and draft-state paths (prose) or the cited memory entry paths. `scope-critic`
  runs after `critic`, never in parallel with it.
- `lead-loop/SKILL.md:25` says the contract is passed verbatim. `:62-68`: from round 2 on, the
  reviewers get a `diff -u` file in the scratchpad plus the prior findings with dispositions.
  `:72-84`: the decide table combines the critic severity with the scope-critic ruling. `:81`: a
  `needs user:` finding stops the loop. `:95`: a stalemate is matched by "same location and claim".
  `:100-104`: the review depth is `full`, `light` or `none`.
- Lead call sites:
  - `pack/agents/researcher.md:36`: domain `research`.
  - `planner.md:39,57`: domain `plan`, dispatched with `model: fable` and a first `light` pass.
  - `executor.md:64`: domain `code`, or `agent-definition` for agent and skill files.
  - `writer.md:37,45-56`: domain `prose`, including a review-only path.
- Ad-hoc review: `pack/agents/supervisor.md:52-54`. Supervisor has no Bash, so `clerk` first
  writes the diff to a file and supervisor then dispatches `critic` and `scope-critic`.
- `curator` and `clerk` never dispatch the critic.

Critic inputs and output [V]:

| Item | Evidence |
|---|---|
| Inputs: contract (else the request), artifact location, domain, round, suppression list | `pack/agents/critic.md:14-18` |
| Inputs: convention and draft-state paths (prose) or memory entry paths; round 2+ diff and prior findings | `critic.md:19-22` |
| Reads `REVIEW.md` at the repo root and in changed directories on its own | `critic.md:34-36` |
| Output: `VERDICT: PASS \| REVISE`, `ROUND: <n>`, table `ID \| Severity \| Location \| Finding \| Evidence \| Minimal fix` with IDs `C1..` | `critic.md:69-79` |
| Severity is BLOCKING, SHOULD or NIT; choose the lower level when unsure | `critic.md:57-62` |
| At most 12 findings, at most 3 NITs; PASS means no BLOCKING finding; no preamble | `critic.md:66,82-83` |
| `needs user:` is defined only for prose | `science-writing-style/SKILL.md:128-134` |

What `scope-critic` consumes [V]:
- Its inputs are the request, the contract, the artifact location (a diff file for code, because
  it has no Bash) and the critic's findings (`pack/agents/scope-critic.md:14-17`). It reads the
  artifact itself (`:19`).
- It rules per finding ID: a table `| Finding | Ruling | Reason | Minimal fix if KEEP |` with KEEP,
  DOWNGRADE or DROP (`:24-27,58-60`). It also returns `CUTS:` entries `S1..` (`:53,63`),
  `VERDICT: LEAN | TRIM` (`:56`) and a `NET:` line (`:65`).
- [I] A replacement critic must therefore keep the `C<n>` IDs and the table columns. Otherwise the
  scope-critic rulings and the lead's decide table do not map.

### A2. The critic definition and its Claude Code dependencies

- Frontmatter [V] (`critic.md:1-7`): `model: opus`, `disallowedTools: Write, Edit, NotebookEdit,
  Agent`. It preloads no skills and inherits Bash, Read, Grep, Glob and the web tools. Bash is
  limited by prompt to read-only inspection and running existing tests or linters (`critic.md:55-56`).
- It loads skills on demand by domain [V] (`critic.md:34-47`). Sizes are from `wc`:

| Domain | Loads | Lines / bytes |
|---|---|---|
| all | `critic.md` body; `REVIEW.md` | 83 / 3996; 36 / 2162 |
| plan | `plan-writing/SKILL.md` (review checklist `:77-98`) | 98 / 5123 |
| prose | `science-writing-style/SKILL.md` (review `:111-142`) | 142 / 8222 |
| prose, slides | `presentation-style/SKILL.md` (checklist `:116-123`) | 123 / 6052 |
| prose with `.supervisor/` | `project-memory/references/writing.md`, plus `project-memory/SKILL.md` rules | 87 / 4703; 147 / 9333 |
| agent-definition | `agent-authoring/SKILL.md` (review `:63-70`) | 77 / 4393 |
| research, code | `critic.md` alone, plus the diff | about 4 KB |

  With `critic.md` and `REVIEW.md` included, the worst-case bundle is about 11.3 KB for plan,
  10.6 KB for agent-definition and up to 34.4 KB for prose (all five prose files). All of these fit easily in Codex context (272k-500k tokens).

Behaviours that a foreign CLI would not get for free:

| Behaviour | Where | Codex equivalent |
|---|---|---|
| Frontmatter `model`, `disallowedTools` | `critic.md:4-5` | `-m` and `-s read-only` flags |
| "Load the X skill" on demand | `critic.md:40-47` | none; inline the text, or give an absolute path to the deployed `SKILL.md` [I] |
| Memory discipline: read only the memory files named in the brief | `critic.md:51-52` | must be stated in the prompt, and the lead still passes the paths |
| Repo `CLAUDE.md` loaded implicitly | Claude Code behaviour | not read: Codex reads `AGENTS.md` only, unless `project_doc_fallback_filenames=["CLAUDE.md"]` is set (B4) |
| Per-dispatch model (planner passes `model: fable`) | `planner.md:57` | needs its own mapping to a Codex model and effort |
| Isolation, parallel fan-out, return to the lead | Agent tool | the script prints the block on stdout; parallel runs worked (B6) |
| Read, Grep, Bash for verification | `critic.md:53-56` | Codex runs `rg`, `nl`, `sed` and `find` itself (B6) |

### A3. How `deploy` works, and what the tests enforce

- Subcommands [V] (`deploy:1637-1701`): install, status, list, uninstall, update, migrate, doctor.
  Install flags: `--tag --target --global --prefix --source --dry-run --yes --overwrite-local
  --no-default-agent --force-default-agent --base-url --token-file --token`. `--fable-is-opus` is
  not an install flag; the launcher parses it at run time (`deploy:84`).
- Copying [V]:
  - `collect_source` (`deploy:322-394`) walks only `agents/*.md` and `skills/*/**` and checks that
    each frontmatter `name` equals the file stem (`:341-346`). Anything else in `pack/`, such as a
    `pack/bin/`, is ignored.
  - Files are copied byte for byte (`data = src.read_bytes()`, `deploy:835`). `atomic_copy` keeps the mode bits
    (`deploy:161-162`).
  - Precedent for shipped executables: `pack/skills/project-backup/scripts/backup.sh` (0755) lands
    at `<target>/skills/project-backup/scripts/`. It is not put on PATH.
- Models [V]: each agent carries a frontmatter alias, for example `critic.md:4` `model: opus`. The
  launcher (`launcher_text`, `deploy:79-117`) exports `CLAUDE_CONFIG_DIR` (`:101`) and exports
  `ANTHROPIC_DEFAULT_FABLE_MODEL` only with `--fable-is-opus` (`:56,107`), then runs
  `exec claude "$@"`. `--global` installs get no launcher.
- Persisted options [V]:
  - The manifest (`deploy:918-933`) has no field for user options or variants.
  - `replay_install` (`deploy:1238-1246`) passes only `--source`, the selection, `--prefix`,
    `--no-default-agent` and `--dry-run`. The base URL persists differently: install reads it back
    from the manifest (`deploy:814`), and the token is detected by file existence (`deploy:947`).
    A new install mode could follow the base-URL pattern: a manifest field, plus docs and tests in
    `tests/test_deploy.py`.
- Settings [V]: `plan_settings` and `plan_attribution` (`deploy:572-637`) write only the `agent`
  key and the `attribution` keys. A sandbox's first install seeds `settings.json` from `~/.claude`
  (`SEED`, `deploy:49`). No existing mechanism selects between install-time variants of an agent
  file.
- Lint (`tests/test_pack_lint.py`) [V]:
  - Every `pack/agents/*.md` must have `name == stem`, and `model` must be in `MODELS` (`:17`,
    Anthropic aliases, plus `claude-*` IDs per the worker reading). A Codex model string in
    `model:` fails.
  - Every agent needs a matching row in the agent-authoring Tiers table, and its body must fit the
    tier word cap (Review tier: 600 words).
  - `TIER_TOOLS` (`:25`) requires `critic` to list `Write, Edit` in `disallowedTools`.
  - `test_leads_dispatch_only_own_workers` (`:158`): leads may name only their own worker,
    `critic` and `scope-critic`. A `critic-codex` subagent type in a lead would fail this test.
  - Body lines may be at most 100 characters.
  - No test checks inventory sync with `docs/architecture.md`; that is a rule only.
    `tests/test_version.py` is skipped off `main`.

### A4. External CLIs, hooks, permissions

- [V] Agents already shell out in plain prose with backticked commands. Examples: git
  (`git-ops.md:18-26`, `executor.md:50`), `python3 -m py_compile` (`clerk.md:24`), conda, uv and
  pip (`python-env/SKILL.md:13,26-28`), and the bundled `backup.sh`. No agent calls `gh` or any
  third-party AI CLI.
- [V] There are no hooks, no `permissions` allow or deny lists, and no Claude Code `sandbox`
  settings anywhere in `pack/` or written by `deploy`.
- `docs/architecture.md:106` explains why a `permissions.deny` rule was not used: "would also
  apply to plain sessions". There is no precedent for a Bash allowlist entry.
- Memory constraints (validated 2026-10-24):
  - `decisions/2026-10-22-installs-never-need-the-source-checkout.md`: any script must ship in the
    install.
  - `decisions/2026-10-23-fable-is-default-opus-is-opt-in.md`: an install-time rewrite was rejected
    for model choice.

## B. Codex CLI on this machine

### B1. Install and auth [V]

- `codex --version` gives `codex-cli 0.164.0`. `/Users/sjoosten/.local/bin/codex` is a symlink
  into `~/.codex/packages/standalone/`.
- `codex login status` gives `Logged in using ChatGPT`. `~/.codex/auth.json` has
  `auth_mode: "chatgpt"`; only key names were read. `CODEX_HOME` is unset, so the default is
  `~/.codex`.
- `~/.codex/config.toml` (mode 600) sets `model="gpt-6.1-sol"` and `model_reasoning_effort="low"`,
  plus plugins, an MCP server, a notify hook and trust entries. `--ignore-user-config` drops all of
  these (B4).

### B2. Non-interactive mode

All from `codex exec --help` [V] unless marked.
- Usage: `codex exec [OPTIONS] [PROMPT]`. When the prompt is `-` or omitted, it is read from stdin.
  A piped stdin plus a prompt argument is appended as a `<stdin>` block.
- Flags:
  - `-m MODEL`, `-C/--cd DIR`, `-s read-only|workspace-write|danger-full-access`.
  - `-c key=value` (TOML-parsed), `--enable/--disable FEATURE`, `--strict-config`, `-p PROFILE`.
  - `--ephemeral` (no session files), `--skip-git-repo-check`, `--ignore-user-config` (auth still
    from `CODEX_HOME`), `--ignore-rules`.
  - `--json` (JSONL on stdout), `-o/--output-last-message FILE`, `--output-schema FILE`,
    `--color never`, `--add-dir`.
  - Subcommand `exec review` (`--uncommitted`, `--base`, `--commit`) is a built-in code review with
    its own output format.
- Approval and sandbox [V, D]: `-a` exists only on the interactive command. In exec, the run
  header showed `approval: never` and `sandbox: read-only`. The docs say exec defaults to
  read-only and that `--full-auto` is no longer supported
  (learn.chatgpt.com/docs/non-interactive-mode).
- Streams [V]: without `--json`, stdout carries only the final message, the same text `-o` writes.
  Stderr carries a header (version, workdir, model, sandbox, effort, session id), the echoed prompt
  and the transcript.
- `--json` events [V]: `thread.started`, `turn.started`, `item.started`/`item.completed`
  (`command_execution` with `command` and `exit_code`; `agent_message`; `error`), then
  `turn.completed` with `usage` or `turn.failed`.
- Exit codes [V]: rc 0 on success. A bad model with `--json` gave rc 1 after 3 s, empty stderr, and
  no `-o` file. The cause was in the JSON event stream: `"code":"model_not_found" ... not supported
  when using Codex with a ChatGPT account`. [I] Failure output without `--json` was not tested.
- Network: exec has no network flag; the read-only sandbox blocks network (B5). `CODEX_API_KEY`
  overrides the key for one run [D].

### B3. Models

- There is no model-list subcommand. `~/.codex/models_cache.json` (refreshed by every run) lists [V]:

| ID | Default effort | Context | Note |
|---|---|---|---|
| `gpt-6.1-sol` | low | 500k | user config default |
| `gpt-6-astra` | medium | 272k | the "astra" candidate |

- Effort is set with `-c model_reasoning_effort=...`. Levels: low, medium, high, xhigh, max and
  ultra for sol and astra.
- The cache has no cost or latency data. With ChatGPT auth, usage counts against the ChatGPT plan
  rather than API billing [I]. Measured token use is in B6.

### B4. Instruction mechanisms

- AGENTS.md discovery [D] (learn.chatgpt.com/docs/agent-configuration/agents-md):
  - Global: `$CODEX_HOME/AGENTS.override.md`, else `AGENTS.md`.
  - Project: one file per directory, walking from the git root down to the cwd, concatenated, with
    a cap of `project_doc_max_bytes` (default 32768).
  - The repo's `CLAUDE.md` is ignored unless `project_doc_fallback_filenames=["CLAUDE.md"]` is set.
  - [V] Every live run searched for AGENTS.md files up the tree, above the repo root.
- Config keys found in the binary [V]: `model_instructions_file`, `base_instructions`,
  `developer_instructions`, `project_doc_fallback_filenames`, `skills.include_instructions`,
  `features.*`. `experimental_instructions_file` is absent (0 hits).
- [V] `-c model_instructions_file="<abs path>"` was accepted per call with no error. Its output
  matched the inlined-prompt runs, so the runs do **not** prove it replaces the base prompt; a
  marker-string test would settle it. Inlining the instructions in the prompt is a working fallback.
- Isolation [V]: `--ignore-user-config` drops the user's model, effort, personality, plugins, MCP
  server, notify hook and trust list for that run, and auth still works. A private `CODEX_HOME`
  would need a copy of `auth.json` (a secret), so it is the worse choice. Per-call disabling of the
  user's skills and MCP beyond this flag was not tested.
- [I] Writing a temporary `AGENTS.md` into the repo would leave a stray file in the user's tree.

### B5. Sandbox

- [V] `codex sandbox -- /bin/sh -c ...` uses macOS Seatbelt:
  - `touch /tmp/x` gave `Operation not permitted`.
  - `curl https://example.com` returned 000, rc 6 (network blocked).
  - `git log -1 --oneline` worked; xcrun cache warnings went to stderr.
- [V] This session's Bash is not inside Claude Code's sandbox. `sandbox-exec ... sandbox-exec ...
  /usr/bin/true` returned rc 0, and the Codex runs worked from subagent Bash with no TTY.
- Model commands ran as `/bin/zsh -lc '...'`, so the user's login profile is loaded [V].
- [D] If the user enables Claude Code's sandbox (`sandbox` settings, Seatbelt on macOS), the network
  allowlist starts empty, so OpenAI hosts would be blocked unless they are listed or the command is
  in `excludedCommands`. Whether Seatbelt allows Codex's nested `sandbox-exec` there is
  **unconfirmed**; no matching GitHub issue was found.
- [V] Even with `--ephemeral`, runs write `~/.codex/logs_2.sqlite` and refresh `models_cache.json`.
  No new session files appeared.
- [I] Guidance: Codex's own `-s read-only` is a sufficient sandbox for a reviewer. Pair it with
  `--ignore-user-config`, `--ephemeral` and an explicit `-m` and effort. A separate Codex sandbox
  is not needed. The open risk is a user who also turns on Claude Code's sandbox.

### B6. Live test

- Target: domain agent-definition, round 1. Review `pack/agents/scope-critic.md` for one defect
  class: references to non-existent files, skills, tools or sections, or contradictions with
  `critic.md`'s output format.
- Instructions: a condensed `critic.md` contract.
- Common flags: `codex exec -s read-only --ephemeral --ignore-user-config --skip-git-repo-check
  --color never -C <worktree> -m <model> -c model_reasoning_effort="medium" -o <out> - < prompt.md`.
- Five invocations in total; the budget was at most two per model plus one probe.

| Run | Model | Mode | Wall | rc | `-o` size | Format | Result | Cmds run | Tokens in / cached / out |
|---|---|---|---|---|---|---|---|---|---|
| sol1 | gpt-6.1-sol | `--json`, instructions file | 17 s | 0 | 485 B | exact | PASS, 0 findings | 2 | 43727 / 27520 / 436 |
| astra1 | gpt-6-astra | `--json`, instructions file | 16 s | 0 | 493 B | exact | PASS, 0 findings | 2 | 41652 / 33152 / 327 |
| sol2 | gpt-6.1-sol | instructions inlined, text output | 18 s | 0 | 532 B | exact | PASS, 0 findings | 3 (from stderr) | not captured |
| astra2 | gpt-6-astra | `--json`, instructions inlined | 18 s | 0 | 565 B | exact | PASS, 0 findings | 4 | 77385 / 66816 / 366 |
| fail | does-not-exist | `--json` | 3 s | 1 | none | n/a | `model_not_found` | 0 | n/a |

Excerpt of `sol1` output [V]:

```
VERDICT: PASS
ROUND: 1

| ID | Severity | Location | Finding | Evidence | Minimal fix |
|----|----------|----------|---------|----------|-------------|

VALIDATION: Read numbered scope-critic.md, critic.md, agent-authoring/SKILL.md, and REVIEW.md; ...
NOTES: scope-critic's separate ruling format does not contradict critic's findings format. ...
```

Observations:
- The verdict is plausible: `scope-critic.md` names no missing files.
- All commands were read-only (`ls`, `find`, `rg`, `nl -ba`, `sed -n`, `cat REVIEW.md`). There
  were no `file_change` items, sandbox denials, approval requests or network attempts. The
  worktree stayed clean.
- Both models read `REVIEW.md` on their own; the condensed instructions had no `REVIEW.md` rule.
- There were no hallucinated paths, but zero findings gave nothing to hallucinate.
- Not tested:
  - the 12-finding and 3-NIT caps and round 2 inputs (B7 covers non-empty tables and finding
    quality on one small file);
  - large diffs (B7 measured high effort on a small file at 36-57 s);
  - pickup of `CLAUDE.md` through the fallback names;
  - `--output-schema`;
  - a marker test that proves `model_instructions_file` replaces the base prompt.

  These are left out because the run budget is spent.

### B7. Seeded-defect test

- Setup: a copy of `pack/agents/scope-critic.md` with three planted defects and one red herring.
  The answer key was written before any run. The prompt inlined the `critic.md` body, `REVIEW.md`
  and `agent-authoring/SKILL.md`, plus the brief: domain agent-definition, round 1, and the
  contract "no behaviour changes beyond the baseline".
- Flags as in B6, except `-C` points at a directory holding only `pack/agents/scope-critic.md`
  (confirmed with `ls -R`) and effort is `high`. One run per model, run in parallel.
- A first attempt was discarded as contaminated: `seed.diff` sat inside `-C`, and both models read
  it. This table is from the clean rerun, which used the identical prompt and flags.

| Key | Line | Class | Expected | gpt-6.1-sol | gpt-6-astra |
|---|---|---|---|---|---|
| D1 verdict rule inverted (`TRIM` = no cuts) | 76-77 | correctness | BLOCKING | found, BLOCKING | found, SHOULD (under-rated) |
| D2 `Bash` removed from `disallowedTools` (Tiers table: no Bash) | 5 | agent-authoring | SHOULD or BLOCKING | found, BLOCKING | found, BLOCKING |
| D3 added "Independent Verification" section (re-run tests, caveats) | 51-57 | scope creep | SHOULD in the key; BLOCKING is also correct under the contract | partial: cited `:53` inside the D2 finding as needing Bash | partial: own finding at `:53`, BLOCKING, framed as a tool conflict |
| R1 "Prefer few" changed to "Go for few" | 49 | red herring | not reported | not flagged | not flagged |

| | gpt-6.1-sol | gpt-6-astra |
|---|---|---|
| Score | 2.5/3, 0 false positives | 2.5/3, 0 false positives, 1 severity miss |
| Wall / rc | 57 s / 0 | 36 s / 0 |
| Tokens in / cached / out (reasoning) | 92103 / 79616 / 1432 (716) | 95340 / 83840 / 1199 (168) |
| Block | well-formed, REVISE, 2 findings | well-formed, REVISE, 3 findings |
| Commands | 5, all inside `-C`; probes of absent `docs/`, `tests/` and git returned rc 2 or 128 | 3, all inside `-C`; reported that one heredoc command was denied by the sandbox (not in the event stream) |

- Neither model recognised D3 as bloat or scope creep. Both caught the section only because it
  needs Bash, and their fixes remove the re-run rule, not the caveats or the whole section. A pack
  critic's scope review is done by `scope-critic`, which stays on Claude in every option.
- Both honestly reported that the baseline, the tests and `architecture.md` were unavailable.
  Neither attempted a write or network access, nor invented a path in its findings.
- Raw files: `scratchpad/seeded-clean-out/` (`prompt.md`, plus `<model>.out.txt`,
  `.stdout.jsonl`, `.stderr.txt` and `.meta.txt` for each model) and `scratchpad/keys/answer-key.md`.

## C. Integration surfaces (compared, not chosen)

Shared building block [I]: a wrapper script shipped in the pack, which today means
`pack/skills/<skill>/scripts/`, since `pack/bin` would need a `collect_source` change. It would:
- build the prompt from the brief, `critic.md`'s output contract and the domain skill text or paths;
- run `codex exec` with the B6 flags, choosing the model and effort from the install choice;
- check rc, that the `-o` file is non-empty, and that it starts with `VERDICT:` and carries the
  table header;
- print the block, or print a failure marker.

It finds its own files through `${CLAUDE_CONFIG_DIR:-$HOME/.claude}` (the launcher exports
`CLAUDE_CONFIG_DIR`, `deploy:101`; `--global` has no launcher).

| | C1 critic agent relays to the script | C2 leads call the script | C3 hook swaps the critic | C4a deploy-time file swap | C4b runtime switch |
|---|---|---|---|---|---|
| What changes in the pack | The `critic` body gains a Codex path; the script is new | `lead-loop` section 4 and the four leads gain a Bash path; supervisor needs `clerk` to run it | A hook script, plus `deploy` writing `hooks` into `settings.json`; probably a relay agent | `collect_source`, a manifest field, `replay_install`, docs and tests; a second critic file kept outside the lint glob or with the lint test extended | The `critic` body reads a switch: a launcher env var or a marker file written by `deploy` |
| Identical for leads and scope-critic | Yes: same `subagent_type`, same block | No: leads handle the output and its failures | Leads yes; the rewritten type must still produce the block | Yes | Yes |
| Model cost | One Claude turn relays. Frontmatter is fixed at `opus`, so a cheap relay needs a separate file or a per-dispatch `model` | No Claude critic turn | PreToolUse can rewrite `subagent_type` or `model` (`updatedInput`) but cannot return a result; PostToolUse `updatedToolOutput` runs after the Claude critic has already run | As C1, but the relay file can declare `haiku` or `sonnet` | As C1 (`opus` unless the leads pass `model`) |
| Failure modes | Relay may paraphrase the block; Bash 2 min default timeout (max 10 min); permission prompt for each `codex` call | Lead context and Bash block during review; logic duplicated in five places; supervisor has no Bash | Hook behaviour for config-dir agents and the Agent output shape are unconfirmed; conflicts with the no-hooks stance | Install-time variant resembles the rejected install-time rewrite; `update` must replay the mode | Switch missing under `--global` unless it is a file; a mode flipped without reinstalling |
| Install-time selectable | Via C4a or C4b | Via a switch read by the leads | Via `deploy` writing or omitting the hook | Yes, natively | Yes, if `deploy` writes the env var into the launcher or a marker file |
| Fallback when Codex fails | The relay reviews itself as the Claude critic, or returns NOTES with the failure | The lead dispatches the Claude critic | Hook does nothing and the normal critic runs | The relay must carry a Claude fallback or fail loudly | Same body holds both paths, so the Claude review is the natural fallback |

Cross-cutting facts:
- Domain skill content [I]. Codex's read-only sandbox can read files, so the script can pass
  absolute paths to `<config>/skills/<skill>/SKILL.md` and `<config>/agents/critic.md` and tell
  Codex to read the review sections. Alternatively it can inline them (at most about 34 KB) or use
  `model_instructions_file`. Reading files outside `-C` was not tested.
  - Repo rules in `CLAUDE.md` are invisible to Codex unless the script adds
    `-c 'project_doc_fallback_filenames=["CLAUDE.md"]'` (B4).
- scope-critic [V, I]. It needs only the block with `C<n>` IDs (A1), so any surface that emits the
  exact block leaves it unchanged. Keeping it on Claude also keeps a Claude check over a GPT
  critic. `lead-loop:72-76` assumes both reviews exist.
- Fallback triggers [V]:
  - `command -v codex` fails;
  - `codex login status` does not report a login;
  - rc is non-zero;
  - the `-o` file is missing or empty;
  - the output does not start with `VERDICT:`.

  The bad-model probe showed that rc plus the missing `-o` file is enough to detect failure. With
  `--json` the cause is in the event stream; [I] non-JSON failure output was not tested.
- Permissions [D]. Each `codex` or script call hits Claude Code's normal Bash prompt unless
  `settings.json` carries an allow rule such as `Bash(codex exec *)` or the script path. A leading
  env assignment or a compound command defeats the rule. `deploy` writes no permissions today
  (A4).
- Time [V, D]. 16-18 s for a small file at medium effort. Larger diffs or high effort may pass the
  Bash 120 s default, so the call needs an explicit timeout of up to 600 s or `run_in_background`.
- Default Codex versus a supplied definition [V, I]. Plain `codex exec` has no knowledge of the
  findings block, severities, caps or domain checklists, and `exec review` has its own format. The
  critic contract must therefore be supplied. A Codex-side sandbox, skills or MCP setup is not
  needed.

## Open questions for the user

1. Which model per domain or effort: `gpt-6.1-sol` and `gpt-6-astra` for all domains, or one per
   domain (for example astra for prose)? Should planner's `model: fable` dispatch map to a cheaper
   effort?
2. Should `scope-critic` stay on Claude? Keeping it there keeps a cross-family check and needs no
   change.
3. Is an install-time variant of an agent file acceptable, given that the Fable decision rejected
   an install-time rewrite for model choice? Or should the mode be a runtime switch that `deploy`
   writes?
4. Is a `deploy`-managed `permissions.allow` entry for the Codex call acceptable, or should every
   call prompt?
5. When Codex is missing, logged out or failing, should the review silently fall back to the Claude
   critic or stop and report?
6. Should prose reviews (which need `needs user:` and the style hard floors) also go to Codex, or
   only code, plan, research and agent-definition?
7. B7 is one small sample: 2.5 of 3 per model, with no bloat detection. Is that enough to decide,
   or should a larger comparison against the Claude critic (several files, both domains) come
   first?

## Appendix: raw files (session scratchpad, ephemeral)

All files are under
`/private/tmp/claude-502/-Users-sjoosten-Work-claude-agents/d680c213-ba80-4b74-a555-ac13820870b8/scratchpad/`:
- `codex-help/`: version, help, exec help, sandbox help, login status, features.
- `codex-runs/`: `critic-instructions.md`, `prompt.md`, `prompt-inlined.md`, `run.sh`, and for each
  run `<name>.cmd.txt`, `.meta.txt`, `.out.txt`, `.stdout.txt`, `.stderr.txt`. Also
  `codex-dir-before.txt` and `codex-dir-after.txt`.
