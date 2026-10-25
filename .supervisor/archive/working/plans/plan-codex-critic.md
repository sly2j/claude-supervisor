# Plan: Codex CLI as an opt-in critic backend

Branch `feat/codex-critic`, worktree `.claude/worktrees/codex-critic`. Research:
`.supervisor/working/research/research-codex-critic.md` (cited below as R, with its section ids).
Target release: next major (`X.0`, X raised by one) at squash-merge; the branch never touches
`VERSION`.

## Goal

Give the pack an optional, runtime-switchable mode in which the lead's critic step runs the OpenAI
Codex CLI (`gpt-6.1-sol` by default, `gpt-6-astra` selectable) instead of the Claude `critic`
subagent, with the Claude critic as the automatic fallback. `scope-critic` and the critic's review
content stay unchanged. Everything a user needs ships in the install: one script, one skill, three
`deploy` touches, one docs section.

Non-goals: changing `scope-critic`; changing what the critic checks; Codex-side MCP, skills or
AGENTS.md; a second sandbox around Codex; install-time pack variants; pushing or merging.

Expected change size: about 1,250 lines added, 20 changed: script about 350, `deploy` about 120,
tests about 500, docs about 150, pack prose about 50 (lead-loop, a new SKILL.md, supervisor and
clerk lines). This plan is about 440 lines.

## Approach

A pack-shipped Python script `skills/supervisor-config/scripts/codex-critic` owns four verbs:
`review`, `enable`, `disable`, `status`. Mode state is a JSON file `<config>/supervisor-config.json`
next to the install's `settings.json`; the script reads it on every call, so pack files stay
byte-identical across modes and the mode flips without a reinstall. At the critic step a lead runs
the script once per round via Bash; it prints either a validated findings block or `NO_CODEX`, on
which the lead dispatches `critic` exactly as today. `deploy critic ...`, the launcher and the
`/supervisor-config` skill are thin front doors onto the same verbs.

Rejected (R C): the `critic` agent relaying to Codex (one wasted Opus turn per review, relay may
paraphrase); a hook swapping the critic (hooks cannot return a result, and the pack has a no-hooks
stance); an install-time file swap (the Fable decision rejected install-time rewrites,
`.supervisor/memory/decisions/2026-10-23-fable-is-default-opus-is-opt-in.md`).

## Decisions

Binding user decisions from the brief (D1-D9) are restated only where this plan adds a detail.

1. **Script location and language.** `pack/skills/supervisor-config/scripts/codex-critic`,
   mode 0755, `#!/usr/bin/env python3`, stdlib only, Python 3.9 compatible (macOS
   `/usr/bin/python3`), like `deploy`. Precedent: `pack/skills/project-backup/scripts/backup.sh`;
   `collect_source` keys every file under `skills/<sk>` (`deploy:390`) and `atomic_copy` keeps the
   mode (`deploy:161`). Python, not sh, because the script parses JSON and edits `settings.json`.
2. **Config dir discovery.** The script derives the install dir from its own path:
   `os.path.abspath(__file__)` three parents up (`scripts` -> `supervisor-config` -> `skills` ->
   config). No `CLAUDE_CONFIG_DIR` dependence (absent under `--global`, and the memory decision
   `2026-10-22-install-target-comes-from-flags-only.md` keeps deploy off that variable). `abspath`,
   not `resolve`: the permission rule must equal the path Claude Code reports, which is the literal
   install path, not a symlink target.
3. **Mode file.** `<config>/supervisor-config.json`, shape:

   ```json
   {"critic": {"backend": "codex", "model": "gpt-6.1-sol", "effort": "high",
               "domains": {"prose": "claude", "plan": {"model": "gpt-6-astra", "effort": "xhigh"}}}}
   ```

   `domains` is optional; a value is `"claude"` (pin the domain to the Claude critic) or an object
   with `model` and/or `effort`. `enable [model]` writes `backend`, `model` and `effort: high`,
   keeping an existing `domains` map; `disable` deletes the `critic` key and removes the file when
   empty. The name is generic so later switches can share it. JSON because 3.9 has no `tomllib`.
