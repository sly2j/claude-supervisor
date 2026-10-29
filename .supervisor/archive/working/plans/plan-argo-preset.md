# Plan: Argo preset (ANL), including argo-proxy URLs

Roadmap item 11 (`.supervisor/roadmap.md:129-150`). Release: next minor. Branch per `repo-workflow` (worktree, `feat/argo-preset`).
Line refs are HEAD `d110a22` hints, re-anchored by content: a concurrent change edits `update_cmd` (`deploy:1682-1790`), so everything after it shifts; nothing here touches those lines.
Facts marked **ANL** come from the owner's manual setup (2026-10-29, Claude Code 2.1.312) and cannot be checked from outside ANL; facts marked **proxy** come from argo-proxy's public README and docs (`https://argo-proxy.readthedocs.io/en/latest/usage/cli-tools/` and `.../usage/models/`, release v3.3.3 of 2026-09-05).

## Goal

Add `--provider argo` beside `openrouter`, `nrp` and `alcf`: `./deploy install --tag argo-supervisor --provider argo --username NAME` reproduces the manual Argo setup with no hand-edited `settings.json`; `--provider argo --base-url http://localhost:44497` does the same through argo-proxy; docs and tests cover both.
Non-goals: `pack/`, `docs/architecture.md` (no agent changes), a live Argo check from this repo, the `update` command output (under concurrent edit), extra env for the other presets, `--global` provider installs.
Expected change size: `deploy` about +50/-10, `tests/test_deploy.py` about +80, `docs/deploy.md` about +15/-3, `README.md` one line. The plan stays under that.

## Approach

Extend the `PROVIDERS` table (`deploy:65-76`) rather than add a code path: the Argo entry carries a helper *template* (`echo {username}`), an `env` map and default tier `models`, and the three readers that need them use `.get`, so the other presets are untouched. `--username` is sugar for `--token-helper "echo NAME"`: it resolves into `helper_flag` at the top of `resolve_provider` (`deploy:1001`), so flag-over-manifest-over-preset precedence, `check_helper` validation, the managed `apiKeyHelper` and `update` replay all apply unchanged. Extra env goes out as launcher exports, per `decisions/2026-10-27-provider-tier-models-and-credentials.md`; no manifest field is needed because `update` re-runs `install_cmd` with the new tool copy's table. Rejected: managed `settings.json` `env` keys (a second claim/release mechanism like `managed_api_key_helper`, and a settings value could never be overridden per session); a static `--token NAME` recipe (Argo's recipe and the manual setup use the helper, whose output Claude Code sends as both `X-Api-Key` and `Bearer`, so it is the only form known to work, **ANL**); a `/v1/models` picker for the preset URL (it lists display names, not ids, **ANL**).

## Decisions

