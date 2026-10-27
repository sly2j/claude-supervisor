# Plan: API-provider installs with per-tier model picks

Research: `.supervisor/working/research/api-access-install.md` (sections cited as R§n).
Branch: `worktree-api-access-install`. Release: next minor unless the user calls it major at landing.

## Goal

Make `./deploy install` into a provider profile user-friendly: presets for OpenRouter, NRP and ALCF, a generic `--base-url` flow, static tokens or an expiring-token helper, and the four tiers (Fable, Opus, Sonnet, Haiku) mapped to models picked from the provider's list, interactively or by flag. Subscription installs (no provider flags) keep today's launcher, settings, prompts and flags byte for byte.

Non-goals: changes under `pack/agents` or to the pack lint; bridging OpenAI-only endpoints (ALCF Sophia and Metis get one doc sentence, R§4c-d); a live completion check; `--global` provider installs.

Expected change size: `deploy` about +330/-20 lines, `tests/test_deploy.py` about +280, docs about +90/-15 across three files. This plan stays under that.

## Approach

All provider state is written by `install` and recorded in the manifest, as `base_url` is today (`deploy:836,956`), so `update` replays it from a fresh clone (`deploy:1297`) and the launcher stays self-contained. Tier models and the credential go through the launcher's exports (`deploy:104-109`), not `settings.json` `env`; the seeded `env` block, which would outrank them (R§3 Profiles), is filtered on provider installs. The only `settings.json` key install adds is `apiKeyHelper` for expiring tokens, managed the way `attribution.*` is (`deploy:632-660`). Model lists come from `urllib.request` with the same credential; the picker is a plain `input()` loop over a numbered, filterable list, and every tier can be given as a flag for scripts. Rejected: tier values in `settings.json` `env` (a per-session `--fable-is-opus` could never override them); `CLAUDE_CODE_SUBAGENT_MODEL` and install-time frontmatter rewrites (already rejected, `decisions/2026-10-23-fable-is-default-opus-is-opt-in.md`); gateway model discovery (`CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY`, feeds `/model`, not the tier aliases); a bundled bridge for OpenAI-only endpoints (non-stdlib, resident process, R§4d).

## Decisions

User decisions of 2026-10-27, not to be reopened:
- U1. Provider installs get an interactive per-tier picker and `--model-<tier>` flags; this supersedes `decisions/2026-10-24-deploy-never-detects-the-plan-or-model.md` for provider profiles only. Subscription installs stay non-interactive with no model prompt.
- U2. On a provider profile `--fable-is-opus` exports the Opus-tier model as `ANTHROPIC_DEFAULT_FABLE_MODEL`, never `claude-opus-5-5`.
- U3. Presets `--provider openrouter|nrp|alcf` fill base URL, auth style and model-list endpoint; `--base-url` stays for anything else.
- U4. Provider installs go in their own profiles; the subscription profile is never touched (`decisions/2026-10-24-product-text-says-profile-never-sandbox.md`).