4. **Permission entry.** `enable` appends `Bash(<abs script path> *)` to `permissions.allow` in
   `<config>/settings.json` (`~/.claude/settings.json` for `--global`), merging like
   `plan_settings` (`deploy:572`: copy the dict, touch one key, write atomically with a `.bak`).
   `disable` removes exactly that string. Rules match literal whole-command text with `*` for any
   text; `~` and variables are not expanded in Bash rules, so the rule carries the absolute path.
   Claude Code reloads `permissions` edits mid-session (settings docs, "When edits take effect"),
   so no restart is needed; the in-session `enable` itself runs before the rule exists and may cost
   one prompt. The whole script is allowed, not only `review`, so an in-session `disable` needs no
   prompt either; the user consented to the script as a whole.
5. **Brief transport.** Leads write the brief to a scratch file and pass `--brief FILE`.
   Reason: Claude Code splits a Bash command at newlines and at compound operators and matches
   each part against the allow rules (Claude Code permissions docs; R C), so a heredoc brief would
   defeat the rule and prompt every round. This refines D1 ("brief on stdin"); the content of the
   brief is unchanged.
6. **`review` interface.** `codex-critic review --domain <research|plan|code|prose|agent-definition>
   --round <n> --brief FILE [--diff FILE] [--cwd DIR] [--timeout SECS] [PATH ...]`. `--cwd`
   (default: the Bash cwd) becomes `-C`; `executor` passes its worktree there, because it runs its
   own commands from the main checkout with absolute paths (`pack/agents/executor.md:50`) and a
   `cd <wt> &&` prefix would be a compound command that defeats the allow rule. Positional paths
   are the artifact locations the lead would give `critic`; Codex reads them itself inside the
   read-only sandbox. `--diff` is inlined into the
   prompt because the diff lives in the scratchpad, outside `-C`, and reads outside `-C` are
   untested (R C, cross-cutting). Memory, convention and draft-state paths travel inside the brief,
   as today.