1. **Preset values.** `"argo": {base_url: "https://apps.inside.anl.gov/argoapi", auth: "helper", helper: "echo {username}", models_url: None, env: {"CLAUDE_CODE_AUTO_MODE_SERVER": "0"}, models: {fable: claude-opus-5-5, opus: claude-opus-5-5, sonnet: claude-sonnet-5-5, haiku: claude-haiku-5-5}, login: "pass --username with your ANL domain username; Argo is reachable only inside ANL or over VPN"}`. Ids and URL are **ANL**. Fable maps to Opus because Argo has no Fable (roadmap). `CLAUDE_CODE_SKIP_ANTHROPIC_AUTH=1` from the recipes is dropped: 2.1.312 never reads it (roadmap, **ANL**) and Claude Code's env-vars reference does not list it; argo-proxy's docs still call it required, so the owner's first live run (Verification) confirms the drop; if needed it is one more `env` key.
2. **`--username NAME`** joins the `tok` mutually exclusive group (`deploy:2401-2405`), so it cannot be combined with `--token`, `--token-file` or `--token-helper`; `--global` rejects it through the tuple at `deploy:252-253`. With a preset whose helper has no `{username}` placeholder, or with `--base-url` alone, it is a `DeployError` like `deploy:1035-1036`. The resolved helper (`/usr/bin/echo NAME`, program made absolute by `check_helper`, `deploy:881`) is recorded as `token_helper`; the username is not a secret and may appear in the manifest, `settings.json`, output and `status`, unlike tokens. A username with whitespace fails `check_helper`'s one-word rule, which is the intended error.
3. **Username default.** No silent default: a wrong username is invisible at install (`check_helper` passes for any word and the picker does not run) and surfaces only as a 401 inside Claude Code. On a terminal (`sys.stdin.isatty()` and not `--yes`, as at `deploy:1066`) install asks `ANL username [<getpass.getuser()>]:` and takes Enter as that default; without a terminal, or with `--yes`, a missing username is a `DeployError` naming `--username`, under `--dry-run` too. `update` never asks: it replays the recorded helper through the same-URL manifest reuse at `deploy:1045`; a re-run that changes the base URL without `--username` asks or errors the same way, as a URL change re-resolves credentials for every preset today. Alternative, if the owner prefers it: default silently to `getpass.getuser()` and print it in the `Provider:` summary (Open Question 1).
4. **Static-token precedence** stays as `lessons/2026-10-27-recorded-token-beats-preset-helper-on.md` requires: a recorded `<dir>/token` beats the preset helper, and `--token`/`--token-file` on an Argo profile turns it into a static-token one, removing the managed `apiKeyHelper`, as for ALCF.
5. **Env exports.** `launcher_text` (`deploy:108`) gains `env: Optional[Dict[str, str]] = None` and writes one `NAME='v'; export NAME` line per key, sorted, right after the `ANTHROPIC_BASE_URL` line (`deploy:140`); `install_cmd` passes `PROVIDERS.get(provider["provider"] or "", {}).get("env")` at `deploy:1294`. The export applies at the preset URL and at an argo-proxy URL alike (same backend). The subscription launcher and the other presets' launchers stay byte-identical (`test_subscription_launcher_unchanged`). Because a `settings.json` `env` entry overrides a launcher export (Claude Code settings reference, "A value here overwrites the same variable exported in your shell"), `seed_profile`'s filter (`deploy:838`) also drops keys named in the preset's `env`, and `doctor`'s WARN loop (`deploy:2023`) also names them; both are one-condition changes.
6. **Tier models.** In `resolve_provider`, `models` falls back to the preset's `models` only when the effective base URL equals the preset's `base_url`; `choose_models` then finds no missing tier, so neither the picker nor the `/v1/models` fetch runs, and `--model-<tier>` flags still override single tiers. At a replaced URL (argo-proxy) the preset defaults do not apply: the tiers come from flags or the picker as for ALCF Tara today, because whether argo-proxy resolves Argo's `claude-*-5-5` ids is unverified (**proxy**, Models reference: `/v1/models` is an OpenAI-style `data` list whose `id` is the proxy alias; documented Claude aliases are dotted, `argo:claude-opus-4.7` or `argo:claude-4.7-opus`, prefix optional, "examples only") and a silent wrong default would break every call. The picker fetches `<proxy>/v1/models` and falls back to typed ids as today. Open Question 2 asks the owner to check the live list; if the standard ids pass through, a follow-up can drop the URL condition.
7. **argo-proxy.** `--provider argo --base-url http://localhost:44497` (root, no `/v1`; Claude Code appends the path, **proxy**) replaces only the URL, as `test_alcf_tara_via_base_url` pins for ALCF; the helper from `--username` (or the recorded one at an unchanged URL) and the env of decision 5 stay. argo-proxy takes the username as the API key, so the same helper works (**proxy**, cli-tools page); the proxy itself needs `user:` in its `config.yaml` and `argo-proxy serve` running on an ANL-connected host, which the docs say and `deploy` does not check (no probe of `/health`: an install must not depend on a running process).
8. **Help, docs, tests.** `--provider` help (`deploy:2398`), `docs/deploy.md:68` and `README.md:253` list `argo`; `docs/deploy.md` Presets gets an `**Argo**` bullet (URL, `--username`, VPN, Fable-to-Opus default tiers, `CLAUDE_CODE_AUTO_MODE_SERVER=0`, the argo-proxy `--base-url` form with flags or picker, username-is-not-secret); the Doctor Checks table needs no new row. The `PROVIDERS` key set assertion (`tests/test_deploy.py:3412` at HEAD) adds `argo`. Tests compute the echo path with `shutil.which("echo")` or a regex, never a literal (`/bin/echo` on macOS, `/usr/bin/echo` on merged-`/usr` Linux).
9. **Version and memory.** Next minor, bumped in the squash commit per `CLAUDE.md`; `docs/architecture.md` unchanged. Memory entries (a decision for decisions 2-3 and 6) are written by `curator` at close-out, not by `executor`.

