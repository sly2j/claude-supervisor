# Plan: Opus by default, Fable on request (ROADMAP item 1)

## Goal

`scripts/deploy install` deploys the three Fable agents (`supervisor`, `planner`, `scope-critic`) and the two prose dispatch overrides (`planner.md:59`, `writer.md:26`) on Opus. `install --fable` is the only way to deploy them on Fable. Every detection path (`_seat_tier`, `detect_fable`, the TTY prompt `ask_fable`, `resolve_fable`, the `auto` value) is removed.

## Approach

- **(a) Source keeps `fable`; the default install rewrites it to `opus`; `--fable` deploys verbatim.** The rewrite (`FABLE_TOKEN`, `deployed_bytes`, `scripts/deploy:295-303`) and its lint (`test_fable_rewrite_covers_pack`) already exist and cover all five `model: fable` tokens in `pack/agents/`. The reverse (source `opus`, `--fable` rewrites to `fable`) would need a per-agent list so the Opus agents stay Opus, and would leave the planner/writer dispatch overrides meaningless in the source. Rejected.
- **(b) The manifest keeps one boolean `fable`; `install` does not read it.** Each `install` deploys what its flag says (stateless). The boolean replaces today's `{"enabled", "reason"}` dict because `file_states` must hash the deployed variant to report `outdated` correctly and `status` prints it. Honoring a saved choice on later installs would keep `resolve_fable` and need an opposite flag (`--opus`); rejected for the extra code. Cost: pass `--fable` on every install that should stay on Fable.
- Pack source files do not change. Deployed copies change through `scripts/deploy install`.

## Files

| File | Change |
|---|---|
| `scripts/deploy` | Delete `fable_enabled` (L306-309) and `_seat_tier`, `detect_fable`, `ask_fable`, `resolve_fable` (L312-393). `install_cmd` L543-546: `fable = args.fable`; print `Fable: on` or `Fable: off (fable agents deploy as opus)`. Manifest L648: `"fable": fable`. `file_states` L675: `fable = manifest.get("fable") is True`. `status_cmd` L708-712: one line, `Fable: on` or `Fable: off`. `build_parser` L923-927: `--yes` help becomes `do not prompt (answers yes to --overwrite-local)`; `--fable` becomes `action="store_true"`, help `deploy the Fable agents on Fable instead of Opus`. Keep `FABLE_TOKEN`, `deployed_bytes(key, src, fable)`, `confirm()` (L110-115) and `MANIFEST_VERSION = 1`. Imports are unchanged. |
| `tests/test_deploy.py` | Remove and change tests as listed under Tests. Delete the helpers `fake_claude` (L363), `auth_json` (L433), `TtyInput` (L498), `NoRead` (L503), `install_in_process` (L508) and the `io` and `stat` imports. In `run()`, L49 comment becomes `# hides the real claude (and git)`. |
| `tests/test_pack_lint.py` | No change. `test_fable_rewrite_covers_pack` (L154-163) calls `deploy.deployed_bytes(key, path, True/False)`, whose signature and meaning stay. |
| `docs/deploy.md` | L15 comment: `# add --fable to deploy the Fable agents on Fable (see Fable Or Opus)`. Replace `## Fable Or Opus` (L39-62) with the text under Interfaces. Delete the L88 bullet. |
| `README.md` | L5: `One Fable supervisor` -> `One supervisor`. L110 note: `Rows marked `fable`, and the `model: fable` dispatch overrides, deploy on Opus unless the pack is installed with `--fable`. See [docs/deploy.md](docs/deploy.md).` L153 troubleshooting row: `You installed with `--fable`; run `scripts/deploy install` without it. `scripts/deploy status` prints the current choice.` Table rows L95-105 and L138 stay: they describe the source and the L110 note covers deployment. |
| `docs/architecture.md` | L54, last sentence: ``scripts/deploy install` deploys those agents and dispatch overrides on Opus unless given `--fable` (see `docs/deploy.md`); the source stays on Fable and the lint checks the source.` Diagram lines 8, 13, 18, 19 stay (source models). |
| `docs/plan-fable-fallback.md` | Delete L209 (the open `- [ ]` item), then `git mv docs/plan-fable-fallback.md docs/archive/plan-fable-fallback.md`. No header note (convention from commit `0936f51`). |
| `ROADMAP.md` | Delete item 1 (L25-43 and the blank line after). Do not renumber items 2-5 (the Context section references item 3). |
| `VERSION` | Executor raises `1.7` to `1.8`, once, before running the tests. |

