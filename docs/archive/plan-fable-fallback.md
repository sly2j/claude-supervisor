# Plan: Fable-to-Opus fallback at deploy time

Fact base: `docs/research-fable-fallback.md` is not checked in; the reviewed research lives at the session scratchpad path given in the brief. All line numbers below were re-verified against `scripts/deploy` at commit 84a95a9.

## Goal

Add `scripts/deploy install --fable {auto,yes,no}`. When Fable is off, the deployed copies of the three Fable agents and the two prose dispatch overrides say `opus` instead of `fable`. The choice is auto-detected from `claude auth status --json`, asked once when unclear, persisted in the manifest, honored by later installs, shown by `status`, and hashed so `status` never reports a false `outdated` or `modified`.

## Approach

Deploy-time rewrite (Option A of the research), chosen by the user. One regex, `\bmodel:[ \t]*fable\b` -> `model: opus`, applied to the bytes of every `agents/*.md` file when Fable is off. It covers the frontmatter `model: fable` line in `supervisor.md:4`, `planner.md:4`, `scope-critic.md:4` and the prose tokens at `planner.md:34` and `writer.md:26` without per-file cases. The rewrite is applied in one helper, `deployed_bytes()`, and every hash and copy site uses that helper's output, so the manifest baseline is the hash of what is on disk.

Rejected, one line each:
- Runtime fallback (`fallbackModel`, hooks, `ANTHROPIC_DEFAULT_FABLE_MODEL`): not conditional on the plan, or unverified; out of scope by the brief.
- Rewriting skills too: `pack/skills/agent-authoring/SKILL.md:21` has the same token, but it documents the source convention and the lint, so the deployed skill stays verbatim.
- Bumping `MANIFEST_VERSION`: the new key is optional and additive; the loader only checks the version, and bumping would make every existing install fail `load_manifest`.
- Changing `doctor`: `status` shows the choice; doctor has no INFO level and nothing to pass or fail.
- Making `planner.md:3` ("critic (run on Fable)") model-neutral: it does not simplify the rewrite; see Open Questions.

## Files

Modify:
- `scripts/deploy`: new `--fable` flag, detection, prompt, rewrite helper, hash sites, manifest key, `status` line.
- `tests/test_deploy.py`: isolate detection in `run()`, add a `fable_pack` fixture and the tests listed below, add `--fable yes` to the two in-process installs.
- `tests/test_pack_lint.py`: one test that the rewrite covers the real pack.
- `docs/deploy.md`, `README.md`, `docs/architecture.md`: document the flag, detection, persistence and troubleshooting.

Create: nothing besides this plan.

## Interfaces And Data Changes

### CLI

`install --fable {auto,yes,no}`, `default=None`. Resolution order in `resolve_fable(args, manifest) -> Tuple[bool, str]` (returns `enabled, reason`):

1. `--fable yes` / `--fable no`: use it. Reason `"--fable yes"` / `"--fable no"`.
2. Flag omitted and the manifest has `fable.enabled` (a bool): use it. Reason `"saved choice; pass --fable auto|yes|no to change"`.
3. Otherwise (flag omitted with no saved choice, or `--fable auto`): `detect_fable()`.
   - Verdict `True`/`False`: reason `"auto: <detail>"`.
   - Verdict `None` (unclear): `ask_fable(detail, args.yes)`. If it returns a bool, reason `"asked: <detail>"`. If it returns `None` (no TTY or `--yes`), enabled is `False` and reason is `"unclear (<detail>); defaulted to opus, pass --fable yes to override"`.

`--yes` help text becomes: "do not prompt (answers yes to --overwrite-local; an unclear Fable detection then defaults to Opus)".

`--dry-run` runs the same resolution, including the question, so the preview matches a real run; it persists nothing.

### Detection

