# Plan: Full Code Review, New-User Usability Review, and REVIEW.md (ROADMAP 1)

Line numbers refer to files at `70e5e85`. `VERSION` is `1.19`. The review itself (the research
stage of this item) is complete: six parallel planner-workers reviewed `deploy` (two halves),
`tests/`, `pack/` against `agent-authoring`, and the new-user journey through `README.md` and
`docs/deploy.md` against a temp-HOME run of every subcommand. Their findings are in `## Findings`
below with a disposition each, so `executor` fixes from this file without re-reviewing.

## Goal

Fix every finding below that is marked `fix`, create the repo's first `REVIEW.md` from the
checklist the review used, make `critic` apply a project's `REVIEW.md` files when present, keep
`docs/architecture.md` in sync, and leave `README.md` and `docs/deploy.md` matching `deploy` for
every journey step, with `python3 -m pytest -q` passing and `VERSION` bumped per change set.

## Approach

- Three independent streams run as three parallel work packages, each reviewed in its own domain:
  P1 code (`deploy`, `tests/`), P2 docs (`README.md`, `docs/deploy.md`), P3 pack and review wiring
  (`REVIEW.md`, `pack/`, `docs/architecture.md`). P4 integrates: one `VERSION` bump, the full
  suite, ROADMAP item removal, plan archive, one commit (OQ1 default; the alternative is one commit
  per package in sequence). Rationale: the critic reviews one domain per dispatch (`code`, `prose`,
  `agent-definition`), the three diffs touch disjoint files, and ROADMAP treats one item as one
  change set. Rejected: a flat plan, because one mixed-domain review of ~85 findings is too large
  to review well; child plans per package, because every package is execute-only.
- `deploy` fixes follow two patterns: validate before the first write (source, registry, launcher
  conflict, token file; the same preflight runs in `migrate` before it removes anything), and
  every user-facing error, WARN, or FAIL message names the next command, written as `./deploy ...`
  since `deploy` is not on PATH. No new flags or subcommands.
- `tests/` gains tests for every changed behavior plus the untested `doctor` command, with a
  whitelisted subprocess environment and a stub `claude` on PATH.
- The `critic` rule is 36 words and fits the 57-word headroom (`tests/test_pack_lint.py:21`
  caps Review-tier bodies at 600; `critic.md` is 543). No separate checklist file in the pack is
  needed; `REVIEW.md` itself is a project file and uncapped. For non-code domains, the
  "directory containing changed files" is the artifact's directory (`docs/` for plans). Rejected:
  passing `REVIEW.md` through the lead's brief, because the decision says critic loads it when
  present, which also serves `supervisor`'s ad hoc reviews.
- `CLAUDE.md` holds no review-only rules today (every line is an edit, test, deploy, or commit
  rule), so nothing moves; the "Done when" criterion already holds and the plan records it.
  `REVIEW.md` instead carries the checklist derived from this review, in the shape Anthropic's
  Code Review reads (always-check rules, severity calibration, do-not-report, evidence).

## Findings

Severity: High = wrong behavior, data loss, half-done state, a traceback, or a message or doc step
that leaves the user stuck; Medium = resilience or edge-case gap, misleading message, docs that
disagree with the tool; Low = polish. Disposition: `fix` (in the owning package), `reject: reason`,
or `OQn` (user decides, see Open Questions). Merged duplicates are noted in the ID column.

### Code: `deploy` (P1)

