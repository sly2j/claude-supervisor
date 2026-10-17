# Plan: Install Registry, Update, Launcher Subcommands, Launch-Time Fable (ROADMAP 6, 7, 8)

Line numbers refer to files at `d70ee5d`. `VERSION` is `1.10` at the time of writing.

## Goal

Every install (sandbox or global) is recorded in one machine-wide registry. The deploy tool can
then update or uninstall one install or all of them, without the source checkout. Each launcher
gains `update` and `uninstall` subcommands. The Opus/Fable choice moves from install time to
launch time. The deploy script moves to the repo root, so it is easier to find.

## Approach

Four packages, each landing as one change set on `main`, in this order.

- **P1, relocate:** `git mv scripts/deploy deploy`, then fix `REPO_ROOT` and every reference.
  The move lands first because P2's stand-alone update runs `<clone>/deploy` from a fresh clone.
  Fixing the in-repo path before P2 means that code is written once, against the final path.
- **P2, registry and `deploy update` (item 7):**
  - Install records its entry in `<prefix>/state/claude-supervisor/installs.json` (default
    prefix `~/.local`), together with the source's git remote. It also copies itself to
    `<prefix>/state/claude-supervisor/deploy`. Each prefix has its own registry and tool copy.
  - `update` (one install, or `--all`) shallow-clones `main` from the recorded remote into a
    temp dir. It then hands off to `<clone>/deploy update --from <clone> ...`, so the newest code
    replays each install's recorded options.
  - `uninstall --all` removes every registered install after one confirmation.
- **P3, launcher subcommands (item 8):** the launcher dispatches a first argument of `update` or
  `uninstall` to the state-dir copy of the tool and passes the hidden `--launcher` flag. With
  that flag, `update` also runs `claude update`. Everything else still reaches `exec claude "$@"`.
- **P4, launch-time Fable (item 6):**
  - The launcher exports `ANTHROPIC_DEFAULT_FABLE_MODEL=claude-opus-5-5` unless the first argument is
    `--fable`. With `--fable`, it strips the flag and unsets the variable.
  - The install-time rewrite, the install `--fable` flag, the manifest `fable` key, and the
    lint test that covers the rewrite are all removed.

Rejected, one line each:
- Relocate last: tool copies from P2 would look for `scripts/deploy` inside clones and break
  after the move.
- Relocate inside P2: a large feature diff on top of a rename weakens git rename detection
  and review.
- Old copy deploys from `--source <clone>/pack` itself: the old code would replay flags that
  newer code may have removed (P4 removes `--fable`). Handing off to the clone avoids that.
- Duplicate manifest fields (launcher, fable, base_url, settings, version) into the registry:
  the manifest already records them, and a second copy can drift. The registry maps each target
  to its tag and remote.
- Honor `$XDG_STATE_HOME`: not asked for. It would also need test isolation, because the tests
  copy `os.environ`. `--prefix` already moves the state dir (Decisions 6).
- `CLAUDE_CODE_SUBAGENT_MODEL` for item 6: it overrides every subagent, haiku and sonnet ones
  included, rather than remapping only `fable` (`docs/architecture.md:77` already warns
  against its `_FORCE` form).

## Files

### P1
- `scripts/deploy` -> `deploy` (`git mv`; keeps mode 0755 and the shebang; `scripts/` is then
  empty apart from the ignored `__pycache__`, so remove the directory).
  - `deploy:35` `REPO_ROOT = Path(__file__).resolve().parent` (was `.parent.parent`).
  - Messages naming `scripts/deploy` at old L705, L715 (status) and L868 (doctor): change them
    to `deploy install`.
- `tests/test_deploy.py`: L1 docstring, L15 `SCRIPT = ... / "deploy"`, and the asserts at L455
  and L492 that match the L705/L715 messages.