## Outline

`deploy`:
- `PROVIDERS` (`deploy:65-76`): the `argo` entry of decision 1; keep the other three entries as they are and read `env`/`models` with `.get`. Add `import getpass`.
- `launcher_text(..., provider=None, env=None)` (`deploy:108-160`): export lines of decision 5 after line 140. Invariant: with `env` None the output is unchanged.
- `target_tag` (`deploy:252-253`): add `"username"` to the rejected tuple.
- `seed_profile(target, dry_run, provider: bool)` (`deploy:810-852`): the extra filter of decision 5; pass the env map (or the provider name) in place of the bool, or add a keyword; keep the subscription call unchanged.
- `resolve_provider` (`deploy:1001-1071`): before line 1041, derive `helper_flag` from `getattr(args, "username", None)` (as `token_helper` at `deploy:1012`; `migrate` reaches this function too) and the preset template (decision 2 errors; the message at `deploy:1035-1036` also names `--username`); the prompt of decision 3 sits only in the preset-default branch (`deploy:1049-1050`), after the same-URL reuse at 1045, so re-installs and `update` never ask; at line 1065 apply the preset `models` under decision 6's URL condition. Gotcha: `prev` is `{}` after a clear (`deploy:1017-1018`); a cleared profile asks again.
- `install_cmd` (`deploy:1294-1295`): pass `env`. `doctor_cmd` (`deploy:2023`): widen the WARN condition. Parser (`deploy:2397-2408`): `--username NAME` in `tok`, help `profile: ANL username for the argo preset (its token helper is `echo NAME`)`; `--provider` help names `argo`.
- Python 3.9: no `match`, no `X | Y`, `str.format` for the template (`facts/2026-10-24-usr-bin-python3-3-9-6-has-no-pytest-so-t.md`).

`tests/test_deploy.py`, API providers block (`:3036-3300` at HEAD): subprocess tests through `run` with `MODEL_FLAGS` (`:3087`) where tiers are not defaulted, each Argo install passing `path="%s:/usr/bin:/bin" % ...` as `provider_stub` does (`:3101`), because `run` isolates PATH to the test `bin` dir (`:60`) and `check_helper` must find `echo`; `provider_stub`/`provider_vars` (`:3093-3116`) extended with `CLAUDE_CODE_AUTO_MODE_SERVER` in `PROVIDER_VARS` (`:3088`), and `provider_vars` keeping any name in `PROVIDER_VARS` instead of the `ANTHROPIC_` prefix test at `:3112`; the prompt of decision 3 through `tty_deploy` (`:2108`) like the picker tests; `test_global_rejects_provider_flags` (`:3295`) gets a `--username` row; `test_help` (`:425`) gets `--username`.

`docs/deploy.md`: line 68, the Presets list (`:166-172`, qualifying `:168` for presets with default tiers). `README.md:253`: add `argo`.

## Slices