## Interfaces And Data Changes

- CLI: `install [--fable]` replaces `install --fable {auto,yes,no}`. `status`, `uninstall`, `doctor` are unchanged.
- Manifest: top-level `"fable": true|false` replaces `"fable": {"enabled": bool, "reason": str}`. `MANIFEST_VERSION` stays `1`. Readers use `manifest.get("fable") is True`, so a missing key or an old dict value reads as Opus until the next `install` rewrites the manifest.
- Output: `install` prints `Fable: on` or `Fable: off (fable agents deploy as opus)`; `status` prints `Fable: on` or `Fable: off`.
- `deployed_bytes(key, src, fable)` and `FABLE_TOKEN` are unchanged.
- New `## Fable Or Opus` section of `docs/deploy.md`:

```
## Fable Or Opus

Three agents (`supervisor`, `planner`, `scope-critic`) are written for Fable, and `planner` and `writer` also name `model: fable` in their dispatch instructions. `install` deploys those agents and dispatch overrides as `opus`; `install --fable` deploys the source verbatim, on Fable. Only files under `agents/` change; skills and the source in `pack/` always name Fable.

Each `install` deploys what its flag says, so pass `--fable` on every install that should stay on Fable. The manifest records the choice and `status` prints it as a `Fable:` line.
```

## Tests

`tests/test_deploy.py`, Fable section (L361-527) and four mechanical spots:

| Test | Action |
|---|---|
| `test_fable_off_rewrites_agents` (L380-390) | Rename `test_default_install_rewrites_agents`; plain `install`; same byte assertions; `manifest(target)["fable"] is False`; `"Fable: off" in r.stdout`. |
| `test_fable_yes_is_verbatim` (L393-399) | Rename `test_fable_flag_is_verbatim`; `install --fable`; `manifest(target)["fable"] is True`; `"Fable: on"`. |
| `test_fable_switch_updates` (L416-423) | Keep; sequence plain -> `--fable` -> plain; the second and third installs each `updated=1` with the right bytes. The last step proves the flag is not persisted. |
| `test_fable_choice_persists` (L402-413) | Rename `test_status_matches_installed_variant`: after `install --fable`, `status` prints `Fable: on` and no row is `outdated`; after a plain `install`, `Fable: off` and no row `outdated`. |
| `test_fable_auto_without_claude` (L426-430), `test_fable_auto_detection` (L437-466), `test_fable_auto_reads_seat_tier_from_home` (L469-473), `test_fable_explicit_auto_rediscovers` (L476-481), `test_fable_old_manifest_not_recorded` (L484-495), `test_fable_prompt_when_unclear` (L518-522), `test_fable_prompt_skipped_with_yes` (L525-527) | Remove. |
| L311, L335 (`"--fable", "yes"`) | `"--fable"`. |
| `legacy_install` fixture (L588, `"--fable", "no"`) | Drop the two arguments. |
| L614 | `assert after["fable"] is False`, trailing comment dropped. |
| Help test (L280-282, `"--fable" in stdout`) | Keep. |

## Risks And Compatibility

- An existing manifest with the old dict value shows `Fable: off` in `status` and may list the Fable agents as `outdated` until the next `install`. No compatibility code; the next install fixes it.

## Acceptance Criteria

- `grep -nE 'detect_fable|_seat_tier|ask_fable|resolve_fable|fable_enabled|"auto"|seatTier|subscriptionType' scripts/deploy` prints nothing; the only `isatty` left is in `confirm()`.
- Tests cover `--fable` on and off (`test_fable_flag_is_verbatim`, `test_default_install_rewrites_agents`, `test_fable_switch_updates`, `test_status_matches_installed_variant`).
- `docs/deploy.md`, `README.md`, `docs/architecture.md` describe `--fable` and no detection.
- `docs/archive/plan-fable-fallback.md` exists, `docs/plan-fable-fallback.md` does not, and the archived file has no `- [ ]` line.
- `ROADMAP.md` has no item 1.
- `git diff --stat -- pack/` is empty; `pack/agents/supervisor.md` body stays 76 lines.
- `python3 -m pytest -q` passes; `VERSION` is raised once.

## Validation Commands