- `tests/test_pack_lint.py:30`: loader path `ROOT / "deploy"`.
- `README.md`: L18, 19, 26, 27, 29, 51, 52, 149, 150, 154 and 162 (the layout row becomes
  `deploy`).
- `docs/deploy.md`: L13-17, 37, 44, 70, 71 and 83 (`"$REPO/deploy" ...`).
- `docs/architecture.md`: L54 and L75 (path only; P4 rewrites the fable text at L54).
- `CLAUDE.md`: L3 and L9 (commands), and L8 (the rule now names `deploy` at the repo root).
- `ROADMAP.md`: L5 and L12 (Context), the item 6 Pointers line, and the item 7 and 8 Pointers.
  Only the path changes, nothing else in the items.
- `pack/skills/agent-authoring/SKILL.md:58`: `deploy install --dry-run`. This is a pack change,
  so `./deploy install` runs after the commit.
- Not touched: `docs/archive/` (109 historical hits), skill-internal `scripts/` dirs, and the
  `skills/demo/scripts/run.sh` fixture paths in `tests/test_deploy.py`.

### P2
- `deploy`: registry helpers, the tool copy, recording the remote, the `update` subcommand,
  `--all` for `uninstall`, and removing a registry entry on uninstall. Add `update` to the
  `Subcommands:` docstring at L4.
- `tests/test_deploy.py`: a new registry/update section (see Acceptance).
- `docs/deploy.md`: a new `## Update` section after `### Token Provider`; `--all` and the
  registry go in `## Uninstall`.
- `README.md`: Install block L26-29, where `git pull && ... install` becomes `deploy update`.
  Add `update` to the layout row at L162.
- `ROADMAP.md`: delete item 7.

### P3
- `deploy`: the case dispatch in `launcher_text` (L44-54), the hidden `--launcher` flag, and
  the `claude update` step.
- `tests/test_deploy.py`: launcher subcommand tests, next to `claude_stub`/`run_launcher`
  (L538-556).
- `docs/deploy.md`: a new `## The Launcher` section after `### Token Provider`.
- `README.md`: Install block.
- `ROADMAP.md`: delete item 8.

### P4
- `deploy`:
  - Delete `FABLE_TOKEN` and `deployed_bytes` (L339-347). Every `deployed_bytes` call site
    then hashes source bytes.
  - Delete the install `--fable` flag (L942), the manifest `"fable"` key (L639), and the
    `Fable:` lines (L536-537, L709).
  - Delete P2's `--fable` replay.
  - Add the launcher `--fable` branch at the L52 placeholder.
  - Print one note on `--global` installs (see Interfaces).
- `tests/test_deploy.py`: replace the fable block (L371-420) and the `--fable` uses (L288, 320,
  345, 507) with launcher `--fable` on and off tests. Change the L572 assert
  `"ANTHROPIC_" not in text`, which fails once every launcher exports the variable.
- `tests/test_pack_lint.py`: delete only `test_fable_rewrite_covers_pack` (L154-164). Keep
  `_load_deploy()`, which the lint still uses.
- `docs/deploy.md`: rewrite `## Fable Or Opus` (L49-53), and change L15 (`add --fable`).
- `README.md`: L111, and L154 (the troubleshooting row about `--fable`).
- `docs/architecture.md:54`.
- `ROADMAP.md`: delete item 6.
- `pack/skills/agent-authoring/SKILL.md`: only if `grep -n 'fable\|--fable' pack/` finds any
  text about the deploy-time rewrite. `planner.md:59` and `writer.md:26` stay as they are (see
  Interfaces).

## Interfaces And Data

**Registry** (`<prefix>/state/claude-supervisor/installs.json`, default prefix `~/.local`,
written with `write_json_atomic`; one registry per prefix):

```json
{"version": 1, "installs": {"<resolved target>": {"tag": "supervisor",
  "remote": "git@host:group/repo.git"}}}
```

- `tag` is `null` for `--global`. Everything else (launcher, fable, base_url, settings) is read
  from the target's manifest.