Lead decisions:
1. A "provider install" is any install whose effective config has a base URL (from `--provider`, `--base-url`, or the manifest). No base URL means today's code path, unchanged, including the `--global` note at `deploy:837-838`.
2. Presets are one constant table in `deploy`: name, base URL, auth style (`token` or `helper`), default helper command, model-list URL, and a login hint. Values from R§4-5: OpenRouter `https://openrouter.ai/api`, token, list `https://openrouter.ai/api/v1/models?supported_parameters=tools`; NRP `https://ellm.nrp-nautilus.io/anthropic`, token, list `https://ellm.nrp-nautilus.io/v1/models`; ALCF `https://inference-api.alcf.anl.gov/resource_server/minerva/api`, helper `alcf-tokens get-token inference`, list `<base>/v1/models`. `--base-url` with `--provider` overrides the base URL only (ALCF Tara: swap `minerva` for `tara`). The generic flow uses `<base>/v1/models` (R§5 common shape; Claude Code's own discovery reads it).
3. Credentials: static tokens keep the shipped mechanism (`<dir>/token`, mode 0600, launcher `ANTHROPIC_AUTH_TOKEN="$(cat ...)"`). A new `--token-helper CMD` (mutually exclusive with `--token`/`--token-file`; the ALCF preset defaults to its helper) writes `settings.json` `apiKeyHelper` with the command's first word resolved to an absolute path (launchers bake absolute paths, `facts/2026-10-24-claude-config-dir-gives-each-dir-its-own.md`), deletes `<dir>/token` if present, and the launcher exports no `ANTHROPIC_AUTH_TOKEN`: a static export outranks the helper and never refreshes (R§3 apiKeyHelper). `apiKeyHelper` is managed like `attribution.*`: set when absent or when the manifest says install wrote it, a user's own value is kept with a warning. A static-token flag overrides a preset's helper default and removes a managed `apiKeyHelper` (a user's own value is kept, with the same warning), so a profile is never both.
4. Launcher environment on a provider profile, after the `CLAUDE_CONFIG_DIR` line: `ANTHROPIC_BASE_URL`; with a static token also `ANTHROPIC_API_KEY=''` (OpenRouter requires it empty, R§4a, and an inherited real Anthropic key must not reach a third party as `X-Api-Key`); with a helper instead `unset ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_KEY`, since either would outrank the helper (R§3); then the four `ANTHROPIC_DEFAULT_<TIER>_MODEL` exports and `ANTHROPIC_MODEL=<Opus-tier model>` (Claude Code's built-in main-model default is a Claude id the tier variables do not remap; NRP's recipe sets it, R§4b). The `--fable-is-opus` line keeps its shape with the Opus-tier model as value (U2). Existing generic `--base-url --token` launchers gain the `ANTHROPIC_API_KEY=''` line on their next install; everything else about them is unchanged.
5. Seeding (`deploy:735`) on a provider install drops `env` keys starting with `ANTHROPIC_` and the top-level `apiKeyHelper` from the copied `settings.json`; `doctor` prints a WARN naming any `ANTHROPIC_*` key found in the profile's `settings.json` `env` afterwards ("overrides the launcher; remove it"). Rejected: editing a user's `env` on later installs. Subscription seeding is unchanged.
6. Tiers are all-or-nothing: a preset install, or any install given a `--model-<tier>` flag, must end with all four tiers set from flags, then the manifest, then the picker. The generic flow asks `confirm("Map the model tiers to this provider's models?")` (the roadmap's "asks whether to configure the tiers") only when `--base-url` is on the command line, no model flag is given and the manifest records no models; a base URL taken from the manifest never asks, so plain re-installs and `update` stay silent. Declined or non-interactive, the tiers stay unset and an Anthropic-API gateway serving Claude ids keeps working as today. `--base-url ''` (or `--provider ''`) clears the whole provider config: base URL, auth style, helper key when managed, and models.
7. Prompting rules: the picker runs only when stdin is a TTY and a required tier is missing; without a TTY, or with `--yes`, a missing tier is a `DeployError` listing the exact `--model-<tier>` flags to pass, under `--dry-run` as well (nothing is written either way). `update` never prompts: it replays the manifest.
8. Model list: `fetch_models(url, bearer)` uses `urllib.request` with a 20 s timeout, sends `Authorization: Bearer` when a token or helper output is at hand, and returns entries `{id, name?, context_length?}` from `{data: [...]}`. Any failure (network, HTTP status, bad JSON) prints one WARNING with the URL and reason and continues with an empty list, so the picker accepts typed ids. The OpenRouter query filters tool-capable models server-side (R§5: 373 of 464); NRP and ALCF lists expose no capability field, so no filter. Rejected: paging or a curses UI.
9. Picker UX (`pick_model(tier, entries, default)`): one prompt per tier in the order Fable, Opus, Sonnet, Haiku. Input: a number picks from the last shown list; an exact id picks it; any other text filters ids case-insensitively and shows up to 30 numbered matches with context length when known and "and N more; narrow the filter" beyond that; `?` or empty input shows the first 30 (or the current filter); from the second tier on, empty input repeats the previous tier's pick (ALCF has one model, R§4c). A typed id not in a fetched list asks `confirm("... is not in the list; use it anyway?")`. Ctrl-D aborts as today (`deploy:1850`).
10. Validation at install, before any write: a helper command must exit 0 within 30 s and print exactly one non-empty line without whitespace, else a `DeployError` with the preset's login hint (`alcf-tokens login inference`; install via pipx, R§4c); a 401 or 403 from the model-list fetch is named in that fetch's WARNING (decision 8). The `confirm` of decision 9 applies to typed picker input only: an id from a flag or the manifest that is absent from a fetched list produces one WARNING naming it, so scripted installs and `update` replays never hit a prompt. No live completion request: it costs credits and proves little for tool use (R§3 wire format). `doctor` repeats the structural checks (decision 12).
11. Manifest fields added: `provider` (preset name or null), `auth` (`token`, `helper` or null), `token_helper` (command string, no secret), `models` (`{fable, opus, sonnet, haiku}` or null). `base_url` stays. On provider profiles only, `status` prints `Provider:`, `Base URL:`, `Auth:` and the four tier lines; neither token values nor helper output ever appear in output, manifest or `settings.json` (R§1 archived secrecy rule, restated in the docs).
12. `doctor` on a provider profile adds: PASS `provider: <name or custom>, base URL`, FAIL when `auth` is `token` and `<dir>/token` is missing or not 0600, FAIL when the helper fails decision 10's check, WARN per `ANTHROPIC_*` key in `settings.json` `env` (decision 5). Subscription profiles get no new rows.
13. `--global` rejects the new flags with the existing message (`deploy:202-207`); `migrate` is untouched (a global install has no provider).
14. Docs are a `writer` package (P2), separate from the executor's `--help` text and docstrings (P1). Memory changes happen at curator close-out (Todo), not in the branch's code work.
15. `VERSION` is not touched on the branch; the squash onto `main` raises y (`CLAUDE.md`, `decisions/2026-10-27-version-bumps-only-for-product-changes.md`).

## Outline

`deploy` (all additions beside the existing provider code):
- Constants near `OPUS_MODEL` (`deploy:55`): `TIERS = ("fable", "opus", "sonnet", "haiku")`, `PROVIDERS: Dict[str, dict]` per decision 2, `MODELS_TIMEOUT = 20`.
- `launcher_text(tag, target, prefix, base_url, has_token, models: Optional[dict], helper: bool)` at `deploy:80`: keep the existing lines; add the exports of decision 4 after `deploy:103`; the `--fable-is-opus` line (`deploy:109`) takes `models["opus"]` when `models` is set. The subscription output must stay identical: add a test that pins today's launcher text for a plain install.
- `target_tag` (`deploy:205`): extend the rejected-flag tuple with `provider`, `token_helper`, `model_<tier>`.
- `seed_profile(target, dry_run, provider: bool)` (`deploy:735`): the filter of decision 5 in the `settings.json` branch (`deploy:752-757`).
- `plan_api_key_helper(settings, prev, command) -> (new_settings, record, msg)` next to `plan_attribution` (`deploy:632`): same shape and manifest flags (`managed_api_key_helper`, `previous_api_key_helper`).
- `resolve_provider(args, manifest) -> dict` with keys `provider, base_url, auth, token_helper, models_url, models` merging flags over the manifest per decisions 1, 2, 6. It runs inside `install_preflight` (`deploy:786`) on the manifest already loaded there (`deploy:795`), so the helper is validated (decision 10) and its absolute path resolved before any write, on replays too; preflight returns the dict and `install_cmd` uses it in place of the `base_url` line at `deploy:836`. Mutual exclusion of `--token-helper` with the `tok` group (`deploy:1758`).
- `fetch_models(url, bearer) -> List[dict]`, `pick_model(tier, entries, default) -> str`, `choose_models(cfg, flags, interactive) -> Dict[str, str]` (decisions 7-9). Input goes through `builtins.input` and `sys.stdin.isatty()` like `confirm` (`deploy:186`), so `tty_deploy` (`tests/test_deploy.py:2071`) drives them.
- `install_cmd`: manifest fields (decision 11) in the dict at `deploy:945-958`; write `settings.json` through the existing ordered write (`deploy:960-968`); launcher call at `deploy:972` gets the models and helper flag; helper installs remove `<dir>/token`. Gotcha: the settings write and the manifest write are ordered so a crash never leaves an unrecorded managed key (comment at `deploy:960`); the helper key must follow that order.
- `status_cmd` (`deploy:1030`): provider lines after `Launcher:` (`deploy:1069`). `doctor_cmd` (`deploy:1588`): rows of decision 12 after the `env` checks (`deploy:1656-1667`).
- Parser (`deploy:1757-1760`): `--provider {openrouter,nrp,alcf,''}`, `--token-helper CMD`, `--model-fable/--model-opus/--model-sonnet/--model-haiku ID`; one-line help each, consistent with the existing `profile:` prefix. Module docstring (`deploy:2-4`) and `LAUNCHER_HELP` (`deploy:62-77`) mention providers in one line each.
- Python 3.9: no `match`, no `X | Y` annotations, no parenthesised context managers (`facts/2026-10-24-usr-bin-python3-3-9-6-has-no-pytest-so-t.md`).

`tests/test_deploy.py`: subprocess tests via `run` (`:56`) pass `--model-*` flags (no network); in-process tests use `load_deploy` (`:84`) and `tty_deploy` (`:2071`) with `monkeypatch.setattr(deploy, "fetch_models", ...)` or a fake `urllib.request.urlopen`; the launcher is exercised with `claude_stub`/`run_launcher` (`:722,733`), extended to print the new variables. Existing tests to extend: `test_profile_token_provider` (`:840`), `test_update_from_remote_replays_options` (`:1334`), help-flag loop (`:428`), `--global` rejection (`:944`).

Docs (P2): `docs/deploy.md`, `README.md`, `docs/architecture.md`; `docs/context-engineering.md` is not touched. Section-level edits in Slice 5.

## Slices

Each slice ends with `python3 -m pytest -q` green and `python3 -m py_compile deploy`; units within a slice are the executor's call (all touch `deploy` and `tests/test_deploy.py`, so one unit each).

### Slice 1: presets, helper auth, launcher env, manifest, status (P1)
Delivers: `install --tag or --provider openrouter --token-file F --model-fable A --model-opus B --model-sonnet C --model-haiku D` produces a working launcher; `--provider alcf` writes `apiKeyHelper`; `update` replays; `status` shows it; subscription output unchanged. Decisions 1-4, 6 (flags only), 10 (helper check), 11, 13.
Tests:
- `subscription_launcher_unchanged`: plain profile install -> launcher text equals the text pinned from `main` (no `ANTHROPIC_` line but the `--fable-is-opus` one), no new prompt, no new manifest keys with values, and `status` prints no `Provider:` line.
- `openrouter_preset_static_token`: `--provider openrouter --token x` + four model flags -> launcher exports base URL, `ANTHROPIC_API_KEY=''`, token, four tier vars, `ANTHROPIC_MODEL=B`; `--fable-is-opus` line carries B; manifest has `provider`, `auth: token`, `models`; `x` appears nowhere but `<dir>/token`.
- `alcf_preset_helper`: `--provider alcf` plus four model flags, with a stub `alcf-tokens` on PATH printing one line -> `settings.json` `apiKeyHelper` is the absolute stub path plus args, manifest `managed_api_key_helper`, no `<dir>/token`, launcher has `unset ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_KEY` and no token line; a second install with `--token x` -> managed `apiKeyHelper` removed, `<dir>/token` written, manifest `auth: token`.
- `helper_failing_is_a_clean_error`: stub exits 1, or prints two lines -> exit 2, message names the login hint, nothing written.
- `user_api_key_helper_is_kept`: profile `settings.json` already has `apiKeyHelper` -> kept, WARN in output, manifest flag false.
- `base_url_clears_provider_config`: install `--base-url ''` on a preset profile -> launcher back to the subscription shape, manifest provider fields null, managed helper key removed.
- `update_replays_provider`: extend `test_update_from_remote_replays_options` -> models, provider and auth survive the replay; launcher identical before and after; no prompt and no `confirm` call during the replay.
- `global_rejects_provider_flags`: `--global --provider nrp` and each new flag -> the existing "cannot be combined" error.
- `status_shows_provider_not_secret`: status output has `Provider: nrp` and four tier lines; no token value.
Checkpoint: `python3 -m pytest -q tests/test_deploy.py -k "provider or helper or launcher"`.

### Slice 2: seeding filter, tier rules, non-TTY and dry-run paths (P1)
Delivers: decisions 5, 6 (all-or-nothing, generic confirm), 7. The `env` guard and the scripted-use error messages.
Tests:
- `provider_seed_drops_anthropic_env`: `~/.claude/settings.json` with `env: {ANTHROPIC_DEFAULT_OPUS_MODEL, FOO}` and `apiKeyHelper` -> provider profile keeps `FOO`, drops the others; a subscription profile keeps all three (seed unchanged).
- `preset_without_tty_needs_flags`: `--provider nrp --token x` with stdin not a TTY -> exit 2, message lists the four missing `--model-<tier>` flags; same with `--yes` and with `--dry-run`.
- `partial_tier_flags_fail`: `--base-url U --token x --model-opus M`, no TTY -> exit 2 listing the three missing flags.
- `generic_without_models_is_quiet`: `--base-url U --token x`, no TTY -> exit 0, no tier exports (today's behaviour plus `ANTHROPIC_API_KEY=''`).
Checkpoint: `python3 -m pytest -q tests/test_deploy.py -k "seed or tier or generic"`.

### Slice 3: model-list fetch and the interactive picker (P1)
Delivers: decisions 8, 9 end to end in-process: a TTY install with a mocked list picks four models and writes them.
Tests:
- `fetch_models_parses_openai_shape`: fake `urlopen` returning `{data:[{id:"a",context_length:1}]}` -> `[{"id":"a","context_length":1}]`; request carries `Authorization: Bearer t` when a bearer is given and no header otherwise.
- `fetch_models_failure_warns_and_continues`: `urlopen` raising `URLError` -> `[]` and one WARNING line with the URL.
- `openrouter_list_url_filters_tools`: preset table -> OpenRouter `models_url` contains `supported_parameters=tools`.
- `pick_by_number_filter_and_exact`: entries `a1, b2, b3`; answers `["b", "2", "a1", "", "zz", "y"]` across tiers -> Fable `b3` (filter then number), Opus `a1` (exact), Sonnet `a1` (empty repeats), Haiku `zz` after the not-in-list confirm.
- `pick_shows_at_most_30`: 460 entries, answer `""` -> the prompt output lists 30 lines and "and 430 more".
- `generic_asks_before_mapping`: `--base-url U --token x` with a TTY, answer `n` -> no tier exports; answer `y` then four picks -> four tier exports.
- `tty_install_end_to_end`: `--provider nrp --token x` in-process with mocked list and answers -> launcher and manifest as in Slice 1.
Checkpoint: `python3 -m pytest -q tests/test_deploy.py -k "fetch_models or pick or tty_install"`.

### Slice 4: doctor rows and help text (P1)
Delivers: decision 12 and the code-level docs: `--help` lines, module docstring, `LAUNCHER_HELP`.
Tests:
- `doctor_provider_rows`: ALCF profile with a failing stub helper -> FAIL row; token profile with `<dir>/token` chmod 0644 -> FAIL; `env` with `ANTHROPIC_API_KEY` -> WARN; subscription profile -> no provider row.
- `help_lists_provider_flags`: extend the help-flag loop at `:428` with `--provider`, `--token-helper`, `--model-fable`.
Checkpoint: `python3 -m pytest -q && /usr/bin/python3 -m py_compile deploy && /usr/bin/python3 deploy install --help` (on a Mac with 3.9; elsewhere `python3`).

### Slice 5: documentation (P2, `writer`)
Delivers: a reader of `docs/deploy.md` can set up an OpenRouter, NRP or ALCF profile without reading `deploy`. Read commits `eaa82bd`, `a4e00e8`, `58ad9e6`, `136b621`, `38274cd` first and match their structure, voice and level of detail; light-touch edits, no rewrite of untouched sections; follow `conventions/2026-10-26-docs-are-for-users-not-prompts.md` and `conventions/2026-10-26-docs-describe-what-we-do-and-why.md`. Verify every flag and message against the P1 `--help` and tests.
- `docs/deploy.md`: new `## API Providers` between `## Fable Or Opus` and `## Codex As Critic`, with `### Presets` (three commands, one per provider; what each exports; the ALCF helper and its 48 h token; Tara via `--base-url`; one sentence that Sophia and Metis are OpenAI-only and need a bridge outside this tool), `### Model Tiers` (the picker, the flags, all-or-nothing, the generic `confirm`, `--fable-is-opus` on a provider profile, scripted use without a TTY), `### Changing Or Removing A Provider` (`--base-url ''`, re-running with new flags, `update` replay, the secrecy rule); `### Token Provider` (line 62) shrinks to its command plus a pointer to the new section; `## Fable Or Opus` gains one sentence for provider profiles; `## Update` (line 113) lists the replayed options; `## Doctor Checks` table gains the rows of decision 12; the `settings.json` bullet of `## What Install Does` gains one clause that provider installs may also set `apiKeyHelper` (link to `## API Providers`). Untouched: Steps, the other What Install Does bullets, Launcher, Codex As Critic, Uninstall, Migrate.
- `README.md`: the token-provider line at `README.md:245` (end of `## Maintaining An Install`) becomes two sentences on API providers with the link to `docs/deploy.md#api-providers`; line 192 (models) gains a clause that provider profiles map all four tiers; one `## Troubleshooting` row for "model not found on a provider profile" pointing to the tier flags. Untouched: everything else, including the Documentation index.
- `docs/architecture.md`: `## Models And Cost` gains one sentence on provider profiles and `ANTHROPIC_DEFAULT_*`. Nothing else.
Tests: none in `tests/`; the checkpoint is a `critic` prose round plus `python3 -m pytest -q` (the lint reads the docs for nothing, so green is expected).
Checkpoint: `grep -n "api-providers" README.md docs/deploy.md` finds the anchor and link; `git diff --stat -- docs README.md` shows only the three files.

## Verification

Fresh `HOME`: `./deploy install --tag or --provider openrouter --token-file F` on a TTY walks four picks and `claude-or --version` runs; `./deploy install --tag nrp --provider nrp --token-file F --model-* ...` without a TTY succeeds; `./deploy install --tag alcf --provider alcf` with a stub helper writes `apiKeyHelper`; `./deploy install` (subscription) produces a launcher identical to one from `main`; `./deploy doctor --tag or` shows the provider rows; `python3 -m pytest -q` green; `/usr/bin/python3 -m py_compile deploy` on macOS. The real ALCF and OpenRouter paths are checked by the user on first use (Assumptions).

## Risks

- `alcf-tokens get-token inference` may print more than the token, or ALCF's `<base>/v1/models` may not exist (R§Unverified): the helper check fails loudly with the login hint; the list fetch falls back to typed ids.
- Whether an empty `ANTHROPIC_API_KEY` or a settings `env` value reaches subagents is read from docs summaries (R§Unverified); `doctor`'s WARN covers the `env` case, and the launcher follows the OpenRouter recipe.
- A user who set `ANTHROPIC_DEFAULT_*` in their shell profile overrides nothing here (launcher exports win over the parent shell), but a `settings.json` `env` value they add later does; `doctor` says so.
- Tool-calling quality of non-Claude models is outside this tool's control; the docs say so once.

## Scope Notes

In: `deploy`, `tests/test_deploy.py`, the three docs. Out: `pack/`, lint changes for model ids, OpenAI bridges, `--global` providers, a live completion check, `migrate`. User decisions U1-U4 and the memory entries cited in Decisions bind `executor` and `writer`. `decisions/2026-10-24-deploy-never-detects-the-plan-or-model.md` still binds subscription installs in full.

## Assumptions

- Claude Code resolves subagent and per-call `fable|opus|sonnet|haiku` through `ANTHROPIC_DEFAULT_<TIER>_MODEL` (R§3); checked by the user's first session on a provider profile.
- A process `unset` of `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_API_KEY` lets `apiKeyHelper` take effect (R§3 precedence); checked the same way on ALCF.
- NRP's `/v1/models` accepts the LLM token as bearer (R§5); checked by the fetch's WARNING path if not.
- `pytest` runs on the developer's `python3` (3.10+) and 3.9 compatibility is checked by `py_compile` and `--help` only (`facts/2026-10-24-usr-bin-python3-3-9-6-has-no-pytest-so-t.md`).

## Work Packages

### P1: deploy code and tests
- Goal: Slices 1-4 land in `deploy` and `tests/test_deploy.py`; done when Slice 4's checkpoint passes and the subscription launcher test pins today's text
- Owns: `deploy`, `tests/test_deploy.py`
- Deps: none
- Stages: execute
- Status: done
- Artifacts: ->

### P2: user documentation
- Goal: Slice 5; done when a `critic` prose round passes and the acceptance sentence of Slice 5 holds
- Owns: `docs/deploy.md`, `README.md`, `docs/architecture.md`
- Deps: P1
- Stages: write
- Status: done
- Artifacts: ->

## Open Questions

None blocking. For the user at landing: whether this is a major release (`X.0`) or the next minor (decision 15 assumes minor).

## Log

2026-10-27 decision: user approved the plan; provider installs get an interactive picker (supersedes the 2026-10-24 no-model-prompt decision for provider profiles only); `--fable-is-opus` on a provider profile remaps Fable to the Opus-tier pick; presets plus generic `--base-url`.

2026-10-27 decision: this lands on main as a major release, VERSION 8.0 in the squash commit.

2026-10-27 P1: Slices 1-4 landed in d81b1a5 on worktree-api-access-install, pytest 524 passed, deploy py_compile and --help OK on 3.9; critic round 1 (claude) 1 BLOCKING and 4 SHOULD fixed, no round 2; deferred: fresh-HOME verification run (covered by subprocess tests), crash-window for simultaneous agent-key claim plus apiKeyHelper release (comment only), real ALCF/OpenRouter/NRP checks (user's first use)

2026-10-27 P2: done; docs/deploy.md API Providers section, README and architecture pointers, commit 07aca38, 2 critic rounds (claude), pytest green; deferred: none

## Todo

- [x] P1 Slice 1: presets, helper auth, launcher env, manifest, status, tests
- [x] P1 Slice 2: seeding filter, tier rules, non-TTY and dry-run paths, tests
- [x] P1 Slice 3: `fetch_models`, `pick_model`, `choose_models`, in-process tests
- [x] P1 Slice 4: doctor rows, `--help`, docstring, `LAUNCHER_HELP`, 3.9 `py_compile`
- [x] P2 Slice 5: `docs/deploy.md`, `README.md`, `docs/architecture.md` per the section list, after reading the five commits
- [ ] Verification run on a fresh `HOME` (section above)
- [ ] Curator close-out: supersede `decisions/2026-10-24-deploy-never-detects-the-plan-or-model.md` with a subscription-only entry; record U1-U4 and decisions 3-5 as entries; trim roadmap item 4 (`.supervisor/roadmap.md:63-69`) to what remains (bridges, none planned); archive this plan and the research artifact
- [ ] Landing: squash onto `main` with the `VERSION` bump; the branch never edits `VERSION`