Each slice ends with `python3 -m pytest -q` green, `/usr/bin/python3 -m py_compile deploy` (or `python3.9` where available) and `./deploy install --help` exit 0.

### Slice 1: the preset at Argo's URL (decisions 1-6)
Delivers: `install --tag argo --provider argo --username NAME` writes the launcher, `apiKeyHelper`, manifest and status without flags or a picker; replay and errors work. One unit (`deploy` + tests).
Tests:
- `argo_preset_username`: `--provider argo --username sj` -> `settings.json apiKeyHelper == "<which echo> sj"`, manifest `provider argo, auth helper, models == defaults`, no `<dir>/token`; launcher vars: `ANTHROPIC_BASE_URL=https://apps.inside.anl.gov/argoapi`, `CLAUDE_CODE_AUTO_MODE_SERVER=0`, the four tier vars and `ANTHROPIC_MODEL=claude-opus-5-5`, `ANTHROPIC_AUTH_TOKEN`/`ANTHROPIC_API_KEY` unset; `status` shows `Auth: token helper <which echo> sj` and four `Model` lines; `--fable-is-opus` leaves Fable on `claude-opus-5-5`.
- `argo_model_flag_overrides_default`: `--provider argo --username sj --model-haiku X` -> manifest haiku X, others default; re-run with `--provider argo` alone keeps X and asks nothing.
- `argo_username_prompt_default` (tty_deploy, `getpass.getuser` patched to `me`): Enter -> helper `echo me`; typed `other` -> `echo other`.
- `argo_username_required_without_tty`: `--provider argo` with no username, no TTY -> exit 2, stderr names `--username`, nothing written; same under `--dry-run` and with `--yes`.
- `username_needs_argo`: `--provider alcf --username x` and `--base-url U --username x` -> exit 2 with the reason; `--username x --token y` -> argparse error.
- `argo_update_replays`: install from clone, push, `update --yes` -> launcher text and manifest provider fields unchanged, no prompt.
- `other_launchers_unchanged`: `launcher_text(..., env=None)` equals today's text for subscription and openrouter inputs (extend `test_subscription_launcher_unchanged`).
- `seed_drops_preset_env_key`: `~/.claude/settings.json env {CLAUDE_CODE_AUTO_MODE_SERVER: "1", OTHER: "x"}` -> seeded profile env keeps only `OTHER`.
Checkpoint: the suite plus `HOME=$(mktemp -d) ./deploy install --dry-run --tag a --provider argo --username me --yes` exits 0 and prints the provider summary.

### Slice 2: argo-proxy URL, doctor, help and docs (decisions 5 doctor, 7, 8)
Delivers: the proxy form installs and documents itself. One unit (`deploy` + tests + docs).
Tests:
- `argo_proxy_via_base_url`: `--provider argo --username sj --base-url http://localhost:44497 *MODEL_FLAGS` -> manifest `base_url` is the proxy URL, models A-D, helper `echo sj`; launcher exports the proxy URL and `CLAUDE_CODE_AUTO_MODE_SERVER=0`; re-run with `--provider argo` alone keeps URL and models.
- `argo_proxy_needs_tiers_without_tty`: same without `MODEL_FLAGS`, no TTY -> exit 2 listing the four flags (preset defaults do not apply).
- `doctor_warns_preset_env_key`: profile env `CLAUDE_CODE_AUTO_MODE_SERVER` -> WARN row naming it; the alcf profile gets no such row.
- `providers_set`: `set(PROVIDERS) == {openrouter, nrp, alcf, argo}`; `install --help` lists `--username` and `argo`.
Checkpoint: the suite; `grep -n argo docs/deploy.md README.md` shows line 68, the Presets bullet and the README line.

## Verification