- `remote` is `git -C <source> remote get-url origin`, or `null` when that fails.
- A non-dry-run install upserts its entry after it writes the manifest. Uninstall deletes the
  entry once the manifest is gone; a global uninstall that leaves errors keeps it.
- The registry is never deleted, and neither is the tool copy.

**Tool copy:** every non-dry-run install copies `Path(__file__)` to
`<prefix>/state/claude-supervisor/deploy` (temp file then `os.replace`, mode 0755). The last
install under that prefix wins; other prefixes keep their own copy.

**CLI** (`common()` adds `--tag`, `--target`, `--global` and `--prefix`; `--prefix` defaults to
`~/.local`, may combine with `--global`, and replaces the removed `--bin-dir`):

- `deploy update [--tag T [--target DIR] | --global | --all] [--from DIR] [--yes] [--dry-run]`
  - Without `--from`:
    1. Group the selected registry entries by `remote`.
    2. Run `git clone --depth 1 --branch main --quiet <remote> <tmp>/src` for each remote, in a
       `tempfile.TemporaryDirectory`, with the terminal inherited so ssh can prompt.
    3. Run `[sys.executable, <tmp>/src/deploy, "update", "--from", <tmp>/src, <selection>,
       "--yes", ("--dry-run")]`. The selection is the original one. Under `--all`, `--from`
       processes only entries whose `remote` equals the clone's `origin` URL, so each clone
       deploys only to its own group.
  - With `--from DIR`, for each entry, in process:
    1. Run `install_cmd` with `--source DIR/pack` and the recorded options replayed:
       - `--tag` and `--target`, or `--global`;
       - `--prefix` = the manifest's recorded `prefix` (the default when the key is absent), so
         a plain reinstall does not write a second launcher under `~/.local`;
       - `--no-default-agent` when manifest `settings.managed_agent_key` is false (a plain
         reinstall would retake the key);
       - `--fable` when manifest `fable` is true (until P4).
       `base_url` and the token are already kept by a plain install (L535, L658).
       `--overwrite-local` is never passed.
    2. Report each install, continue past failures, and exit 1 if any install failed.
  - Entry errors:
    - An entry with `remote: null` errors with "no recorded remote; run deploy install from a
      checkout, or pass --from".
    - An entry whose target has no manifest is reported and skipped.
    - An unregistered install errors with "not registered; run deploy install once".
  - The hand-off passes `--prefix <given prefix>` to the clone's `update`. `update` and
    `uninstall` (single and `--all`) use the registry of the given prefix.
  - Confirmation: `--all` asks once through `confirm()`, listing the targets and remotes. A
    single-install `update` does not ask, as `install` does not.
- `deploy uninstall [--tag T [--target DIR] | --global | --all] [--yes] [--dry-run] [--force]`
  - `--all` asks once, listing every target ("deletes sessions, history, login" for sandboxes),
    then runs the existing uninstall path for each entry.
  - Entries with no manifest are pruned with a note.
- Install records `"prefix": "<resolved prefix>"` in the manifest. When the target's existing
  manifest records another prefix (no key = `~/.local`), `install` and single-target `uninstall`
  refuse with exit 2: `<target> was installed with --prefix <recorded>; pass --prefix <recorded>`.
  The check runs before anything is written, dry-run included. Under `uninstall --all` the entry
  is reported as `ERROR` and skipped. Sandbox dirs stay `~/.config/claude-<tag>` for any prefix.
- `--all` conflicts with `--tag`, `--target` and `--global`, except under `--launcher`.

**Launcher** (P3, then P4). The marker stays on line 2:

```sh
#!/bin/sh
# managed by claude-supervisor (tag: T)
case "$1" in update|uninstall)
  d='<prefix>/state/claude-supervisor/deploy'
  [ -x "$d" ] || { echo "claude-T: $d missing; run deploy install" >&2; exit 1; }
  s=$1; shift
  exec "$d" "$s" --prefix '<prefix>' --tag 'T' --target '<target>' --launcher "$@";;
esac
CLAUDE_CONFIG_DIR='<target>'; export CLAUDE_CONFIG_DIR
# ... base_url / token lines unchanged ...
# P4: if [ "$1" = --fable ]; then shift; unset ANTHROPIC_DEFAULT_FABLE_MODEL;
#     else ANTHROPIC_DEFAULT_FABLE_MODEL='claude-opus-5-5'; export ANTHROPIC_DEFAULT_FABLE_MODEL; fi
exec claude "$@"
```

- `--launcher` (hidden, `help=argparse.SUPPRESS`) changes five things:
  - `update` always asks for confirmation through `confirm()`, unless `--yes` is given.
  - `uninstall` requires typing the sandbox tag instead of y/N (OQ2). `--yes` skips it, and
    with no terminal it refuses with exit 2, as `confirm()` does.
  - `update --all` replaces the tag/target selection.
  - `uninstall --all` is refused ("use deploy uninstall --all").
  - `update` runs `subprocess.run(["claude", "update"])` with the order and failure handling
    of OQ3. `--dry-run` prints "would run claude update" instead.
- The deploy call runs before `CLAUDE_CONFIG_DIR` is exported, so `claude update` sees the
  user's normal environment.

**Item 6 decisions left to the planner:**
- Variable: `ANTHROPIC_DEFAULT_FABLE_MODEL`, documented at code.claude.com/docs/en/model-config
  ("Each value must be a full model name"). The value is a `deploy` constant,
  `claude-opus-5-5` (OQ4), changed with each Opus release.
- `--global` installs have no launcher. Deploy does not manage the variable for them. Install
  `--global` prints one line: "set ANTHROPIC_DEFAULT_FABLE_MODEL to run fable agents on Opus".
  `docs/deploy.md` gives the shell-profile form and the `~/.claude/settings.json` `env` form
  (OQ5).
- Prose dispatch tokens (`planner.md:59`, `writer.md:26`): the docs say these variables control
  what the aliases resolve to, so the Agent tool's `model: fable` should follow the remap. No
  pack edit. A manual check under P4 confirms it.

## Risks And Compatibility

- **Existing installs:** they are not registered, and their launchers have no subcommands.
  - Run `./deploy install` once from the checkout after P2, and again after P3.
  - `docs/deploy.md` says so.
  - The user's sandbox (`~/.config/claude-supervisor`) is updated only through that normal
    install step.
- **`status` after `update`:** the manifest's `source_dir` then names the deleted temp clone,
  so `status` needs `--source` to report outdated files or a version mismatch. Say so in
  `## Update`.
- **Update needs a pushed `main`:** a clone of an older `main` has no `update --from`. The hand-off
  then fails with an argparse error. Push each package before relying on `update`.
- **SSH remote** (`git@eicweb.phy.anl.gov:...`): the clone needs key access. Without it, git
  fails, and the error is reported per remote.
- **`claude-<tag> uninstall`** used to send the prompt "uninstall" to claude. `update` already
  meant `claude update`, so P3 keeps that meaning and adds the pack update.
- **P4 global installs:** they used to get Opus through the rewrite and will now run Fable
  unless the variable is set (OQ5). Old opus-rewritten files equal their baseline, so the
  three-way reconcile updates them to `model: fable` with no `--overwrite-local`.
- **Python 3.9:** the tool copy and launcher subcommands run under whatever `python3` is first
  on `PATH`. `/usr/bin/python3` (3.9.6) has no pytest, so 3.9 is checked with
  `/usr/bin/python3 ./deploy --help` and a dry-run install (below). The launcher tests'
  `PATH=tmp/bin:/usr/bin:/bin` also runs the copy under 3.9 on macOS.