| ID | Sev | Location | Finding | Fix |
|---|---|---|---|---|
| D-01 (= D-53, D-04, U-03) | High | deploy:1337-1346, 614 | `main` catches only `DeployError` and `KeyboardInterrupt`; any `OSError`, `shutil.Error`, or `EOFError` (missing `--token-file`, read-only target, Ctrl-D at a prompt) is a raw traceback, often mid-install | fix: catch `OSError` and `shutil.Error` in `main` (`error: <exc>; check the path and permissions, then re-run`, exit 2); `EOFError` at a prompt prints `aborted` (exit 1); wrap the token read at 614 as `DeployError("cannot read --token-file %s: %s; check the path")` |
| D-02 | High | deploy:583, 601 | A dangling symlink under `~/.claude/skills` or `agents` makes `copytree` raise during seeding; the partial dir then makes every re-run skip that seed silently | fix: `copytree(..., symlinks=True)`; on error remove the partial dir and raise `DeployError("cannot seed from %s: %s; fix or move that file and re-run")` |
| D-51 | High | deploy:1142-1146 | `migrate` removes the pack from `~/.claude` before `install_cmd` can fail its own checks (launcher conflict 612, `collect_source`, token file, registry); the user ends with no pack and no sandbox and a message that does not say so | fix: factor the install preflight (resolve source, `collect_source`, `load_registry`, launcher check, token read) into one function that `install_cmd` and `migrate_cmd` call first; on an install failure after the uninstall, print `pack files were removed from ~/.claude (backup: %s); fix the error above and re-run ./deploy migrate` |
| D-52 | High | deploy:958-968 | `uninstall` keeps locally modified files but still deletes the manifest and registry entry, so the hint `use --force to remove` fails on re-run with `nothing to uninstall` | fix: message becomes `WARNING kept locally modified %s (now unmanaged; delete it by hand)` |
| D-03 | Medium | deploy:589, 597, 459 | An unparseable `~/.claude/settings.json` aborts a first sandbox install with install wording (`settings step skipped, file not changed`), and `Seeded ...` prints before the copy | fix: seed errors raise the D-02 message; print `Seeded` after the copy; make the `(settings step skipped...)` suffix install-only |
| D-05 (= D-61) | Medium | deploy:763, 516-529 | A corrupt `installs.json` is detected after files, manifest, settings and launcher are written; the tool copy is then missing and the message has no next step | fix: `load_registry` in the preflight (D-51); registry errors end with `; delete or fix that file, then re-run ./deploy install` |
| D-06 (= D-19, D-60 part) | Medium | deploy:418-430, 658 | Corrupt or unsupported-version manifest blocks every command with no recovery text; a non-dict `files` entry is an `AttributeError` | fix: `cannot read manifest %s: %s; restore it from a backup, or delete it and re-run ./deploy install (existing files then need --overwrite-local)`; `manifest %s has unsupported version %r; it was written by a newer deploy, update your checkout`; validate that `files` values are dicts in `load_manifest` |
| D-08 | Medium | deploy:612 | Installing a second target with the same `--tag` silently repoints `claude-TAG` and orphans the first install | fix: if the existing launcher's `CLAUDE_CONFIG_DIR` differs from `target`, raise `claude-%s already launches %s; pick another --tag` |
| D-09 | Medium | deploy:612-613 | `exists and is not a claude-supervisor launcher` has no next step | fix: append `; move it aside, or choose another --tag or --prefix` (tests at test_deploy.py:729,733 assert the prefix, keep it) |
| D-10 | Medium | deploy:365-369, 539 | The `origin` URL is stored and printed verbatim; `https://user:token@host/...` leaks credentials in `status` and `update` prompts | fix: strip userinfo with `urllib.parse` in `git_remote` before recording |
| D-54 | Medium | deploy:1011-1014, 1099 | `update --all --from DIR` with no matching registered install prints nothing and exits 0 | fix: when `selected` is empty print `no registered install follows branch %s of %s; nothing updated` |
| D-55 | Medium | deploy:1007-1008 | `update` for an install made with `--prefix` says `not registered; run deploy install once` | fix: `%s is not registered under prefix %s; run ./deploy install once (pass --prefix if you installed with one)` |
| D-56 | Medium | deploy:1297-1299 | `uninstall --help` understates the default: a sandbox uninstall deletes the whole config dir (sessions, login) and the launcher | fix: add `Sandbox installs (default): deletes the whole sandbox dir and its launcher. --global: removes only pack files.` |
| D-57 (= U-08 part) | Medium | deploy:1210-1211 | Doctor's files row mixes missing (FAIL) and modified (WARN) and gives no next step | fix: two rows: FAIL `%d managed files missing: %s; run ./deploy install` and WARN `%d managed files modified: %s; keep them, or run ./deploy install --overwrite-local` |
| D-58 | Medium | deploy:1176, 1180, 1189 | FAIL rows for old python, missing `claude`, unreadable `claude --version` give no remedy | fix: `python %s; deploy needs 3.9 or newer`; `claude CLI not found on PATH; install Claude Code and open a new terminal`; `cannot determine claude version from \`claude --version\`: %r; reinstall Claude Code` |
| D-59 (= U-06) | Medium | deploy:1220 | `settings agent = None (expected 'supervisor'...)` WARN fires before any install (docs promise one WARN) and for a deliberate `--no-default-agent`, with no remedy | fix: skip the row when no manifest exists; otherwise append `; run ./deploy install (--force-default-agent to replace another agent)` |
| D-60 | Medium | deploy:1199, 1224 | Doctor FAIL rows pass raw `load_manifest`/`load_settings` text, including install wording | fix: covered by D-06 and D-03 message changes; settings row reads `cannot parse %s: %s; fix the JSON` |
| D-62 | Medium | deploy:885-888, 907-911 | After a failed sandbox `rmtree`, a later uninstall says `nothing to uninstall` and never mentions the dir with sessions and login still exists | fix: in the no-manifest branch, when `target` exists append `The directory still exists; delete it by hand if you no longer need it.`; unlink the launcher after the `rmtree` |
| D-63 | Medium | deploy:1079-1080, 1090-1091 | Missing git is reported as a network error; `clone failed` has no next step | fix: `FileNotFoundError` reads `git not found on PATH; install git`; clone message appends `; check network access, credentials and that the branch exists, or pass --from DIR` |
| D-64 | Medium | deploy:1144 | After a migrate uninstall failure the message omits that pack files were already removed and where the backup is | fix: covered by the D-51 message (update test_deploy.py:1457's expected text) |
| U-01 | High | deploy:766-772 (and docs) | After `install` nothing tells the user how to get `claude-supervisor` onto PATH; only `migrate` (1147-1152) prints the export hint | fix: run the same PATH check at the end of `install_cmd`: `WARNING %s is not on your PATH; add export PATH="%s:$PATH" to your shell profile, then open a new terminal` |
| U-02 | High | deploy:682, 979 | During `update` a collision says `use --overwrite-local`, a flag `update` never passes | fix: message reads `exists but is not managed by this pack; not touched (run ./deploy install --overwrite-local from your checkout to replace it)` |
| D-07 (= D-65) | Low | deploy:753, 1344-1346 | Manifest is written last, so an interrupted install leaves files without a baseline; a re-run after a source change reports them unmanaged | fix: the `KeyboardInterrupt` message reads `interrupted; re-run ./deploy install (use --overwrite-local if files are reported as not managed)`. Rejected the `finally` manifest write: larger change for an interrupt-plus-source-change edge case |
| D-11 | Low | deploy:321-323 | A SKILL.md without frontmatter reports `frontmatter name None != directory` instead of the agents' `missing --- frontmatter` | fix: test `parse_frontmatter(...) is None` first in the skills branch |
| D-12 | Low | deploy:217 | A UTF-8 BOM makes a valid frontmatter read as missing | reject: `collect_source` reads the repo's own `pack/` files, which carry no BOM |
| D-13 | Low | deploy:659-664 | `target is a symlink or not a regular file; skipped` has no next step | fix: append `; replace it with a regular file or remove it, then re-run` |
| D-14 (= D-70, U-19) | Low | deploy:35, 201-203, 52, 1073, 1202 | Messages say `run deploy install`, but `deploy` is not on PATH; the tool copy has no `pack/` | fix: `source directory not found: %s; run ./deploy from the repo checkout or pass --source DIR`; every recovery message writes `./deploy ...` and adds `from your checkout` where it names install; doctor's install hint carries the non-default `--tag`/`--target` |
| D-15 | Low | deploy:47-62 | Launcher wraps paths, base URL and token path in unescaped single quotes | reject: config-dir, prefix and URL values carry no quote characters in practice; four tests (test_deploy.py:591, 623, 697, 998) pin the quoted form |
| D-16 | Low | deploy:536-540 | Registry read-modify-write is not locked across targets | reject: the registry is written by one sequential process per user; `update --all` is sequential |
| D-17 | Low | deploy:444 | Lock error says nothing about retrying | fix: append `; wait for it to finish, then re-run` (test_deploy.py:268 asserts a prefix, keep it) |
| D-18 | Low | deploy:139-152 | Non-tty refusal reads `<question> -- refusing without a terminal`; Ctrl-D is a traceback | fix: `cannot ask '%s' without a terminal; re-run with --yes`; `EOFError` handled per D-01 (test_deploy.py:245 asserts the refusal, update it) |
| D-20 | Low | deploy:173, 188 | `--target ""` and `--prefix ""` fall back to defaults silently (`--tag ""` is rejected, test_deploy.py:715) | reject: an empty path flag is not an observed failure |
| D-21 | Low | deploy:574 | `prune_empty_dirs` stops at `.DS_Store`, leaving `skills/<name>/` after uninstall | fix: ignore `JUNK_NAMES` when judging emptiness |
| D-22 | Low | deploy:451 | `load_settings` annotated `Optional[dict]` but never returns None | fix: `dict` |
| D-66 (= U-04 part) | Low | deploy:1239-1241 | Doctor calls git `optional, used by some skills`; `update` and commit recording need it | fix: `git not found; needed for ./deploy update and to clone, optional otherwise` |
| D-67 | Low | deploy:864-868 | `uninstall --all` prints no per-install header (update prints `== update key ==`, 987) | fix: print `== uninstall %s ==` first |
| D-68 | Low | deploy:903, 907-911 | `Removed X and <launcher>` prints even when the launcher was missing or not a launcher | fix: build `gone` from what was removed; `WARNING %s is not a claude-supervisor launcher; left in place` |
| D-69 | Low | deploy:1055, 763 | `update --from CHECKOUT` re-registers the install with that checkout's remote and branch silently | fix: print `now tracking branch %s of %s` when either changed |
| U-15 | Low | deploy:825-829 | `status` after `update` shows a deleted temp dir as Source and `source=unknown` | fix: append `(source dir gone; pass --source <checkout>/pack)` when the source is missing |
| U-08 (env rows) | Medium | deploy:1226-1237 | The three env WARNs do not say what to do | fix: append `; unset it, or remove it from settings.json env` |

### Code: `tests/` (P1)

| ID | Sev | Location | Finding | Fix |
|---|---|---|---|---|
| T-01 | High | tests/ (none) | `doctor` (deploy:1167-1246) has zero tests | fix: `test_doctor_*` with a stub `claude` script on PATH: all-PASS exit 0; `claude` missing FAIL exit 1; old version FAIL; unparsable version FAIL; file missing FAIL; file modified WARN exit 0; each env var WARN; no manifest gives one WARN (D-59); corrupt manifest FAIL text |
| T-02 | High | test_deploy.py:53-63 | No test drives `confirm`/`confirm_typed` (deploy:139-152); only the no-tty refusal and `--yes` are covered | fix: in-process tests via `load_deploy()` with `isatty` and `input` monkeypatched: yes, no, typed tag, `EOFError` -> aborted |
| T-03 | Medium | test_deploy.py:54 | `run()` copies the developer's whole environment; `CLAUDE_CODE_*`, `GIT_*`, `XDG_*` leak and will break doctor tests | fix: build the env from a whitelist (`PATH`, `HOME`, `TMPDIR`, `LANG`, `LC_ALL`) plus explicit extras |
| T-04 | Medium | (none) | `update --dry-run` (deploy:985, 1017, 1031, 1096) untested | fix: one test: snapshot unchanged, `[dry-run]` line present |
| T-05 | Medium | deploy:1088-1098 | Clone failure and child update failure untested | fix if cheap: delete the branch in the bare remote after install, assert exit 1 and the D-63 text; otherwise record as rejected in the commit |
| T-06 | Medium | deploy:424-429, 523-528, 460 | Corrupt manifest, registry and settings types untested | fix: parametrize malformed JSON, wrong version, non-dict entry; assert exit 2, no `Traceback`, and the D-05/D-06 text |
| T-07 | Medium | deploy:286-325 | Most `collect_source` validation branches untested | fix: parametrize the pack fixture: missing dir, no agents, SKILL.md missing, skill name mismatch, no frontmatter (D-11), symlinked dir |
| T-08 | Medium | deploy:793, 796 | `status` rows `outdated` and `not installed` untested | fix: edit the source after install and assert both |
| T-09 | Medium | test_version.py:48 | The rule checks only the working tree against `HEAD`; a committed forgotten bump passes once committed | OQ3 (default reject: `CLAUDE.md` defines the rule at this enforcement point) |
| T-10 | Medium | test_pack_lint.py:62 | The Tiers table's Tools column is not enforced (supervisor no Bash, critic no Write/Edit, scope-critic no Bash, leads preload `lead-loop`) | fix: assert `disallowedTools`/`skills` per tier for those rows |
| T-11 | Low | test_pack_lint.py:74-81 | Closing `---` with trailing whitespace counts the frontmatter as body | fix: `l.strip() == "---"` |
| T-12 | Low | test_pack_lint.py:128 | Leaf assertion `"Agent" in disallowed or tools` passes for any allowlist | reject: the `or tools` branch is the allowlist case (`git-ops`, `quick-edit`), and L127 already asserts `Agent` is absent from the allowlist |
| T-13 | Low | deploy:659, 712 | Symlink-target and removed-but-modified branches untested | fix: one test each |
| T-14 | Low | test_deploy.py:309-350 | In-process tests duplicate HOME setup | reject: no observed fragility; rewrite beyond findings |
| T-15 | Low | test_deploy.py:1030, 1135, 1150 | The roots/snapshot block is copy-pasted | fix only when the new tests need it: one `snapshot_unchanged(tmp_path)` helper |
| T-16 | Low | deploy:586-588, 635, 729-745 | Seed dry-run, `--base-url ''` clear, `source_commit`/`source_dirty` recording unasserted | fix: one assertion each |
| T-17 | Low | deploy:1112, 1122-1124 | Migrate prefix mismatch and backup collision untested | fix: prefix mismatch test; reject the collision test (needs a clock mock) |
| T-18 | Low | test_deploy.py:909 | The remote fixture is rebuilt per test (most of the 42s) | reject: 42s is acceptable; a session-scoped bare repo couples tests |

### Pack (P3)

| ID | Sev | Location | Finding | Fix |
|---|---|---|---|---|
| P-01 | High | researcher.md:23, planner.md:33 | `Write only research artifacts.` / `Write only plan files.` contradicts `lead-loop` L61-63, which has the lead write scratch copies and `diff -u` files for round 2 | fix: append `and review scratch files per \`lead-loop\`` to both (planner headroom 81) |
| P-02 | Medium | meeting-summary/SKILL.md:24,112; writer.md:32-33; researcher-worker.md:22; writer-worker.md:25 | Workers must return facts with locations, but the skill emits finished minutes with no locations and hides its Pass 1 | fix: one line in the skill: when dispatched by a lead, return the Pass 1 extraction with timestamps instead of minutes |
| P-03 | Medium | planner-worker.md:6 vs 20 | Prompt says `Never write or edit files` but `disallowedTools` omits `Write` | fix: add `Write` to `disallowedTools`; architecture.md:34 becomes `all except Agent, Write, Edit, NotebookEdit` |
| P-04 | Medium | writer.md:41-42; agent-authoring/SKILL.md:21; architecture.md:16,36,73 | writer dispatches `writer-worker` with `model: fable`, but the docs list only the critic override | fix: agent-authoring L21-22 and architecture.md L73 name both overrides; L16 and L36 add `(fable when writer calls)` |
| P-05 | Medium | executor.md:22-23; git-safety/SKILL.md:41 | executor is told to read `references/conflict-resolution.md` with no path; whether `${CLAUDE_SKILL_DIR}` expands in a preloaded skill is unverified | fix: executor.md names the same `${CLAUDE_SKILL_DIR}/references/conflict-resolution.md` path git-safety uses; see Risks |
| P-06 | Medium | presentation-style/SKILL.md:30-50 | No `[hard floor]`/`[overridable default]` tags, which `writing-rules-persistence` L28/L32 depends on | fix: one line: the "Hard language rules" and "AI-tell avoidance" sections are hard floors; everything else is overridable |
| P-07 | Low | lead-loop/SKILL.md:78 | `needs user:` is defined only in `science-writing-style`; critic.md never emits it for other domains | fix: `(prose domain; see \`science-writing-style\`)` |
| P-08 | Low | writing-rules-persistence/SKILL.md:57-61; critic.md:43-44 | Heading says `(writer only)` but L60 has critic read it; critic.md loads the skill `when docs/writing-rules.md exists` while SKILL L48 says use only the path the brief gives | fix: heading `Lead procedures`; critic.md: `Load \`writing-rules-persistence\` when your brief gives a rules path.` |
| P-09 | Low | meeting-summary/SKILL.md:109 | `say what is missing and ask`; subagents cannot ask the user (architecture.md:97) | fix: `and stop` |
| P-10 | Low | project-backup/SKILL.md:1-5 | User-only skill lacks `disable-model-invocation: true` (agent-authoring L52-53) | fix: add the key |
| P-11 | Low | supervisor.md:56-59 | Ad hoc review dispatch omits the domain and contract critic.md requires | fix: `with the domain and contract` |
| P-12 | Low | supervisor.md:90-91 | `quick-edit` runs `git mv`/`git add` for the archive move although `git-ops` owns git | reject: the exception is documented at architecture.md:59 and the operations are non-destructive |
| P-13 | Low | science-writing-style/SKILL.md:135-138 | Broken wrapping (`using` alone on a line) | fix: reflow |
| P-14 | Low | executor.md:3 | Description omits git conflicts and Python environments, which supervisor.md:22 routes to executor | fix: add `git conflicts, Python environments` |
| P-15..P-19 | Low | planner.md:24-25; scope-critic.md:39-45; lead-loop/SKILL.md:30-31; conflict-resolution.md:22-23; document-extraction/SKILL.md:43-47, email-extraction/SKILL.md:42-45 | Clauses that read as anticipated-failure rules or restate earlier rules | OQ2 (default: delete P-18 and P-19 as pure restatements; keep P-15, P-16, P-17 unless the owner recalls no failure behind them) |

Inventory check: all 14 agents match `docs/architecture.md` on name, model, effort and tools; the
only mismatches are P-03 and P-04 above.

### Docs: `README.md`, `docs/deploy.md` (P2)

| ID | Sev | Location | Finding | Fix |
|---|---|---|---|---|
| U-01 | High | README.md:21,186; docs/deploy.md:20 | Docs say the launcher must be on PATH but give no command | fix: README: after the install step add `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc` (zsh is the macOS default; `~/.bashrc` for bash), then open a new terminal. docs/deploy.md (also read by Claude, L1, L163): show the `export PATH="..."` line that `install` now prints and say to ask before editing the profile |
| U-02 | High | README.md:172, 190-191 | Troubleshooting does not cover a collision during `update` | fix: one row: run `./deploy install --overwrite-local` from your checkout |
| U-04 | Medium | README.md:9-11; docs/deploy.md:3 | `needs only python3` is false: `git` is needed to clone and for `update` | fix: add `git` to Requirements; drop `only` |
| U-05 | Medium | README.md:29-35, 167-169, 187; docs/deploy.md:13-17 | Nothing says `doctor`, `status`, `update` and `uninstall` take the same `--tag` or `--global` as the install | fix: one sentence under "Choosing An Install" |
| U-06 | Medium | README.md:16; docs/deploy.md:13 | Comments promise one WARN before install; the tool prints two | fix: after D-59 one WARN is correct; keep the comments and verify in P4 |
| U-07 | Medium | docs/deploy.md:119-127 | The Doctor Checks table omits the python, `claude` presence, managed-files, settings-agent and `settings.json env` rows and does not mark FAIL vs WARN | fix: add the rows with level and remedy, matching the D-57/D-58/D-59 texts |
| U-09 | Medium | README.md:35, 191 | A first install can exit 1 because a seeded user agent shadows a pack name; the launcher and manifest are still written | fix: Quick Start says `if install prints ERROR, see Troubleshooting`; Troubleshooting row for `exists but is not managed by this pack` |
| U-10 | Medium | README.md:17, 29-35 | "sandbox" is undefined at first use; MCP servers and `~/.claude.json` state do not carry over | fix: gloss at first use: `a private config dir, not a security sandbox`; one clause on what does not carry over |
| U-11 | Medium | docs/deploy.md:7-18 | The Steps block mixes first-time (`git clone`) and existing-checkout (`git pull`) commands | fix: split into "First time" and "From an existing checkout" |
| U-12 | Medium | README.md:176; docs/deploy.md:42-48 | "token" and "token provider" are never explained | fix: `only for a proxy or gateway; omit it to use a normal login` |
| U-13 | Medium | README.md:182-193 | Troubleshooting misses `STALE ... branch is gone` (exit 3), `was installed with --prefix X`, `exists and is not a claude-supervisor launcher`, `another deploy is running`, `is not registered`, `cannot read branch` | fix: one row each, using the P1 message texts |
| U-14 | Medium | README.md:25; docs/deploy.md:129 | Plugins stay behind in a sandbox, so "In Claude Code" is ambiguous for the document-skills plugin | fix: `inside a claude-supervisor session` |
| U-16 | Low | README.md:164 | `update` wording hides that it updates only the default sandbox without `--all`/`--tag` and ignores local checkout edits | fix: one clause |
| U-17 | Low | docs/deploy.md:38, 117, 150 | Hard-coded `1.x`, `before 1.10`, and `before this change` will go stale | fix: `X.y` placeholders; name the version for the migrate note |
| U-18 | Low | docs/deploy.md:164 | Exit-code note omits a doctor FAIL and an aborted prompt (both exit 1) | fix: add them |
| U-20 | Low | docs/deploy.md:69 | `Neither is ever deleted` is true of the registry file and tool copy, but entries are removed | fix: `the registry file and tool copy stay after uninstall` |
| U-21 | Low | README.md:37 | Fable and Opus appear with no gloss | fix: one line or a link to `docs/architecture.md` Models And Cost |
| A-01 | Low | docs/archive/plan-install-lifecycle.md:1, 19, 68, 323, 337, 347, 357, 389 | References to ROADMAP items 6-8, which no longer exist | reject: archived plans are frozen history; the numbering was correct when written |

## Files

### P1 (code)
- `deploy`: modify per the D-* and U-01/U-02/U-08/U-15 fixes above.
- `tests/test_deploy.py`: modify (env whitelist, stub `claude` helper, updated expected texts at
  245, 268, 729, 733, 827, 1457) and add tests per the T-* fixes.
- `tests/test_pack_lint.py`: modify (T-10, T-11, T-12).
- `tests/test_version.py`: unchanged unless OQ3 says otherwise.

### P2 (docs)
- `README.md`: modify per U-*, plus one paragraph on `REVIEW.md` (text in Interfaces).
- `docs/deploy.md`: modify per U-*.

### P3 (pack and review wiring)
- `REVIEW.md`: create (content in Interfaces).
- `pack/agents/critic.md`: modify (new bullet; P-08 wording).
- `pack/agents/{researcher,planner,planner-worker,writer,executor,supervisor}.md`: modify per P-*.
- `pack/skills/{agent-authoring,meeting-summary,presentation-style,writing-rules-persistence,science-writing-style,project-backup,lead-loop}/SKILL.md`: modify per P-*.
- `pack/skills/git-safety/references/conflict-resolution.md`, `pack/skills/document-extraction/SKILL.md`, `pack/skills/email-extraction/SKILL.md`: only if OQ2 says delete.
- `docs/architecture.md`: modify (critic row and step 4, planner-worker tools, writer-worker
  override, skills table row for `meeting-summary` if P-02 changes its contract).

### P4 (integration)
- `ROADMAP.md`: delete item 1 (L24-73), renumber item 2, and drop its `Depends on item 1.` (L98).
- `docs/plan-full-review.md` -> `docs/archive/plan-full-review.md` with `git mv`.
- `VERSION`: `1.19` -> `1.20` once (OQ1 default; one bump per package commit under the alternative).

## Interfaces And Data

### `deploy` message contract (P1; tests assert the quoted fragments)

Every error, WARN and FAIL message ends with a next step. Commands are written `./deploy <cmd>`,
and `from your checkout` is added where the message names `install`. Exact new texts are in the
Findings table; the fragments tests assert are:

- `cannot read --token-file` (D-01); `error:` prefix and no `Traceback` for OSError paths.
- `cannot seed from` (D-02/D-03); seed symlinks preserved (`symlinks=True`).
- `delete or fix that file, then re-run ./deploy install` (D-05); the target dir is empty after a
  refused install.
- `restore it from a backup, or delete it` and `written by a newer deploy` (D-06).
- `already launches` (D-08); `move it aside, or choose another --tag or --prefix` (D-09).
- `now unmanaged; delete it by hand` (D-52).
- `pack files were removed from ~/.claude (backup:` (D-51/D-64); and, for a preflight failure,
  `~/.claude` still holds the pack.
- `not registered under prefix` (D-55); `nothing updated` (D-54); `now tracking branch` (D-69).
- `run ./deploy install --overwrite-local from your checkout` (U-02).
- Doctor rows (D-57, D-58, D-59, U-08): `managed files missing:` FAIL, `managed files modified:`
  WARN, `install Claude Code`, `reinstall Claude Code`, `deploy needs 3.9 or newer`, `unset it, or
  remove it from settings.json env`, and no `settings agent` row without a manifest.
- `is not on your PATH; add export PATH=` after a sandbox install (U-01).
- `cannot ask '` (D-18); `wait for it to finish` (D-17).
- `== uninstall ` header (D-67); `left in place` (D-68); `The directory still exists` (D-62).
- `source dir gone; pass --source` (U-15); `git not found on PATH` (D-63).

Preflight (D-51): one function, called at the top of `install_cmd` and before the uninstall in
`migrate_cmd`, that resolves the source, runs `collect_source`, `load_registry(prefix)`, the
launcher checks (D-08, D-09) and the token read (D-01). It writes nothing.

### Test harness (P1)

- `run()` env: whitelist `PATH`, `HOME`, `TMPDIR`, `LANG`, `LC_ALL`, plus keyword extras.
- `stub_claude(bin_dir, version="2.1.300")` writes an executable `claude` that answers
  `--version` with `<version> (Claude Code)` and records other argv to a file; tests prepend
  `bin_dir` to `PATH`.
- `test_pack_lint.py` T-10: a `TIER_TOOLS` map from the Tiers table (supervisor: `Bash` in
  `disallowedTools`; critic: `Write`, `Edit` in `disallowedTools`; scope-critic: `Bash` in
  `disallowedTools`; the four leads: `lead-loop` in `skills`).

### `critic.md` change (P3; 36 words, body 583 after the P-08 edit, cap 600)

Insert after L32 (the `**All domains**` bullet):

```
- **Project rules**: Apply `REVIEW.md` at the repo root and in each directory holding a changed
  file or the artifact, when present. Precedence: the contract, then `REVIEW.md`, then this file.
  `REVIEW.md` never overrides the user's decisions.
```

Replace the sentence `Load \`writing-rules-persistence\` when \`docs/writing-rules.md\` exists.` (the
last sentence of L43-44; keep the `presentation-style` sentence before it) with
`Load \`writing-rules-persistence\` when your brief gives a rules path.` (P-08).

"Changed file" means a path in the diff for `code`; for `research`, `plan`, `prose` and
`agent-definition` the artifact's own paths count, so `docs/REVIEW.md` would apply to plans and
`pack/REVIEW.md` to agent definitions. Nothing else in the pack changes for this: leads pass no
new input (`lead-loop` L49-53 unchanged), and `supervisor`'s ad hoc review gets the same behavior.

### `REVIEW.md` (P3; root; about 40 lines)

```
# Review Rules

Rules for reviewers of this repo: Anthropic Code Review and the pack's `critic`.

## Always check

- `deploy`: stdlib-only and Python 3.9 syntax (`/usr/bin/python3 -m py_compile deploy`); every
  error, WARN and FAIL message says what went wrong and names the next command as `./deploy ...`
  (`deploy` is not on PATH); validation (source, registry, launcher conflict, token file) runs
  before the first write; no traceback reaches the user; `migrate` and `uninstall` never leave
  a half-done state without saying so.
- `tests/`: every changed `deploy` branch has a test; tests run against a temp HOME with a
  whitelisted environment, never the real `~/.claude` or `~/.config/claude-supervisor`.
- `pack/`: `pack/skills/agent-authoring/SKILL.md` conventions; body word caps are not raised;
  `docs/architecture.md` matches each agent's frontmatter (name, model, effort, tools);
  cross-references to agents, skills, sections and lines resolve; a new rule cites an observed
  failure.
- `README.md` and `docs/deploy.md`: every command is copy-pasteable with flags that exist;
  stated behavior matches `deploy`; prerequisites and the next step are stated for a new user.
- Every change set on `main` bumps `VERSION` once (`CLAUDE.md`).

## Severity here

- BLOCKING (Important): data loss, a half-done install, uninstall or migrate state, a traceback,
  a message or doc step that leaves the user stuck, a failing test, a word-cap violation.
- SHOULD: a message without a next step, a doc that disagrees with the tool, a stale reference.
- Do not report: line length and word counts under the caps (linted), anything under
  `docs/archive/`, style in test fixtures.

## Evidence

- For a claim about `deploy` behavior, run the command against a temp HOME and quote the output.
```

### `docs/architecture.md` (P3)

- L37 critic row: scope becomes `Reviewer: quality and compliance, PASS/REVISE; applies the
  project's REVIEW.md when present`.
- L50 step 4: append `It applies the project's root REVIEW.md and any REVIEW.md in a directory
  holding a changed file or the artifact, after the brief's contract.`
- L34: planner-worker tools `all except Agent, Write, Edit, NotebookEdit` (P-03).
- L16, L36, L73: writer-worker override (P-04).

### `README.md` paragraph on `REVIEW.md` (P2, after the "Larger Work" review sentence)

`A project can add a REVIEW.md at the repo root (and in subdirectories) with review-only rules;
critic applies it after the brief's contract and before its own defaults.`

## Risks And Compatibility

- Message changes break tests that assert the old text (test_deploy.py:245, 268, 729, 733, 827,
  1457). P1 U2 updates them in the same unit; the Interfaces fragments are the contract.
- The preflight (D-51) changes the order of `install_cmd`; `collect_source` already runs first,
  so the visible change is that registry and launcher errors arrive before any write. `--dry-run`
  must still run the preflight and still write nothing (test_deploy.py dry-run tests).
- `critic.md` lands at 583 words (17 of headroom left); any later addition must trim first.
  `tests/test_pack_lint.py` enforces it.
- `${CLAUDE_SKILL_DIR}` expansion in preloaded skills (P-05) is unverified. The fix names the path
  the same way `git-safety` already does, so nothing gets worse; if the user observes it does
  not expand, the follow-up is to name the deployed path in both places.
- Until P4 bumps `VERSION`, `tests/test_version.py` fails on the dirty tree by design; P1-P3
  validate with their own test files and leave that test to P4.

## Acceptance Criteria

- Every finding above is fixed as described or carries a `reject:` reason or an OQ decision
  recorded in `## Open Questions` after the user answers.
- `/usr/bin/python3 -m py_compile deploy` passes; `python3 -m pytest -q` passes with the new
  tests, including at least eight `test_doctor_*` tests and the `confirm` tests.
- No `deploy` error, WARN or FAIL message lacks a next step: `grep -nE 'DeployError\(|add\("(WARN|FAIL)"|print\(".*(ERROR|WARNING)' deploy` reviewed line by line by P1's critic round.
- `REVIEW.md` exists at the root with the four Always-check areas, Severity and Evidence
  sections; `CLAUDE.md` is unchanged and holds no review-only rules.
- `pack/agents/critic.md` contains the Project rules bullet and `tests/test_pack_lint.py` passes
  (it caps the body at 600 words).
- `docs/architecture.md` matches every agent's frontmatter and names the `REVIEW.md` behavior.
- A fresh temp-HOME run of the README Quick Start (`doctor`, `install`, `status`, `doctor`)
  matches the docs line for line: one WARN before install, a PATH hint after install, zero
  WARN/FAIL after.
- Every command in `README.md` and `docs/deploy.md` exists with the flags shown
  (`./deploy <sub> --help`).

## Validation Commands

- P1: `python3 -m pytest -q tests/test_deploy.py tests/test_pack_lint.py`;
  `/usr/bin/python3 -m py_compile deploy`; `/usr/bin/python3 ./deploy --help`;
  `HOME=$(mktemp -d) ./deploy doctor` (expect one WARN, exit 0, with `claude` on PATH).
- P2: `grep -oE '(\./|"\$REPO/")deploy [a-z]+( --?[a-z-]+)*' README.md docs/deploy.md | sort -u`,
  then `./deploy <sub> --help` for each subcommand named, checking every flag exists.
- P3: `python3 -m pytest -q tests/test_pack_lint.py`;
  `grep -n REVIEW.md pack/agents/critic.md docs/architecture.md`.
- P4: `python3 -m pytest -q` after the `VERSION` bump (expect all passed, 5 skipped); the temp-HOME
  Quick Start run from Acceptance Criteria; `git diff --cached --stat -- VERSION` non-empty before
  the commit.

## Scope Notes

- **In:** the fixes in `## Findings` marked `fix`; `REVIEW.md`; the `critic.md` bullet; the
  architecture and README sync for it; tests for changed behavior and for `doctor`.
- **Out:** new `deploy` flags or subcommands (the PATH hint at install end reuses `migrate`'s
  existing check and is a message, not a feature); raising any word cap; rewrites of `README.md`,
  `docs/deploy.md` or `deploy` beyond the listed findings; ROADMAP item 2; test refactors not
  needed by a new test (T-14, T-18); fixing archived plans (A-01).
- **Scope creep to resist:** turning the preflight into a general validation framework (one
  function, called twice); adding doctor rows for new conditions (U-09's optional collision row is
  out); restructuring `install_cmd` to write the manifest incrementally (D-07 rejected);
  "hardening" every `json.load`; rewording messages the findings do not name; adding clauses to
  `critic.md` for `REVIEW.md` edge cases; growing `REVIEW.md` past one screen.
- **User decisions executor must not reopen:** the `REVIEW.md` precedence (contract, then
  `REVIEW.md`, then critic defaults; never the user's task decisions); critic discovers
  `REVIEW.md` itself (root plus directories of changed or artifact files) rather than receiving it
  from the lead; no word cap is raised; the package split below.

## Work Packages

### P1: Code fixes and tests
- Goal: `deploy` and `tests/` fixes for every D-*, T-*, U-01, U-02, U-08, U-15 row marked `fix`;
  done when the P1 validation commands pass and the critic round (domain `code`) returns PASS.
- Owns: `deploy`, `tests/`
- Deps: none
- Stages: execute
- Status: done
- Artifacts: ->

### P2: Docs for the new-user journey
- Goal: `README.md` and `docs/deploy.md` carry the U-* fixes and the `REVIEW.md` sentence, written
  to the message texts in Interfaces; done when the P2 validation passes and the critic round
  (domain `prose`) returns PASS.
- Owns: `README.md`, `docs/deploy.md`
- Deps: none
- Stages: execute
- Status: done
- Artifacts: ->

### P3: REVIEW.md, critic wiring, pack fixes
- Goal: `REVIEW.md` created, `critic.md` applies it, P-* fixes applied, `docs/architecture.md`
  in sync; done when `tests/test_pack_lint.py` passes and the critic round (domain
  `agent-definition`) returns PASS.
- Owns: `REVIEW.md`, `pack/`, `docs/architecture.md`
- Deps: none
- Stages: execute
- Status: done
- Artifacts: ->

### P4: Integration and landing
- Goal: one change set on `main`: `VERSION` bumped, full suite green, docs verified against the
  tool, ROADMAP item 1 removed, this plan archived; done when the commit is on `main` and the user
  has run `./deploy install`.
- Owns: `VERSION`, `ROADMAP.md`, `docs/plan-full-review.md` (move)
- Deps: P1, P2, P3
- Stages: execute
- Status: done
- Artifacts: commit on main

## Orchestration

Default partition for `executor`. P1-P3 run in parallel in one working tree with disjoint files
and commit nothing; P4 lands everything in one commit (OQ1 default).

| Pkg | Unit | Owns | Validation by the worker |
|---|---|---|---|
| P1 | U1 (deploy) | `deploy` | `/usr/bin/python3 -m py_compile deploy`; `python3 -m pytest -q tests/test_deploy.py -x` once U2 lands |
| P1 | U2 (tests) | `tests/test_deploy.py`, `tests/test_pack_lint.py` | `python3 -m pytest -q tests/test_deploy.py tests/test_pack_lint.py` (new tests written to the Interfaces fragments; they fail until U1 lands) |
| P2 | U3 (README) | `README.md` | the P2 grep and `--help` check |
| P2 | U4 (deploy.md) | `docs/deploy.md` | the P2 grep and `--help` check; the Doctor Checks table against the D-57/D-58/D-59 texts |
| P3 | U5 (review wiring) | `REVIEW.md`, `pack/agents/critic.md`, `pack/skills/agent-authoring/SKILL.md`, `docs/architecture.md` | `python3 -m pytest -q tests/test_pack_lint.py` |
| P3 | U6 (pack fixes) | every other `pack/` file named in Findings | `python3 -m pytest -q tests/test_pack_lint.py` |

- Waves: within P1, U1 and U2 run in parallel against the Interfaces contract, then the lead runs
  the P1 validation. Within P2 and P3 the two units run in parallel. P4 is one unit.
- `executor` glue per package: integrate the units, run the package's validation commands, run
  critic (domain per package) and scope-critic. No `VERSION` bump and no commit. U6 reports the
  architecture.md lines it needs (P-03, P-04) and U5 applies them; the texts are in Interfaces.
- P4 glue: `printf '1.20\n' > VERSION`, `python3 -m pytest -q`, the temp-HOME Quick Start run and
  the P2 grep check against the merged tree, the ROADMAP edit, `git mv docs/plan-full-review.md
  docs/archive/`, commit through `git-ops` with `VERSION` staged; the user runs `./deploy install`.

## Open Questions

- **OQ1 Landing granularity.** Default: P1-P3 execute in parallel and land together in one commit
  at P4 with one `VERSION` bump, as ROADMAP's one-item-one-change-set rule reads. Alternative: one
  commit per package in sequence (P1, then P2, then P3), as the install-lifecycle program did; that
  gives three single-domain diffs but serializes the packages: `P2 Deps: P1`, `P3 Deps: P2`,
  `VERSION` added to each package's Owns and bumped in each glue, and the temp-HOME docs check
  moves into P2's glue.
  Decision: default; one commit at P4.
- **OQ2 Anticipated-failure clauses (P-15..P-19).** Which to delete? Default: delete P-18
  (`warn immediately if a conflict involves credentials`, already covered by git-safety L26) and
  P-19 (the `Edge cases` sections restate Rules); keep P-15, P-16, P-17 unless you recall no
  observed failure behind them.
  Decision: P-15 to P-18 deleted.
  P-19: deletion reverted per user; document-extraction and email-extraction edge-case sections kept as at HEAD.
- **OQ3 `test_version.py` on a clean tree (T-09).** Should the test also compare `HEAD:VERSION`
  with `HEAD~1:VERSION` when the tree is clean on `main`, so a forgotten bump fails after the
  commit? Default: no; `CLAUDE.md` defines the rule at the working-tree checkpoint, and the
  `git-ops` escalation covers the commit step.
  Decision: default; no `HEAD~1` check.

## Todo

- [x] User approves the plan and answers OQ1-OQ3, or accepts the defaults
- [x] P1 U1: every `deploy` row marked `fix`; the preflight (D-51) before its callers; messages to
  the Interfaces fragments
- [x] P1 U2: env whitelist and `stub_claude` helper first (T-03), then `test_doctor_*` (T-01),
  `confirm` tests (T-02), the other T-* rows marked `fix`, the six updated asserts, one test per
  Interfaces fragment
- [x] P1 glue: P1 validation commands, critic (`code`) and scope-critic
- [x] P2 U3: every `README.md` row marked `fix` plus the `REVIEW.md` sentence
- [x] P2 U4: every `docs/deploy.md` row marked `fix`
- [x] P2 glue: P2 grep and `--help` check, critic (`prose`) and scope-critic
- [x] P3 U5: `REVIEW.md`; critic.md bullet and P-08 sentence; agent-authoring L21-22 (P-04);
  architecture.md L16, L34, L36, L37, L50, L73
- [x] P3 U6: the other P-* rows marked `fix`; OQ2 deletions if approved
- [x] P3 glue: `tests/test_pack_lint.py`, critic (`agent-definition`) and scope-critic
- [x] P4: `VERSION` 1.20, full pytest, temp-HOME Quick Start run, ROADMAP item 1 deleted and
  item 2 renumbered with its `Depends on item 1.` dropped, `git mv` this plan to `docs/archive/`,
  commit; user runs `./deploy install` (left to the user)