```
python3 -m pytest -q
/usr/bin/python3 scripts/deploy install --dry-run
/usr/bin/python3 scripts/deploy install --fable --dry-run
grep -nE 'detect_fable|_seat_tier|ask_fable|resolve_fable|fable_enabled|"auto"|seatTier|subscriptionType' scripts/deploy
grep -n -i fable docs/deploy.md README.md docs/architecture.md
git diff --stat -- pack/
test -f docs/archive/plan-fable-fallback.md && ! test -f docs/plan-fable-fallback.md && ! grep -q '^- \[ \]' docs/archive/plan-fable-fallback.md
grep -c '^### 1\.' ROADMAP.md   # 0
```

After `scripts/deploy install`: `grep -rn 'model: fable' ~/.claude/agents/` prints nothing (unless installed with `--fable`), and `scripts/deploy status` shows no `outdated` row.

## Scope Notes

- In: the Files table.
- Out: any model or subscription detection; wording changes under `pack/` (the source stays `fable`, including the `agent-authoring` tier table); renumbering roadmap items; roadmap items 2-5; changes to `confirm()`, `MANIFEST_VERSION`, or the `run()` test helper's environment.
- Creep to resist: an `--opus` or `--no-fable` flag; compatibility code for the old manifest dict; an explanation of the model choice in `status`; "while here" cleanups in `scripts/deploy` or the tests; rewriting README or architecture prose about where Fable has leverage; renaming `deployed_bytes` or `FABLE_TOKEN`.
- Decided, do not reopen: no detection; Opus is the default; Fable is a manual flag; (a) and (b) above.

## Orchestration

Default partition, one wave, then glue.

| Unit | Owns | Validation |
|---|---|---|
| U1 deploy script | `scripts/deploy` | `/usr/bin/python3 scripts/deploy install --dry-run` and `--fable --dry-run`; the grep in Acceptance Criteria; `python3 -m pytest -q tests/test_pack_lint.py` |
| U2 tests | `tests/test_deploy.py` | `python3 -m pytest -q tests/test_deploy.py`, run by the executor after U1 lands |
| U3 docs | `docs/deploy.md`, `README.md`, `docs/architecture.md`, `docs/plan-fable-fallback.md` (edit, then `git mv`), `ROADMAP.md` | the `grep`/`test` lines in Validation Commands |

U1 and U2 share the interface above (flag, manifest boolean, output strings) and run in parallel.

Exact sequence for the executor:
1. Dispatch U1, U2, U3.
2. Raise `VERSION` to `1.8`.
3. `python3 -m pytest -q`, then the other Validation Commands.
4. `scripts/deploy install` (add `--fable` only if the owner says so under Open Questions), then `scripts/deploy status`.
5. Commit all touched files, including the `git mv`, with the trailer exactly `Co-Authored-By: Claude` (ROADMAP Context); push.

## Open Questions

1. This machine's `~/.claude` manifest currently records Fable on (pack 1.7). The final `scripts/deploy install` deploys Opus here unless given `--fable`. Should the executor pass `--fable`? Default if unanswered: plain `install` (Opus).

## Todo

- [x] `scripts/deploy`: delete `fable_enabled`, `_seat_tier`, `detect_fable`, `ask_fable`, `resolve_fable`
- [x] `scripts/deploy`: `install_cmd` reads `args.fable`, prints the new `Fable:` line, writes `"fable": fable`
- [x] `scripts/deploy`: `file_states` and `status_cmd` read `manifest.get("fable") is True`
- [x] `scripts/deploy`: `--fable` is `store_true`; `--yes` help loses the detection clause
- [x] `tests/test_deploy.py`: remove the seven detection/prompt tests and their helpers
- [x] `tests/test_deploy.py`: adapt the four kept Fable tests and the four mechanical spots
- [x] `docs/deploy.md`: L15, `## Fable Or Opus`, L88
- [x] `README.md`: L5, L110, L153
- [x] `docs/architecture.md`: L54
- [x] `docs/plan-fable-fallback.md`: delete L209, `git mv` to `docs/archive/`
- [x] `ROADMAP.md`: delete item 1
- [x] `VERSION` 1.7 -> 1.8
- [x] `python3 -m pytest -q` passes; Validation Commands clean
- [x] `scripts/deploy install`; `status` shows no `outdated` row; commit with trailer `Co-Authored-By: Claude`; push