- **Test isolation:** `run()` sets `HOME` to `tmp_path`, so the default prefix (`~/.local`) and
  its registry land under the fake home. `claude_stub()` (L546) returns only `PATH`, so P3 launcher tests must add
  `HOME=str(tmp_path)` to that env. Without it, the tool copy resolves the real home prefix and could
  update or uninstall real installs. In-process tests must monkeypatch `HOME` before
  `load_deploy()`. Update tests need `git` on `PATH`; skip them when `shutil.which("git")` is
  None.

## Acceptance Criteria

- **P1:**
  - `git grep -n 'scripts/deploy' -- ':!docs/archive' ':!docs/plan-install-lifecycle.md'`
    prints nothing.
  - `./deploy --help` works.
  - The pytest suite passes.
- **P2:** tests show that:
  - install creates the registry entry and the tool copy (byte-equal, executable);
  - a reinstall refreshes the entry, and uninstall (sandbox and global) removes it;
  - `--dry-run` writes neither the registry nor the copy (`snapshot()`).
  - **Update:**
    - Build a bare `file://` repo with branch `main` holding `deploy`, `VERSION` and the `pack`
      fixture. Install from a clone of it, push a pack change, and delete the clone.
    - The state-dir copy's `update --tag t --yes` then installs the change.
    - It keeps `--prefix`, `--no-default-agent`, `--fable` and `base_url`.
    - No temp dir is left behind.
  - **Prefix:**
    - Two prefixes stay independent: each gets its own registry, tool copy and launcher, and
      `uninstall --all --yes --prefix A` leaves B's install and registry untouched.
    - Install refuses (exit 2, nothing changed) when the manifest records another prefix.
    - A legacy manifest with no `prefix` key counts as `~/.local`: a default reinstall works,
      another `--prefix` refuses.
    - Update replays the recorded prefix: after `install --prefix <tmp>/px` and `update`, the
      launcher, registry and tool copy stay under `<tmp>/px` and nothing is written to
      `~/.local`.
  - **`--all`:**
    - Update and uninstall cover two sandboxes and one global install.
    - Without `--yes`, and with no terminal, they exit 2 and change nothing.
    - A stale entry is skipped by update and pruned by uninstall.
    - `remote: null` gives the documented error.
- **P3:** launcher tests run the generated script with `claude_stub` and with `HOME` set to
  `tmp_path`.
  - `update --yes` updates the sandbox, and the stub shows `update`.
  - `uninstall --yes` removes the target, the launcher and the registry entry.
  - `update --all --yes` covers every entry. `uninstall --all` is refused.
  - With no terminal and no `--yes`, both exit 2 and change nothing.
  - A missing tool copy gives exit 1 with the message.
  - Passthrough of `"a b" -- ""` is unchanged (L575-577).
- **P4:**
  - Launcher tests cover `--fable` (variable unset, flag stripped) and its absence (variable set
    to the constant).
  - Installed agents keep `model: fable` byte-for-byte.
  - `grep -n 'deployed_bytes\|FABLE_TOKEN' deploy tests/` prints nothing.
  - The owner confirms by hand that a `model: fable` dispatch reports Opus under the default
    launcher.
- **Every package:**
  - `VERSION` is raised by one over `HEAD`.
  - `python3 -m pytest -q` passes on `main`.
  - `/usr/bin/python3 ./deploy --help` exits 0.
  - `HOME=$(mktemp -d) /usr/bin/python3 ./deploy install --dry-run --tag t` exits 0.
  - The package's ROADMAP item is deleted in the same commit. P1 has no item.

## Scope Notes

- **In:** P1-P4 as specified, the docs they touch, and `CLAUDE.md` L3/L8/L9 (P1). The `CLAUDE.md`
  edits are approved with this plan.
- **Out:**
  - a `list` or `status --all` command;
  - version pinning, rollback, branch selection, offline update and update checks;
  - launcher support for global installs;
  - model or subscription detection;
  - pty-driven tests of the interactive `y` path;
  - rewriting `docs/archive/`;
  - tagging releases.