7. **Fallback contract.** Stdout is either the block or the single line `NO_CODEX`; the reason
   goes to stderr as `codex-critic: <reason>`; exit code 0 in both cases (usage errors exit 2 with
   argparse's message). Triggers (R C fallback list, plus D1): no mode file or `backend != codex`;
   domain pinned to `claude`; `codex` not on PATH; non-zero rc; timeout (default 540 s, below the
   lead's 600 s Bash cap, since an expired foreground Bash command is backgrounded, not killed);
   `-o` file missing or empty; block fails validation; `<config>/agents/critic.md` missing. The
   lead's rule is simpler still: anything that does not start with `VERDICT:` means "dispatch
   `critic`". `review` does not run `codex login status` (an auth failure already yields rc != 0);
   `enable`, `status` and `doctor` do.
8. **Prompt assembly** (D5), in this order: a fixed preamble of about 10 lines (you are the pack's
   critic running under Codex; the skill texts you would load follow; read only the memory files
   the brief names; output the block and nothing else); the body of `<config>/agents/critic.md`
   without frontmatter; `<cwd>/REVIEW.md` when present (Codex reads changed-directory `REVIEW.md`
   files itself, per the critic's rule at `critic.md:34-36`); domain files per R A2: plan ->
   `plan-writing/SKILL.md`; agent-definition -> `agent-authoring/SKILL.md`; prose ->
   `science-writing-style/SKILL.md`, `presentation-style/SKILL.md` and, when `<cwd>/.supervisor/`
   exists, `project-memory/references/writing.md`; research and code -> none; then the inlined
   diff under a `## Diff` heading; then the brief under `## Brief`. All files come from
   `<config>/skills/`, never from the source checkout. Prose always gets both style skills because
   the script cannot tell slides from documents; the critic applies the one that fits, as the
   Claude critic does.
9. **Codex flags** (D5, verified in R B6/B7): `codex exec -s read-only --ephemeral
   --ignore-user-config --skip-git-repo-check --color never -C <cwd> -m <model>
   -c model_reasoning_effort=<effort> -o <tmpfile> -` with the prompt on stdin, plus
   `-c 'project_doc_fallback_filenames=["CLAUDE.md"]'` so the repo's `CLAUDE.md` reaches Codex as
   it reaches the Claude critic (R B4; documented key, not live-tested: the live smoke run in Slice
   2 confirms it, and the executor drops it if Codex rejects it). No `--json`, no
   `model_instructions_file`.
10. **Block validation.** After stripping whitespace and one wrapping code fence: line 1 matches
    `VERDICT: (PASS|REVISE)`, line 2 `ROUND: <n>`, the header row
    `| ID | Severity | Location | Finding | Evidence | Minimal fix |` is present, one `VALIDATION:`
    and one `NOTES:` line follow, every finding row has six cells and a severity in
    {BLOCKING, SHOULD, NIT}, and the verdict agrees with the rows (REVISE iff a BLOCKING row). On
    success the script appends `backend: codex <model> <effort>` after the NOTES line(s) and prints
    the block.
11. **Probe once per task.** `lead-loop` step 1 gains one bullet: read
    `<config>/supervisor-config.json` with the Read tool, `<config>` being two levels above this
    skill's base directory (the `Base directory for this skill:` line that Claude Code prints for
    preloaded skills). If it
    names `critic.backend: codex`, step 4 runs the script each round; otherwise the task uses the
    Claude critic with no further checks. The script still re-reads the file on every call. A Read
    outside the working directory may prompt in default permission mode (docs: read-only tools are
    auto-allowed "within the working directory and additional directories"); whether it does is
    checked in Verification and recorded in the docs caveats. No permission entry is written for
    the probe: installs must not touch `permissions` unless the user opts in.
12. **Lead-loop and supervisor wording.** Step 4 item 1 gains the Codex branch (write brief file,
    run the script with `timeout: 600000`, use the block if it starts with `VERDICT:`, else
    dispatch `critic`); step 7 Validation names the engine (`critic: codex gpt-6.1-sol high` or
    `critic: claude (<fallback reason>)`). Per-dispatch `model:` hints (planner's `model: fable`,
    `planner.md:57`) do not reach the script: model and effort come from the mode file (a `plan`
    domain override is the knob for a cheaper pass), and the review depth travels in the brief as
    today. `supervisor.md:52-54`: `clerk` writes the diff and runs
    the script; supervisor dispatches `critic` only on `NO_CODEX`. `supervisor.md` has zero word
    headroom under the 1000-word lint cap, so the executor trims equivalent words in the same
    file. `clerk.md` (80 words headroom) gains one line naming the script path rule, because
    `clerk` is the one that must type it (it preloads `project-memory`, so it has a base directory
    line). Leads keep dispatching only `critic` and `scope-critic`; no new `subagent_type` string.
13. **Front doors.** `deploy critic <verb> [args] [--tag|--target|--global]` resolves the target
    like `status` and execs
    `[sys.executable, <target>/skills/supervisor-config/scripts/codex-critic, verb, *rest]`
    with inherited stdio, returning its rc; `DeployError` when the script is not installed. The
    launcher gets `critic` in `LAUNCHER_COMMANDS` (`deploy:57`), a help line
    (`:60`) and a `case` branch that `shift`s and execs the installed script directly (no deploy
    dependency, per `2026-10-22-installs-never-need-the-source-checkout.md`). The skill
    `supervisor-config` (`disable-model-invocation: true`, main thread, `argument-hint`) parses
    `$ARGUMENTS` (`critic codex [model]`, `critic claude`, `critic status`), asks consent with
    `AskUserQuestion` using the script's own consent text, then runs
    `"${CLAUDE_SKILL_DIR}/scripts/codex-critic" enable --yes [model]` itself when it has Bash and
    through `clerk` otherwise (the `supervisor` agent has no Bash). Not `context: fork`: subagents
    lack `AskUserQuestion`.
14. **Consent text** (printed by `enable`; `SKILL.md` carries the same text verbatim, since the
    `supervisor` main thread has no Bash to fetch it): Codex reviews spend the user's
    OpenAI/ChatGPT quota; the repository content under the current directory, the review brief and
    the diff are sent to OpenAI; one `permissions.allow` entry for the script is added to the
    named `settings.json`; Codex runs read-only and ephemeral. y/n on a TTY via a `confirm`-style
    check (`deploy:184`), `--yes` required otherwise.
15. **Lifecycle.** `install` prints one hint line after the Settings line (`deploy:961-969`) when
    `shutil.which("codex")`: Codex as critic is off, how to enable. `update` needs no code: the
    mode file is not in the manifest, so stale-file cleanup (`deploy:880`) never touches it,
    and `plan_settings` merges, so `permissions.allow` survives (`deploy:572`, test
    `tests/test_deploy.py:190`); a test pins this. `uninstall`: the sandbox branch `rmtree`s the
    target (`deploy:1163`), which covers both artefacts; the `--global` branch (`deploy:1178`)
    runs the installed script's `disable --yes` before removing files, when the script exists.
    `doctor` (`deploy:1495`, new check before the tally at `:1585`): one line stating the critic
    backend; when it is `codex`, FAIL rows for a missing binary or a failing `codex login status`
    (D2); nothing else, since `status` already reports the rule and the config.
16. **Model strings.** `enable` accepts any model string and defaults to `gpt-6.1-sol`; the docs
    name the two verified IDs (`gpt-6.1-sol`, `gpt-6-astra`; R B3). A wrong ID surfaces as
    `NO_CODEX` with `model_not_found` on stderr and in `doctor`, not as a hard error, because IDs
    are account-specific.
17. **Tests never call real Codex.** Script tests build a fake config dir and a stub `codex` on a
    private PATH, following `tests/test_deploy.py:56-83` (subprocess runner, whitelisted env, stub
    executables in `tmp/bin`). Line-length and word-cap lint already covers the new SKILL.md
    (`tests/test_pack_lint.py:174`); a new lint test covers `scripts/` files (exec bit, shebang,
    `py_compile` for Python).

## Outline

`pack/skills/supervisor-config/scripts/codex-critic` (new, about 350 lines)
- `main(argv) -> int`: argparse with sub-verbs `review`, `enable [model] [--yes]`,
  `disable [--yes]`, `status`.
- `config_dir() -> Path`; `load_mode(cfg) -> dict | None`; `save_mode(cfg, mode)`.
- `settings_path(cfg)`, `add_allow(cfg, rule)`, `remove_allow(cfg, rule)`: merge-style edits with
  `.bak`, modelled on `deploy:551-570`.
- `rule_for(script_path) -> str` returns `Bash(<abs> *)`.
- `resolve_model(mode, domain) -> ("claude", None, None) | ("codex", model, effort)`.
- `build_prompt(cfg, cwd, domain, brief, diff) -> str` per Decision 8.
- `run_codex(prompt, cwd, model, effort, timeout) -> (rc, out_text | None, stderr_tail)`.
- `validate_block(text) -> str | None` per Decision 10 (returns the normalised block).
- `fallback(reason) -> int`: prints `NO_CODEX`, stderr reason, returns 0.
- `codex_ok() -> (path | None, authenticated: bool)`: `shutil.which("codex")`; logged in iff
  `codex login status` exits 0 and its stdout contains `Logged in` (R B1 shows only that output).
- Gotcha: `-o` goes to a `tempfile` in the system temp dir, deleted afterwards; never write inside
  the repo (Codex's sandbox denies it anyway, R B5).

`deploy`
- `critic_cmd(args)`: `resolve_target(args)` (`:213`), script path check, `subprocess.call`.
- `build_parser` (`:1603`): `add_parser("critic")` with `common(sp, source=False)`, positional
  `verb` in {enable, disable, status}, `rest` as `argparse.REMAINDER`.
- `LAUNCHER_COMMANDS` (`:57`) += `"critic"`; `LAUNCHER_HELP` (`:60`) one line; `launcher_text`
  (`:79`, branch next to `update|uninstall|list|status)` at `:96`): `critic) shift; exec
  '<target>/skills/supervisor-config/scripts/codex-critic' "$@";;`.
- `install_cmd` summary block (`:961-969`): the hint.
- `uninstall_cmd` global branch (`:1178`): the `disable` call before the file loop.
- `doctor_cmd` (`:1495`): the check before `:1585`, in the `add(level, msg)` style of `:1576-1581`.

`pack/skills/lead-loop/SKILL.md` (127 lines, cap 300): step 1 bullet after the Memory bullet
(`:20-22`); step 4 item 1 (`:53-56`) gains the Codex branch; step 7 Validation line (`:118`).
`pack/agents/supervisor.md:52-54` and `pack/agents/clerk.md:20-21` per Decision 12.
`pack/skills/supervisor-config/SKILL.md` (new, under 60 lines): frontmatter per
`agent-authoring` (`name`, `description`, `disable-model-invocation: true`, `argument-hint`);
argument parsing like `pack/skills/meeting-summary/SKILL.md:12`; script path via
`${CLAUDE_SKILL_DIR}` like `pack/skills/project-backup/SKILL.md:18`.

Tests
- `tests/test_codex_critic.py` (new): fixture `cfg(tmp_path)` copies the script to
  `tmp/cfg/skills/supervisor-config/scripts/codex-critic` plus minimal `agents/critic.md`,
  `skills/plan-writing/SKILL.md`, `skills/agent-authoring/SKILL.md`; fixture `codex_stub(tmp_path)`
  writes `tmp/bin/codex` (sh) that records argv and stdin to files, answers `login status` with the
  rc in `tmp/stub/login_rc`, and on `exec` copies `tmp/stub/out.txt` to the `-o` path and exits
  with `tmp/stub/rc`; runner like `tests/test_deploy.py:56`. The repo-side cwd is a tmp dir holding
  `REVIEW.md` and a target file.
- `tests/test_deploy.py`: new tests near the install (`:107`), uninstall (`:365`), launcher
  (`:724-735`) and doctor (`:1837-1865`) groups, reusing their fixtures and stubs.
- `tests/test_pack_lint.py`: `test_scripts_executable` parametrised over `pack/skills/*/scripts/*`.

Docs
- `docs/deploy.md`: new `## Codex As Critic` between `Fable Or Opus` (`:128`) and `Doctor Checks`
  (`:148`); one bullet in Doctor Checks and one sentence in Uninstall (`:172`).
- `README.md`: one link line in `Maintaining An Install` (`:186`), the skill in `What's In The
  Pack` (`:166`); nothing in Quick Start.
- `docs/architecture.md`: Skills row (`:86` table) and one sentence at `:106` noting the opt-in
  allow entry as the one exception to "no permission rules".

## Slices

### Slice 1: the switch

Delivers: a user can run `./deploy critic enable|disable|status` (and `claude-supervisor critic
...`) and see the mode file and the permission entry appear and disappear.

Units (disjoint files):
- U1a: script verbs `enable`, `disable`, `status` + `tests/test_codex_critic.py` (switch tests).
- U1b: `deploy` (`critic_cmd`, parser, launcher) + `tests/test_deploy.py` additions.
- U1c: `pack/skills/supervisor-config/SKILL.md`.

Tests:
- `enable_writes_mode_and_rule`: stub codex logged in, `enable --yes` -> mode file equals
  Decision 3 default; `settings.json` `permissions.allow` holds `Bash(<abs> *)`; pre-existing keys
  untouched; `.bak` written.
- `enable_model_arg`: `enable gpt-6-astra --yes` -> `model: gpt-6-astra`, `effort: high`.
- `enable_keeps_domains`: existing `domains` map survives re-enable; rule not duplicated.
- `enable_requires_yes_off_tty`: no `--yes`, stdin not a TTY -> rc 2, nothing written.
- `enable_refuses_missing_binary` / `enable_refuses_logged_out`: rc 1, nothing written, message.
- `disable_removes_both`: mode file gone, rule gone, other allow entries and keys kept.
- `disable_idempotent`: off already -> rc 0.
- `status_off` / `status_on`: prints backend, model, effort, domains, binary path, auth, rule.
- `deploy_critic_delegates`: install to `target`, `deploy critic status --target` prints the
  script's status; `enable --yes` with stub codex on PATH writes both artefacts in `target`.
- `deploy_critic_not_installed`: exit 2 with a message naming the target.
- `launcher_critic_passthrough`: generated launcher `critic status` -> script output, `claude`
  stub not invoked.
- `skill_lint`: existing `test_skill` passes for `supervisor-config`.

Checkpoint: `python3 -m pytest -q tests/test_codex_critic.py tests/test_deploy.py
tests/test_pack_lint.py` and `./deploy install --dry-run --tag t`.

### Slice 2: the review

Delivers: in Codex mode a lead's critic step produces a Codex findings block; every failure path
falls back to the Claude critic; Claude mode is unchanged apart from the probe.

Units:
- U2a: script `review` + its tests.
- U2b: `pack/skills/lead-loop/SKILL.md`, `pack/agents/supervisor.md`, `pack/agents/clerk.md`.

Tests (script, stub codex):
- `review_no_mode_file`: -> stdout `NO_CODEX`, rc 0, stub not called.
- `review_backend_claude` / `review_domain_pinned`: -> `NO_CODEX`, stub not called.
- `review_missing_binary`: PATH without codex -> `NO_CODEX`, stderr names the binary.
- `review_nonzero_rc` / `review_empty_output` / `review_malformed_block` /
  `review_verdict_disagrees_with_rows` / `review_timeout` (stub sleeps, `--timeout 1`): ->
  `NO_CODEX` with the reason on stderr; the repo cwd is left clean.
- `review_valid_block`: stub writes a valid REVISE block -> stdout equals the block plus
  `backend: codex gpt-6.1-sol high`; recorded argv contains every Decision 9 flag, `-C <cwd>`,
  `-o <tmp>`; the `-o` tmp file is removed.
- `review_fenced_block_unwrapped`: block inside ``` fences -> accepted.
- `review_prompt_contents`: domain plan with `--diff` -> stdin to codex contains the critic body
  without frontmatter, `REVIEW.md`, the plan-writing text, the diff, the brief, in that order; the
  preamble names the domain and round.
- `review_prose_includes_writing_md`: cwd with `.supervisor/` -> `writing.md` included; without
  -> not.
- `review_domain_override`: `domains.plan = {model: gpt-6-astra, effort: xhigh}` -> `-m
  gpt-6-astra`, `model_reasoning_effort=xhigh`, NOTES line says so.
- `review_cwd_flag`: `--cwd <dir>` -> `-C <dir>`; without it `-C` is the Bash cwd.

Lead-loop text is validated by the pack lint (line length, caps) and by reading: the executor
checks that step 4 still reads as one procedure for both modes and that `scope-critic` text is
untouched. `supervisor.md` stays at or under 1000 body words
(`tests/test_pack_lint.py:128`).

Checkpoint: `python3 -m pytest -q`; then, if `codex` is installed and logged in on the executor's
machine, one live smoke run from the worktree root against a copy of the config dir
(`cp -R` the dry-run output or a `--tag` test install): `codex-critic review --domain
agent-definition --round 1 --brief <file> pack/agents/scope-critic.md` must print a valid block
including the `backend:` line, and `CLAUDE.md` fallback must not error (Decision 9). Record wall
time and token use in the slice report. Skip and report when Codex is unavailable.

### Slice 3: lifecycle

Delivers: install hints, update preserves, uninstall cleans, doctor diagnoses.

Units:
- U3a: `deploy` (hint, global uninstall step, doctor) + `tests/test_deploy.py` additions.

Tests:
- `install_hint_with_codex` / `install_hint_without_codex`: hint line present iff a `codex` stub
  is on PATH; never enables (no mode file, no allow entry).
- `update_preserves_codex_mode`: install, `enable --yes`, update (as `test_sandbox_round_trip`
  does at `tests/test_deploy.py:735`) -> mode file unchanged, rule present, script re-copied.
- `global_uninstall_removes_codex_mode`: `--global` install, enable, `uninstall --yes` -> mode
  file gone, rule gone, other settings keys as before.
- `sandbox_uninstall_removes_dir`: existing behaviour still holds with the mode file present.
- `doctor_codex_off`: one backend line, no codex rows.
- `doctor_codex_on_ok`: stub codex logged in -> PASS rows, `0 FAIL`.
- `doctor_codex_on_fail[missing-binary|logged-out]` (parametrised) -> FAIL row and exit 1.

Checkpoint: `python3 -m pytest -q tests/test_deploy.py`.

### Slice 4: docs, inventory, lint

Delivers: a user can find, understand and audit the feature; the pack inventory is in sync.

Units:
- U4a: `docs/deploy.md`, `README.md`.
- U4b: `docs/architecture.md`, `tests/test_pack_lint.py` (`test_scripts_executable`).

`## Codex As Critic` covers, in this order: what it does and what stays on Claude
(`scope-critic`, fallback); consent, cost and data flow (quota, repository content sent to OpenAI,
read-only and ephemeral runs, the one allow entry and its exact form); switching (`deploy critic`,
`claude-supervisor critic`, `/supervisor-config critic ...`, no reinstall; first in-session enable
may prompt once); models and per-domain overrides with the JSON shape; fallback behaviour and how
to see which engine reviewed (`backend:` NOTES line, lead report, `status`); caveats (Claude Code
sandbox blocks OpenAI hosts unless allowlisted and nested Seatbelt is unconfirmed, R B5; model IDs
are account-specific; the once-per-task Read probe may prompt in default permission mode if
Verification finds so; Bash rule mismatch when the install path contains a symlink, with `status`
printing the rule). Prose follows the repo's existing docs voice; nothing goes into Quick Start.

Tests: `test_scripts_executable[...]`: every `pack/skills/*/scripts/*` has the exec bit and a
shebang; Python ones `py_compile`. Link check: every `docs/deploy.md#...` anchor referenced from
README exists (one-line grep in the checkpoint).

Checkpoint: `python3 -m pytest -q` and
`grep -o 'deploy.md#[a-z-]*' README.md | sort -u` against `grep '^## ' docs/deploy.md`.

## Verification

1. `python3 -m pytest -q` green in the worktree (baseline: 402 passed, 6 skipped).
2. `/usr/bin/python3 -m py_compile deploy pack/skills/supervisor-config/scripts/codex-critic`;
   `HOME=$(mktemp -d) /usr/bin/python3 ./deploy install --dry-run --tag t` (3.9 check, per
   `.supervisor/memory/facts/2026-10-21-usr-bin-python3-has-no-pytest-check-3.md`).
3. Live, in a `--tag` test install made from the worktree (`./deploy install --tag codextest
   --source <worktree>/pack`, removed afterwards with `uninstall`): `claude-supervisor codextest
   critic status` reports Claude mode; then, inside a session, `/supervisor-config critic codex`
   asks consent, writes both artefacts, and a small `executor` task in the same session reports
   `critic: codex ...` with no permission prompt at the critic step (this exercises the
   mid-session settings reload, D3); `status` and `doctor` agree; `/supervisor-config critic
   claude` restores the Claude path and a second task reports `critic: claude`. Note whether the
   step-1 Read probe prompted in Claude mode and whether the preloaded skill text showed
   `${CLAUDE_SKILL_DIR}` substituted; write the outcome into the docs caveats.
4. `git status` clean apart from the intended files; `VERSION` untouched.

## Risks

- Claude Code's own sandbox (off by default) blocks network for Bash children; Codex inside it
  would fail every run and the lead would silently fall back. Mitigation: `NO_CODEX` reasons on
  stderr, `doctor`, docs caveat. Nested Seatbelt behaviour is unconfirmed (R B5) and out of scope.
- The lead must type the script path exactly as the allow rule has it. A symlinked install path or
  a lead that normalises differently gives a prompt, not a failure. `status` prints the rule.
- The step-1 Read probe may prompt once per task in Claude mode under default permissions. If
  Verification confirms this, the docs say so and the user decides whether to keep the probe or
  accept a Bash call at each critic step instead (reported as an open item then, not now).
- Long reviews: high effort took 36-57 s on one small file (R B7); a large diff could approach the
  540 s script timeout and fall back. The timeout is a flag; the docs name it.
- Model IDs and quota behaviour are account-specific (R B3); `enable` cannot validate them cheaply.
- Codex output drift: a future Codex version wrapping the block differently fails validation and
  falls back; the stderr reason makes this visible.
- `supervisor.md` has no word headroom; the required one-line change must be paid for with cuts in
  the same file without losing a rule.
- Compatibility: pack files are identical in both modes and the mode file is ignored by every
  deploy code path except `critic`, `uninstall --global` and `doctor`; a pre-feature install
  updated to this version behaves as before until the user enables.

## Scope Notes

In scope: D1-D8 of the brief as restated above. Out of scope: the non-goals in `## Goal`
(`scope-critic` is the user's call, D6), any `VERSION` edit (D8), and, by memory: install-time
variants (`.supervisor/memory/decisions/2026-10-23-fable-is-default-opus-is-opt-in.md`);
reading the source checkout at run time (`2026-10-22-installs-never-need-the-source-checkout.md`);
deriving the target from `CLAUDE_CONFIG_DIR` (`2026-10-22-install-target-comes-from-flags-only.md`);
printed strings say "Supervisor for Claude" (`2026-10-23-product-name-is-supervisor-for-claude.md`).
Decisions 1-17 are the executor's constraints; D-numbered items of the brief are the user's and
are not reopened. Commits on the branch via `git-ops` or the executor lead with the trailer
`Co-Authored-By: Supervisor for Claude` (D9).

## Assumptions

- A1: `codex exec` accepts `-c 'project_doc_fallback_filenames=["CLAUDE.md"]'` without error;
  checked by the Slice 2 live smoke run (dropped if not).
- A2: Claude Code prints `Base directory for this skill: <abs>` for preloaded skills in subagents;
  observed in this planning session for `lead-loop`, `plan-writing` and `repo-workflow`; re-checked
  in Verification 3.
- A3: the `codex` stub approach (sh script on a private PATH) runs under the test suite's
  whitelisted env on macOS and Linux; checked by Slice 1 tests.

## Open Questions

None for the user. Two items may come back after Verification 3 (the Read-probe prompt and
`${CLAUDE_SKILL_DIR}` substitution in preloaded skills); both have a default in the plan.

## Log

- 2026-10-24 executor: suspended. Part A rebase onto origin/main v6.1 (70fb747) landed, tests green except lead-loop word cap; Part B wip-committed (install-time rule `Bash(<abs> review *)`, probe removed, consent 2 bullets, cap raised 1300->1350 per user option a, 3 lossless v6 lead-loop trims, docs updated); deferred: deploy-side Part B worker output unverified (tests/test_deploy.py not run), headless NO_CODEX re-verify, critic round, plan Todo ticks.
- 2026-10-24 executor: resumed and done; branch on v6.1 with Part B (install-time review-only rule, no probe, cap 1350); 467 tests green; headless default mode: review -> NO_CODEX unprompted, enable prompts; deferred: end-to-end in-session lead run in a logged-in profile (needs interactive /login)

## Todo

- [x] S1 U1a: script `enable`/`disable`/`status`, mode file, allow rule, consent text; tests
- [x] S1 U1b: `deploy critic` verb, `LAUNCHER_COMMANDS`, launcher branch and help; tests
- [x] S1 U1c: `pack/skills/supervisor-config/SKILL.md`
- [x] S1 checkpoint
- [x] S2 U2a: script `review` (prompt assembly, flags, validation, fallbacks); tests
- [x] S2 U2b: `lead-loop` step 1 probe, step 4 branch, step 7 line; `supervisor.md`; `clerk.md`
- [x] S2 checkpoint, live smoke run if Codex is available
- [x] S3 U3a: install hint, global uninstall cleanup, doctor check; tests
- [x] S3 checkpoint
- [x] S4 U4a: `docs/deploy.md` section, README link and pack list
- [x] S4 U4b: `docs/architecture.md` row and constraint note; `test_scripts_executable`
- [x] S4 checkpoint
- [ ] Verification 1-4; record probe and `${CLAUDE_SKILL_DIR}` outcomes in docs caveats
- [x] Commit on `feat/codex-critic` with the trailer; leave `VERSION` alone