In the worktree, fresh `HOME`: `./deploy install --tag argo-supervisor --provider argo --username <name> --yes` prints `Provider: argo (https://apps.inside.anl.gov/argoapi), auth: token helper, fable=claude-opus-5-5, ...`; the launcher contains, in order, `ANTHROPIC_BASE_URL='https://apps.inside.anl.gov/argoapi'`, `CLAUDE_CODE_AUTO_MODE_SERVER='0'`, `unset ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_KEY`, the four tier exports and `ANTHROPIC_MODEL='claude-opus-5-5'`; `settings.json` holds `"apiKeyHelper": "/usr/bin/echo <name>"` (or `/bin/echo`) and no `env` `ANTHROPIC_*` or `CLAUDE_CODE_AUTO_MODE_SERVER` key; `./deploy doctor --tag argo-supervisor` passes the helper row. Then the owner, inside ANL: `claude-argo-supervisor -p 'say hi'` works at both URLs (the proxy one after `argo-proxy serve`), which settles Open Question 2 and confirms that `CLAUDE_CODE_SKIP_ANTHROPIC_AUTH` is not needed (decision 1). `python3 -m pytest -q` green; 3.9 `py_compile`, `--help` and a dry-run install pass.

## Risks

- `CLAUDE_CODE_SKIP_ANTHROPIC_AUTH` may matter after all (argo-proxy's docs call it required; the roadmap says 2.1.312 ignores it): the live run shows it; adding it is one more `env` key in the preset.
- argo-proxy may reject `claude-*-5-5` or list unusable ids: the picker takes typed ids, and `argo-proxy models` shows what it accepts.
- A wrong username is not detectable at install; decision 3's prompt and the status line are the only guards.
- `echo` resolved to an absolute path at install breaks only if the profile moves between machines with different `echo` paths, as for any helper today.
- Nothing here runs against Argo from this repo; the done criterion is checked by the owner's live run.

## Scope Notes

In: `deploy`, `tests/test_deploy.py`, `docs/deploy.md`, one `README.md` line. Out: `pack/`, `docs/architecture.md`, `update_cmd` output, extra env for the other presets, a `/health` probe, `--global` providers, a live completion check. Binding on `executor`: the four provider decisions of 2026-10-27 (`decisions/2026-10-27-provider-tier-models-and-credentials.md`, `-expiring-provider-tokens-use-a-managed.md`, `-provider-installs-pick-models-per-tier.md`, `-on-a-provider-profile-fable-is-opus-maps.md`), `lessons/2026-10-27-recorded-token-beats-preset-helper-on.md`, `decisions/2026-10-22-installs-never-need-the-source-checkout.md`.

## Assumptions

- `shutil.which("echo")` finds a binary on every supported system (coreutils); checked by `check_helper`'s own error path.
- The concurrent `update_cmd` change does not alter `replay_install` or `resolve_provider`; checked by rebasing before Slice 1 and re-reading `deploy:1631-1646`.

## Open Questions

1. Username default: keep decision 3 (prompt with `$USER` as the default, error without a terminal), or default silently to `$USER`? Recommended: decision 3.
2. argo-proxy tiers (**proxy**, needs a live proxy): does `argo-proxy models` or `GET http://localhost:44497/v1/models` list `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5`? If yes, a follow-up may apply the preset defaults at the proxy URL too. Recommended now: decision 6 (flags or picker at the proxy URL).

## Log

## Todo

- [x] Slice 1: preset entry, `--username`, prompt, env exports, default tiers, seed filter, tests
- [x] Slice 2: argo-proxy URL path, doctor WARN, help, `docs/deploy.md`, `README.md`, tests
- [x] Verification run on a fresh `HOME`; 3.9 `py_compile`, `--help`, dry-run install
- [ ] Owner: live run at both URLs inside ANL (Open Question 2, `CLAUDE_CODE_SKIP_ANTHROPIC_AUTH`)
- [ ] Curator close-out: decision entries for decisions 2-3 and 6; remove roadmap item 11; archive this plan
- [x] Landing: squash onto `main` with the minor `VERSION` bump