- **Creep to resist:**
  - registry fields beyond `tag` and `remote`, or a registry lock;
  - a registry "repair" or "import" command;
  - git env tweaks (`GIT_SSH_COMMAND`, timeouts) that would break ssh passphrase prompts;
  - generalizing the launcher's `case` beyond `update` and `uninstall`;
  - deprecation shims for the removed `--fable` install flag.
- **Settled by the user, do not reopen:** the "Decisions already made" in ROADMAP items 6, 7
  and 8, plus the root location of the script and the package order.

## Work Packages

### P1: Relocate the deploy script to the repo root
- Goal: `deploy` lives at the repo root and every live reference names it; done when the P1
  acceptance criteria hold.
- Owns: the script's location, `REPO_ROOT`, and all non-archive path references.
- Deps: none
- Stages: execute
- Status: done
- Artifacts: commit on main (VERSION 1.11)

### P2: Install registry, deploy update, and --all (ROADMAP 7)
- Goal: registry-driven `update` and `--all`, with the tool copy and the clone hand-off; done
  when the P2 acceptance criteria hold.
- Owns: the registry and tool-copy helpers, `update` and `uninstall --all` in `deploy`, the
  registry tests, `## Update` in the docs, and ROADMAP item 7.
- Deps: P1
- Stages: execute
- Status: done
- Artifacts: commit on main (VERSION 1.12)

### P3: Launcher update and uninstall (ROADMAP 8)
- Goal: the launcher dispatches `update` and `uninstall` to the tool copy; done when the P3
  acceptance criteria hold.
- Owns: the `launcher_text` dispatch, `--launcher`, the `claude update` step, the launcher
  subcommand tests, `## The Launcher` in the docs, and ROADMAP item 8.
- Deps: P2
- Stages: execute
- Status: execute
- Artifacts: ->

### P4: Launch-time Opus/Fable switch (ROADMAP 6)
- Goal: the launcher `--fable` replaces the install-time rewrite; done when the P4 acceptance
  criteria hold.
- Owns: the fable code paths in `deploy`, the fable tests and lint, `## Fable Or Opus`,
  `README.md:111`, `docs/architecture.md:54`, and ROADMAP item 6.
- Deps: P3
- Stages: execute
- Status: execute
- Artifacts: ->

## Orchestration

Packages run sequentially, and each lands as its own commit on `main`. Within a package, wave 1
runs these units in parallel, with disjoint files:

| Pkg | U1 (code) | U2 (tests) | U3 (docs) |
|---|---|---|---|
| P1 | `git mv`, `deploy`, `tests/test_deploy.py`, `tests/test_pack_lint.py` | (in U1) | `README.md`, `docs/deploy.md`, `docs/architecture.md`, `CLAUDE.md`, `ROADMAP.md`, `pack/skills/agent-authoring/SKILL.md` |
| P2 | `deploy` | `tests/test_deploy.py`, written to the Interfaces spec | `docs/deploy.md`, `README.md` |
| P3 | `deploy` | `tests/test_deploy.py` | `docs/deploy.md`, `README.md` |
| P4 | `deploy` | `tests/test_deploy.py`, `tests/test_pack_lint.py` | `docs/deploy.md`, `README.md`, `docs/architecture.md`, pack text if any |

- Validation per unit:
  - U1 runs `python3 -m pytest -q tests/test_deploy.py`. In P4, U1 runs it at glue instead,
    because the old `--fable` tests fail until U2 lands.
  - U2 runs the same file after integration.
  - U3 runs the P1 `git grep` (P1) or reads the changed sections.