`detect_fable() -> Tuple[Optional[bool], str]`: `True` means Fable, `False` means Opus, `None` means ask. No network and no model requests; it only runs `claude auth status --json` (timeout 30 s, like `doctor`'s `claude --version`) and reads one local JSON file.

| Observation | Verdict | Detail string contains |
|---|---|---|
| `shutil.which("claude")` is None | False | `claude CLI not found` |
| `subprocess.run` raises `OSError` / `SubprocessError` (incl. timeout) | False | `claude auth status failed` |
| Exit code != 0 | False | `claude auth status exited <n>` (not logged in, or `--json` unsupported) |
| stdout is not a JSON object | False | `no JSON` |
| `apiProvider` present and != `firstParty` | False | `apiProvider=<value>` |
| `authMethod` in `api_key`, `api_key_helper` | None | `authMethod=<value>` |
| `subscriptionType` (lowercased) starts with `max` | True | `subscriptionType=<value>` |
| starts with `pro` or `free` | False | `subscriptionType=<value>` |
| starts with `team` or `enterprise`: `seatTier` found and contains `premium` | True | `seatTier=<value>` |
| same, `seatTier` found without `premium` | False | `seatTier=<value>` |
| same, `seatTier` not found | None | `seat tier unknown` |
| anything else (missing or unrecognized `subscriptionType`) | None | `subscriptionType=<value> not recognized` |

Checks run in table order (provider, then auth method, then subscription). The strings in the last column are the test contract; the full wording is the executor's.

`_seat_tier(auth: dict) -> Optional[str]` reads `oauthAccount.seatTier` from `<configDirectory>/.claude.json` (the layout when `CLAUDE_CONFIG_DIR` is set) if that file is readable, else from `~/.claude.json` (the default layout, where the config dir is `~/.claude` and the file sits beside it). Every read is wrapped in `try/except (OSError, ValueError, AttributeError)`; any failure yields `None`.

`ask_fable(detail: str, assume_yes: bool) -> Optional[bool]`: returns `None` when `assume_yes` or `not sys.stdin.isatty()` (it never raises, unlike `confirm()`); otherwise prompts `Cannot tell whether your plan includes Fable (<detail>). Run the Fable agents on Fable? [y/N]` and returns `True` only for `y`/`yes`.

### Rewrite

```python
FABLE_TOKEN = re.compile(r"\bmodel:[ \t]*fable\b")

def deployed_bytes(key: str, src: Path, fable: bool) -> bytes:
    data = src.read_bytes()
    if fable or not (key.startswith("agents/") and key.endswith(".md")):
        return data
    return FABLE_TOKEN.sub("model: opus", data.decode("utf-8")).encode("utf-8")
```

`collect_source` has already rejected non-UTF-8 agents, so no new error path. The `\b` before `model` keeps `submodel:` untouched; `[ \t]*` keeps the match on one line; line endings pass through unchanged. `effort:` lines are untouched. When `fable` is `True` the output is byte-identical to the source, so `--fable yes` reproduces today's install exactly.

`sha256_bytes(data: bytes) -> str` joins `sha256_file`.

### Hash and copy sites (current line numbers)

- `install_cmd` loop, line 415: `data = deployed_bytes(key, src, fable); src_hash = sha256_bytes(data)`.
- Copies at lines 409 (inside `overwrite()`), 426 and 447: write `data` with the source mode. Smallest diff: give `atomic_copy` an optional `data: Optional[bytes] = None` parameter (`src.read_bytes() if data is None else data`) and pass `data` at all three sites; `overwrite()` gains a `data` argument.
- `file_states`, line 533: `sha256_bytes(deployed_bytes(key, src_files[key], fable_enabled(manifest))) != h`.
- `uninstall_cmd` line 591 compares target bytes with the manifest baseline only; no change.

### Manifest

`MANIFEST_VERSION` stays `1`. New optional top-level key written by every install:

```json
"fable": {"enabled": false, "reason": "auto: subscriptionType=pro"}
```

Two readers, two defaults, on purpose:
- `resolve_fable`: a missing key means "no saved choice", so it auto-detects (step 3 above).
- `fable_enabled(manifest) -> bool` (used by `file_states`): a missing key means `True`, because installs made before this change deployed the source verbatim. `return not isinstance(rec, dict) or rec.get("enabled") is not False`.

Old script reading a new manifest: ignores the key. New script reading an old manifest: detects on the next install, then writes the key.

### Output

- `install` prints, right after the `install <src> -> <target>` line: `Fable: on (<reason>)` or `Fable: off (<reason>); fable agents deploy as opus`.
- `status` prints, after `Installed:`: `Fable: on (<reason>)`, `Fable: off (<reason>)`, or `Fable: not recorded (installed verbatim; the next install detects)`.

Tests assert on the substrings `Fable: on`, `Fable: off` and `Fable: not recorded`.

## Steps

1. `scripts/deploy`, new section `# --- fable` after `git_info`: add `FABLE_TOKEN`, `deployed_bytes`, `sha256_bytes`, `fable_enabled`, `_seat_tier`, `detect_fable`, `ask_fable`, `resolve_fable` as specified. Use `Optional`/`Tuple` from `typing`, no `X | Y` syntax, no new imports beyond the stdlib already imported.
2. `scripts/deploy` `install_cmd`: inside `target_lock`, right after `manifest = load_manifest(target) or {}` (line 399), call `fable, fable_reason = resolve_fable(args, manifest)` and print the `Fable:` line. Thread `data` through lines 404-411, 415, 426 and 447. Add `"fable": {"enabled": fable, "reason": fable_reason}` to `new_manifest` (lines 488-496).
3. `scripts/deploy` `file_states` and `status_cmd`: compare against `deployed_bytes(...)` at line 533; print the `Fable:` line after line 551.
4. `scripts/deploy` `build_parser`: add `--fable` to `install` (lines 750-762) with `choices=("auto", "yes", "no")`, `default=None`, help: "run the Fable agents on Fable (yes), on Opus (no), or detect from `claude auth status` (auto); default: the choice saved by the last install, else auto". Update the `--yes` help text.
5. `tests/test_deploy.py`, isolation first:
   - `run()` sets `env["PATH"] = str(target.parent / "bin")` and `env["HOME"] = str(target.parent)`, and passes `stdin=subprocess.DEVNULL` so the child never sees a TTY even under `pytest -s`. The `bin` directory need not exist; `shutil.which("claude")` then returns `None`, so every existing test takes the "claude CLI not found -> opus" path, which is a byte-level no-op for the `model: sonnet` fixtures. `git_info` tolerates a missing `git` (returns `None, None`), and no test asserts on `source_commit`.
   - Add `"--fable", "yes"` to the two in-process `parse_args` lists (lines 305 and 328-329); they run `install_cmd` with the real `PATH` and must never reach detection.
   - Helper `fake_claude(target, stdout: str, code: int = 0)`: writes an executable script at `target.parent / "bin" / "claude"` with a `#!` + `sys.executable` shebang whose body is `import sys; sys.stdout.write(<stdout literal>); sys.exit(<code>)`, for any arguments. Not `#!/bin/sh` with `cat`: the restricted `PATH` has no `/bin`, so external commands fail and every case would silently take the `no JSON` branch; a Python shebang is also quote-safe for the JSON.
   - Fixture `fable_pack(pack)`: adds `agents/planner.md` with `model: fable`, `effort: xhigh` and a body line ``Dispatch `critic` (`model: fable`, domain `plan`).`` plus a line `Critic runs on Fable.` (must survive the rewrite); returns `pack`.
6. `tests/test_deploy.py`, new tests (all through `run()` unless noted):
   - `test_fable_off_rewrites_agents`: `install --fable no`; deployed planner frontmatter `model: opus`, `effort: xhigh`, body contains `` `model: opus` `` and `Critic runs on Fable.`, no `model: fable` anywhere under `target/agents`; `helper.md` and the skill files byte-identical to source; `manifest()["fable"] == {"enabled": False, "reason": "--fable no"}`; stdout contains `Fable: off`.
   - `test_fable_yes_is_verbatim`: `install --fable yes`; every deployed file equals its source bytes; manifest `enabled` is `True`; stdout contains `Fable: on`.
   - `test_fable_choice_persists`: `install --fable no`, then `install` with no flag: stdout has `copied=0, updated=0` and `Fable: off`, file still `model: opus`, manifest still `enabled: False`; then `status`: every row `ok`, no `outdated`, stdout has `Fable: off`.
   - `test_fable_switch_updates`: `--fable no`, then `--fable yes` gives `updated=1` and a verbatim planner, then `--fable no` gives `updated=1` and `model: opus` again.
   - `test_fable_auto_without_claude`: `install` with no flag and no manifest: stdout has `Fable: off` and `claude CLI not found`; planner rewritten; exit 0.
   - `test_fable_auto_detection`, parametrized `(stdout, code, expect_on, expect_substring)` over: max -> on, `subscriptionType`; pro -> off; free -> off; `apiProvider: "bedrock"` -> off, `apiProvider`; `authMethod: "api_key"` -> off, `defaulted to opus`; team with a `.claude.json` holding `seatTier: team_labs_premium` in the fake `configDirectory` -> on, `seatTier`; team with `seatTier: team_standard` -> off; team with no `.claude.json` -> off, `defaulted to opus`; exit code 1 -> off, `exited 1`; non-JSON stdout -> off, `no JSON`; `subscriptionType: "whatever"` -> off, `not recognized`. Each case asserts the planner model and the manifest `enabled` value. The team cases point `configDirectory` at `target.parent / "cfg"` and write `cfg/.claude.json`.
   - `test_fable_explicit_auto_rediscovers`: `install --fable no`, then `fake_claude(max)` and `install --fable auto`: stdout `Fable: on`, `updated=1`, verbatim planner.
   - `test_fable_old_manifest_not_recorded` (the upgrade path): `install --fable yes` on `fable_pack`, pop the `fable` key from the manifest JSON on disk; `status` prints `Fable: not recorded` and every row `ok`; a flagless `install` then prints `Fable: off`, `updated=1`, and writes `enabled: False`.
   - `test_fable_prompt_when_unclear` (in-process via `load_deploy()`, `monkeypatch`): set `deploy.detect_fable = lambda: (None, "authMethod=api_key")`, replace `sys.stdin` with a `StringIO` subclass whose `isatty()` returns `True` and whose content is `"y\n"` (`input()` reads `sys.stdin.readline()` when stdin is not the console); run `install_cmd` with `--fable auto`; manifest `enabled` is `True` and reason starts with `asked:`. A second parametrized case feeds `"\n"` and expects `False`. A third case uses `--yes` and expects `False` with reason containing `defaulted to opus` and no read from stdin.
   - `test_help`: also assert `--fable` in the `install --help` output.
7. `tests/test_pack_lint.py`: `test_fable_rewrite_covers_pack`: for every real `pack/agents/*.md`, `text = deploy.deployed_bytes("agents/" + path.name, path, False).decode()`; assert `"model: fable" not in text`, the parsed `model` is `opus` when the source said `fable` and unchanged otherwise, and `effort` is unchanged. With `fable=True`, the bytes equal `path.read_bytes()`.
8. `docs/deploy.md`: new section `## Fable Or Opus` after "What Install Does" covering the flag, the detection table in user terms (Max and premium Team/Enterprise seats keep Fable; Pro, Free, standard seats, Bedrock/Vertex/Foundry and any detection failure get Opus; API-key users and unclear cases are asked once), persistence (`status` shows it; re-run `install --fable yes|no|auto` to change), and the no-TTY default. Add to "Notes For Claude Running This": Bash has no terminal, so an unclear detection defaults to Opus and says so; relay that and offer `install --fable yes`. Update the install steps block with a `--fable` comment.
9. `README.md`: one sentence under the Agents table (after line 54): rows marked `fable` run on Opus when the pack is installed with `--fable no` or when `install` detects a plan without included Fable (link to `docs/deploy.md`). One troubleshooting row: "Claude Code asks to bill Fable to usage credits" -> `scripts/deploy install --fable no`; `status` prints the current choice.
10. `docs/architecture.md:52`: append one sentence: on plans without included Fable, `scripts/deploy install` deploys those agents and dispatch overrides on Opus (`--fable`, see `docs/deploy.md`); the source stays on Fable and the lint checks the source.
11. Validate (commands below), then run a real-pack install into a scratch target under both Pythons and inspect the output.

## Risks And Compatibility

- Existing installs: the manifest lacks the key, so the next `install` auto-detects. Max and premium-seat users see `unchanged`; Pro users see three `update` lines. A user who edited one of the three agents locally keeps the edited file (`kept-local`), which stays on its old model; `status` shows it as `modified`, as today.
- Detection depends on unverified strings; see the assumptions below. Every unknown value is `None` (ask) or `False` (opus), never `True`, so a wrong guess costs a prompt or a rerun with `--fable yes`, never an unwanted Fable bill.
- `~/.claude.json` is undocumented and may move or change shape. Failure to read it yields "ask" on Team/Enterprise and never crashes.
- Org-disabled Fable on Enterprise premium seats: the pack deploys `fable`, and Claude Code's own `availableModels` substitution applies (research 2a). Acceptable; `--fable no` fixes it.
- `pack/skills/agent-authoring/SKILL.md:21` still says the planner dispatches critic with `model: fable` after an Opus install. It describes the source, which is correct.
- `tests/test_deploy.py::run()` now hides `git` and `claude` from every subprocess test. Nothing in the suite depends on them.

Assumptions to verify during execution (the research saw only a Team premium account):
- A1: `subscriptionType` is `pro`, `max`, `free`, `team`, `enterprise` (prefix match, case-insensitive). If `claude auth status --json` on the executor's machine shows a different vocabulary, extend the table; the unknown branch asks.
- A2: `claude auth status --json` on the pinned minimum version 2.1.293 supports `--json`; it does on 2.1.300. A non-zero exit on older versions yields opus.
- A3: `.claude.json` is `$CLAUDE_CONFIG_DIR/.claude.json` when the variable is set and `~/.claude.json` otherwise (verified for the default layout on this machine: `~/.claude.json` exists, `~/.claude/.claude.json` does not). Check whether `claude auth status --json` already exposes a seat-tier field; if it does, read it from there first and keep the file as the fallback.

The `--fable auto --dry-run` command in the validation list exercises A1-A3 on the executor's machine (Team premium: expect `Fable: on (auto: ... seatTier=...)`) without writing anything.

## Acceptance Criteria

1. `scripts/deploy install --help` lists `--fable {auto,yes,no}`.
2. `install --fable no` from the real pack: the deployed `supervisor.md`, `planner.md`, `scope-critic.md` have `model: opus` with their `effort` unchanged; `grep -rn "model: fable" <target>/agents` finds nothing; `writer.md:26` and `planner.md:34` read `` `model: opus` ``; every other file is byte-identical to its source.
3. `install --fable yes`: every deployed file is byte-identical to its source (today's behavior).
4. After either, `install` without a flag reports `copied=0, updated=0`, and `status` shows every file `ok` plus a `Fable: on|off (...)` line. Switching `yes` -> `no` -> `yes` updates exactly the three agents plus `writer.md` each time.
5. With no `claude` on `PATH`, a flagless first install chooses Opus, says `claude CLI not found`, and exits 0.
6. Detection follows the table; an unclear result without a TTY or with `--yes` chooses Opus and prints `defaulted to opus`; with a TTY it asks once, and the next flagless install does not ask again.
7. No test executes the real `claude` binary or reads the real `~/.claude.json`: `run()` isolates `PATH` and `HOME`, and the in-process installs pass `--fable yes`.
8. `python3 -m pytest -q` passes; `scripts/deploy` still imports and runs under `/usr/bin/python3` (3.9).
9. `README.md`, `docs/deploy.md` and `docs/architecture.md` describe the flag; the README inventory keeps its model column unchanged and gains the fallback note.

## Validation Commands

```bash
cd "$REPO"                                            # the repo checkout
python3 -m pytest -q
/usr/bin/python3 -m py_compile scripts/deploy
/usr/bin/python3 scripts/deploy install --help | grep -- --fable
S=$(mktemp -d)/fable-target
/usr/bin/python3 scripts/deploy install --fable auto --dry-run --target "$S" | grep "Fable:"   # runs detect_fable under 3.9 against the real CLI; writes nothing; expect "Fable: on (auto: ...)" on this Team-premium machine
/usr/bin/python3 scripts/deploy install --fable no --target "$S" && grep -rn "model: fable" "$S/agents"; echo "exit $? (1 = none found)"
grep -n "model: opus" "$S/agents/supervisor.md" "$S/agents/planner.md" "$S/agents/scope-critic.md" "$S/agents/writer.md"
python3 scripts/deploy install --target "$S" | grep -E "Fable:|Summary"      # expect Fable: off, updated=0
python3 scripts/deploy status --target "$S" | grep -E "Fable:|outdated|modified"  # expect only the Fable line
python3 scripts/deploy install --fable yes --target "$S" | grep -E "Fable:|Summary"  # expect updated=4
diff -r pack/agents "$S/agents" && echo verbatim
grep -n -i "fable" README.md docs/deploy.md docs/architecture.md
```

Do not run `scripts/deploy install` against the real `~/.claude` during validation; the user deploys per `docs/deploy.md`.

## Open Questions

1. `pack/agents/planner.md:3` (description: "iterates with critic (run on Fable)") is informational prose that the rewrite leaves alone, so an Opus install still says it. Reword it to be model-neutral (for example "critic (on the plan review tier)")? Default: leave it.

## Todo

- [x] `scripts/deploy`: fable section (`FABLE_TOKEN`, `deployed_bytes`, `sha256_bytes`, `fable_enabled`, `_seat_tier`, `detect_fable`, `ask_fable`, `resolve_fable`)
- [x] `scripts/deploy`: `install_cmd` resolution, `Fable:` line, `data` at lines 409/415/426/447, manifest key
- [x] `scripts/deploy`: `file_states` line 533 and `status_cmd` `Fable:` line
- [x] `scripts/deploy`: `--fable` flag and `--yes` help text
- [x] `tests/test_deploy.py`: `run()` isolation (`PATH`, `HOME`, `stdin=DEVNULL`), `--fable yes` in the two in-process installs
- [x] `tests/test_deploy.py`: `fake_claude` helper (Python shebang) and `fable_pack` fixture
- [x] `tests/test_deploy.py`: rewrite, verbatim, persistence, switch, no-claude, detection table, explicit auto, old-manifest, prompt, help tests
- [x] `tests/test_pack_lint.py`: `test_fable_rewrite_covers_pack`
- [x] `docs/deploy.md`: `## Fable Or Opus` section, runbook note, steps comment
- [x] `README.md`: inventory note and one troubleshooting row
- [x] `docs/architecture.md`: one sentence in Models And Cost
- [x] Validation commands pass under `python3` and the 3.9 smoke commands pass under `/usr/bin/python3`