- `executor` glue for each package:
  1. Integrate U1 and U2, and delete the package's ROADMAP item (P2-P4).
  2. `printf '1.<x+1>\n' > VERSION`.
  3. Run `python3 -m pytest -q`, the two `/usr/bin/python3` checks, and critic/scope-critic.
  4. Commit through `git-ops` with `VERSION` staged. P1's commit also carries this plan file
     and ROADMAP items 7 and 8. P4's commit also carries
     `git mv docs/plan-install-lifecycle.md docs/archive/`, with the Todo ticked first.
  5. Run `./deploy install` when `pack/` changed (P1, and P4 if pack text changed) or to pick
     up new launcher text (P2, P3).

## Decisions

User decisions on the former open questions (OQ1-OQ5):

1. **Root script name:** `deploy`, run as `./deploy install`.
2. **Launcher confirmation:** launcher `update` uses the `confirm()` y/N prompt. Launcher
   `uninstall` asks the user to type the sandbox tag, because it deletes sessions, history and
   login. `--yes` skips either prompt, and with no terminal the command refuses.
3. **`claude update` order and failure:** run `claude update` first, because a new pack can
   need a newer Claude Code (doctor's `MIN_CLAUDE_VERSION`). On failure, report it and still
   update the pack. Exit 1 if either step failed.
4. **Item 6 variable:** `ANTHROPIC_DEFAULT_FABLE_MODEL`, set to the full model ID
   `claude-opus-5-5`, not the `opus` alias.
5. **Global installs after P4:** a printed note plus documentation is enough.
6. **`--prefix`** (added to P2's change set; `--bin-dir` is removed, with no shim):
   - `--prefix P` is a common flag, default `~/.local`. Launchers go to `P/bin/claude-<tag>`;
     the registry and tool copy go to `P/state/claude-supervisor/`.
   - Installs under different prefixes are independent: one registry and tool copy per prefix.
   - Sandbox dirs stay `~/.config/claude-<tag>` (or `--target`). The manifest records the
     prefix, and install refuses with exit 2 on a mismatch (no key = `~/.local`).
   - `update` and `uninstall` (and `--all`) use the given prefix's registry. Update replays the
     recorded prefix, and the hand-off passes `--prefix` to the clone.

## Todo

- [x] User approves the plan and answers OQ1-OQ5, or accepts the recommendations
- [x] P1 U1: `git mv`, `REPO_ROOT`, messages, test paths and asserts
- [x] P1 U3: README, docs/deploy.md, architecture, CLAUDE.md, ROADMAP paths, SKILL.md:58
- [ ] P1 glue: grep clean, VERSION +1, pytest, 3.9 checks, review, commit (with this plan and
  ROADMAP 7/8), `./deploy install`
- [x] P2 U1: registry helpers, lock, tool copy, remote recording, uninstall entry removal
- [x] P2 U1: `update` (clone, hand-off, `--from` replay), `--all` for update and uninstall
- [x] P2 U2: registry, update-from-`file://`, `--all`, stale-entry and null-remote tests
- [x] P2 U3: `## Update`, `## Uninstall` `--all`, README Install block
- [ ] P2 glue: delete ROADMAP item 7, VERSION +1, pytest, 3.9 checks, review, commit, install
- [ ] P3 U1: launcher `case` dispatch, `--launcher`, `claude update` step, typed-tag confirm
  for uninstall
- [ ] P3 U2: launcher subcommand tests (yes, refusal, `--all`, missing copy, passthrough)
- [ ] P3 U3: `## The Launcher`, README Install block
- [ ] P3 glue: delete ROADMAP item 8, VERSION +1, pytest, 3.9 checks, review, commit, install
- [ ] P4 U1: remove the rewrite, flag, manifest key and replay; launcher `--fable`; global note
- [ ] P4 U2: launcher `--fable` tests, remove the fable block and lint test
- [ ] P4 U3: `## Fable Or Opus`, README:111, architecture:54, any pack text
- [ ] P4 glue: delete ROADMAP item 6, VERSION +1, pytest, 3.9 checks, review, commit, install
- [ ] P4: owner checks by hand that a `model: fable` dispatch runs Opus by default
- [ ] P4 commit: archive this plan with `git mv` in the same change set
