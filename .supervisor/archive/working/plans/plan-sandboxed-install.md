# Plan: Sandboxed Installs With A Launcher (ROADMAP Item 2)

Facts: `docs/research-sandboxed-install.md` (CLAUDE_CONFIG_DIR, `~/.claude` inventory, launcher
shape) plus worker reports on `scripts/deploy`, `tests/test_deploy.py`, docs, and this machine.
Line numbers refer to the current files.

## Goal

By default, `scripts/deploy` installs the pack into a sandbox: a tag (default `supervisor`) plus
a dir (default `~/.config/claude-<tag>`). It writes a `claude-<tag>` launcher, which runs
`claude` with `CLAUDE_CONFIG_DIR` set to the dir and can point it at a token provider.
`--global` keeps today's `~/.claude` install.

## Approach

- There are two modes, chosen by flags only:
  - **Sandbox** (the default): `--tag T` sets the tag, and `--target DIR` overrides only the
    dir.
  - **Global**: `--global` means `~/.claude`, exactly as today. It does no seeding, writes no
    launcher, and uninstall stays manifest-driven. `--global` combined with `--tag`,
    `--target`, `--bin-dir`, or a provider flag is an error.
- The first install of a sandbox (no manifest yet) seeds it from `~/.claude` through an
  allowlist. It then runs the normal pack install, which sets and manages the `agent` key as
  today. Seeding only once means a re-install never overwrites edits made in the sandbox.
- After the manifest is written, a sandbox install writes `<dir>/token` (mode 0600) when a
  token flag is given. It then regenerates the launcher (mode 0755) from:
  - the base URL: the flag if given, otherwise the value in the manifest;
  - whether `<dir>/token` exists.

  The manifest records the tag, the launcher path, and the base URL, never the token.
- A sandbox uninstall needs the manifest. It removes the launcher, but only when the file has
  the marker, and then removes the whole dir, `token` included. Without a manifest it stays a
  no-op, as today, so the deploy never deletes a dir it did not create.
- Rejected alternatives, one line each:
  - Re-seeding on every install: it would overwrite sandbox edits.
  - `--bin-dir` on uninstall: the manifest already holds the launcher path.

## Decisions (asked of the planner)

- **Manifest:** add three keys, each `null` in global mode.
  - `tag`.
  - `launcher`: the absolute path. `status` and `uninstall` cannot recompute it for a
    `--target` sandbox or a non-default `--bin-dir`.
  - `base_url`: so a plain re-install keeps it.

  No schema bump: old manifests lack the keys, so `.get()` returns `None`. Nothing about the
  token goes in the manifest; its state is whether `<dir>/token` exists.
- **Re-install without provider flags:** the existing `token` and the manifest's `base_url` are
  kept, and the launcher is regenerated from them. `--base-url ''` clears the URL. Deleting
  `<dir>/token` drops the token line at the next install. This is the least code.
- **The global dir as a sandbox:** a sandbox whose dir resolves to `~/.claude` is refused
  ("use --global"). Otherwise `uninstall --target ~/.claude` would delete `~/.claude`, and the
  launcher would select a different Keychain entry (research section 1).
- **Sandbox dir mode:** a new sandbox dir is created 0700 whether or not a token is given. That
  is one unconditional line, and the dir also holds login state and history.
- **doctor:** no change beyond the shared target flags.
- **status with no flags on a global-only machine:** it prints the default sandbox target and
  "No manifest: pack is not installed here." No extra code.
- **Tests:**
  - Existing tests that pass `--target` become sandbox tests. Seeding is a no-op there,
    because the test `HOME` (`tmp_path`) has no `.claude`, and the launcher lands in
    `tmp_path/.local/bin`.
  - The tests that check manifest-driven uninstall move to global mode through a
    `global_target` fixture (`tmp_path/.claude`). `run()` passes `--global` for that fixture.
- **settings.json on tagged uninstall:** nothing to restore, because the whole dir is removed.
- **Executor order:** `uninstall --global` runs last, after the push, because this session's
  agents and skills load from `~/.claude`. The executor commits and pushes itself.

## Files

### `scripts/deploy` (stdlib only, Python 3.9: `typing` generics, `%` formatting)

1. Docstring line 2: replace `(~/.claude)` with `(default: sandbox ~/.config/claude-supervisor)`.
2. New constants and the launcher renderer near line 27:

   ```python
   DEFAULT_TAG = "supervisor"
   SEED = ("settings.json", "CLAUDE.md", "commands", "output-styles", "keybindings.json",
           "agents", "skills")
   LAUNCHER_MARKER = "# managed by claude-supervisor"


   def launcher_text(tag: str, target: Path, base_url: Optional[str], has_token: bool) -> str:
       lines = ["#!/bin/sh", "%s (tag: %s)" % (LAUNCHER_MARKER, tag),
                "CLAUDE_CONFIG_DIR='%s'; export CLAUDE_CONFIG_DIR" % target]
       if base_url:
           lines.append("ANTHROPIC_BASE_URL='%s'; export ANTHROPIC_BASE_URL" % base_url)
       if has_token:
           lines.append("ANTHROPIC_AUTH_TOKEN=\"$(cat '%s/token')\"; export ANTHROPIC_AUTH_TOKEN"
                        % target)
       # ROADMAP item 6 adds its leading --fable branch here, above the exec line.
       lines.append('exec claude "$@"')
       return "\n".join(lines) + "\n"
   ```

   Rendered with no provider flags, as on this machine:

   ```sh
   #!/bin/sh
   # managed by claude-supervisor (tag: supervisor)
   CLAUDE_CONFIG_DIR='/Users/<user>/.config/claude-supervisor'; export CLAUDE_CONFIG_DIR
   exec claude "$@"
   ```

   Rendered with `--tag work --base-url https://llm.example.com --token-file F`:

   ```sh
   #!/bin/sh
   # managed by claude-supervisor (tag: work)
   CLAUDE_CONFIG_DIR='/Users/<user>/.config/claude-work'; export CLAUDE_CONFIG_DIR
   ANTHROPIC_BASE_URL='https://llm.example.com'; export ANTHROPIC_BASE_URL
   ANTHROPIC_AUTH_TOKEN="$(cat '/Users/<user>/.config/claude-work/token')"; export ANTHROPIC_AUTH_TOKEN
   exec claude "$@"
   ```

3. Replace `resolve_target` (118-120) and add `target_tag` and `is_launcher`:

   ```python
   def target_tag(args: argparse.Namespace) -> Optional[str]:
       """Sandbox tag, or None for --global."""
       if args.use_global:
           for name in ("tag", "target", "bin_dir", "base_url", "token", "token_file"):
               if getattr(args, name, None) is not None:
                   raise DeployError("--global cannot be combined with --%s" % name.replace("_", "-"))
           return None
       tag = DEFAULT_TAG if args.tag is None else args.tag
       if not re.fullmatch(r"[A-Za-z0-9_-]+", tag):
           raise DeployError("invalid tag %r (use letters, digits, '-' or '_')" % tag)
       return tag

   def resolve_target(args: argparse.Namespace) -> Path:
       tag = target_tag(args)
       home = Path("~/.claude").expanduser().resolve()
       if tag is None:
           return home
       target = Path(args.target or "~/.config/claude-" + tag).expanduser().resolve()
       if target == home:
           raise DeployError("%s is the global dir; use --global" % target)
       return target

   def is_launcher(path: Path) -> bool:
       try:
           with open(path, "rb") as f:
               return LAUNCHER_MARKER.encode() in f.read(256)
       except OSError:
           return False
   ```

4. New `seed_sandbox(target, dry_run)`:

   ```python
   def seed_sandbox(target: Path, dry_run: bool) -> None:
       """Copy the user's own ~/.claude items into a new sandbox; pack files come from install."""
       home = Path("~/.claude").expanduser()
       names = [n for n in SEED if (home / n).exists()]
       if not names:
           return
       print("%s from %s: %s" % ("Would seed" if dry_run else "Seeded", home, ", ".join(names)))
       if dry_run:
           return
       skip = {"skills/.trash", "skills/synced"} | set((load_manifest(home) or {}).get("files", {}))

       def ignore(d: str, entries: List[str]) -> List[str]:
           rel = os.path.relpath(d, home)
           return [e for e in entries if os.path.join(rel, e) in skip or ".bak-" in e]

       for n in names:
           if n == "settings.json":
               data = load_settings(home)
               data.pop("agent", None)
               write_json_atomic(target / n, data)
           elif (home / n).is_dir():
               shutil.copytree(home / n, target / n, ignore=ignore, dirs_exist_ok=True)
           else:
               shutil.copy2(home / n, target / n)
   ```

   `copytree` follows symlinks by default, so the sandbox gets copies.

5. `install_cmd` (438-575):
   - Right after `resolve_target` (440), before anything is written, add the checks and the
     token read. `atomic_write_bytes` creates parent dirs itself, so the launcher needs no
     separate `mkdir`.

     ```python
     tag = target_tag(args)
     launcher = Path(args.bin_dir or "~/.local/bin").expanduser().resolve() / ("claude-" + tag) if tag else None
     if launcher and os.path.lexists(launcher) and not is_launcher(launcher):
         raise DeployError("%s exists and is not a claude-supervisor launcher" % launcher)
     token = Path(args.token_file).expanduser().read_bytes() if args.token_file else None
     if args.token is not None:
         token = args.token.encode()
     ```

   - Just before `with target_lock(...)` (451), after `collect_source` has validated the pack:
     `if tag and not args.dry_run: target.mkdir(mode=0o700, parents=True, exist_ok=True)`.
   - Inside the lock, right after the manifest load at 453:

     ```python
     if tag and not <loaded manifest>:
         seed_sandbox(target, args.dry_run)
     base_url = <loaded manifest>.get("base_url") if args.base_url is None else args.base_url
     ```

   - In `new_manifest` (548-558), add `"tag": tag`,
     `"launcher": str(launcher) if launcher else None`, and `"base_url": base_url or None`.
   - In the `if not args.dry_run:` block, after the manifest and settings writes (559-569):

     ```python
     if launcher:
         if token is not None:
             atomic_write_bytes(target / "token", token, mode=0o600)
         text = launcher_text(tag, target, base_url, (target / "token").exists())
         atomic_write_bytes(launcher, text.encode(), mode=0o755)
     ```

     `mkstemp` creates the temp file 0600, so the token is never readable by others.
   - After the `Settings:` print (572), add `if launcher: print("Launcher: %s" % launcher)`. It
     prints on dry runs too.
6. `status_cmd`: after the `Fable:` line (617), add
   `if manifest.get("launcher"): print("Launcher: %s" % manifest["launcher"])`.
7. `uninstall_cmd` (643-711): the no-manifest check (646-648) stays first. The confirm text
   depends on the mode, and the sandbox branch goes before the lock (656):

   ```python
   tag = target_tag(args)
   prompt = "Delete %s (sessions, history, login) and its launcher?" if tag else \
       "Remove the agent pack from %s?"
   if not args.dry_run and not confirm(prompt % target, args.yes): ...   # existing abort
   if tag:
       launcher = manifest.get("launcher")
       gone = "%s and %s" % (target, launcher) if launcher else str(target)
       if args.dry_run:
           print("[dry-run] would remove %s" % gone)
           return 0
       if launcher and is_launcher(Path(launcher)):
           Path(launcher).unlink()
       shutil.rmtree(target)
       print("Removed %s" % gone)
       return 0
   ```

8. `build_parser`:
   - Epilog (814):
     `"Target: sandbox ~/.config/claude-TAG (--tag, default supervisor; --target DIR sets the dir), or --global for ~/.claude."`
   - Replace the `--target` line in `common()` (819) with three plain flags. `target_tag`
     enforces the `--global` conflicts, so argparse needs no mutex group here.

     ```python
     sp.add_argument("--tag", help="sandbox tag: launcher claude-TAG (default: supervisor)")
     sp.add_argument("--target", metavar="DIR", help="sandbox dir (default: ~/.config/claude-TAG)")
     sp.add_argument("--global", dest="use_global", action="store_true", help="use ~/.claude (no seeding, no launcher)")
     ```

   - Install only:

     ```python
     sp.add_argument("--bin-dir", metavar="DIR", help="launcher dir (default: ~/.local/bin)")
     sp.add_argument("--base-url", metavar="URL", help="sandbox: export ANTHROPIC_BASE_URL ('' clears)")
     tok = sp.add_mutually_exclusive_group()
     tok.add_argument("--token-file", metavar="PATH", help="sandbox: copy to <dir>/token for ANTHROPIC_AUTH_TOKEN")
     tok.add_argument("--token", metavar="VALUE", help="like --token-file, from a value (stays in shell history)")
     ```

   - argparse rejects `--token` combined with `--token-file`, with exit 2.
9. Must keep: `parse_frontmatter`, `as_list`, and `deployed_bytes(key, path, fable)`, which
   `tests/test_pack_lint.py` imports, and the `--fable` flag and manifest `fable` key.

### `tests/test_deploy.py`

- Changed:
  - New fixture `global_target`, which returns `tmp_path / ".claude"`.
  - `run()` (45-54) gets the keyword `target_args=None`. When it is `None`, `run()` passes
    `["--global"]` if `target.name == ".claude"`, and `["--target", str(target)]` otherwise.
    `HOME` and `PATH` stay as they are.
  - Swap the `target` parameter for `global_target`, with no logic change, in:
    - `test_uninstall_restores_previous_agent` (213) and `test_uninstall_removes_agent_key`
      (227), which fail today under sandbox uninstall;
    - the `legacy_install` fixture (466), which the five legacy tests use, so that
      `test_uninstall_removes_legacy_install` checks the manifest path again.
  - `test_settings_write_failure_keeps_manifest_consistent` (299) and
    `test_release_write_failure_leaves_agent_revertible` (321) also move to `global_target`.
    These two run in process with the real `HOME`, so each also:
    - adds `monkeypatch.setenv("HOME", str(global_target.parent))` before `load_deploy()`;
    - replaces `"--target", str(target)` with `"--global"` in its `parse_args` list.
  - `test_help` also asserts that `--tag`, `--global`, `--bin-dir`, `--base-url`, `--token`,
    and `--token-file` appear in `install --help`.
- New helper `claude_stub(tmp_path)`:
  - It writes `tmp_path/bin/claude` with mode 0755, `#!/bin/sh`, and
    `printf '%s\n' "$CLAUDE_CONFIG_DIR" "$ANTHROPIC_BASE_URL" "$ANTHROPIC_AUTH_TOKEN" "$@"`.
  - It returns `{"PATH": "%s:/usr/bin:/bin" % (tmp_path / "bin")}`, the env to use when running a
    launcher. The stub comes first on PATH, and the token line needs `cat`.
- New tests. Paths are under `tmp_path`, and expected values use `.resolve()`.
  - `test_sandbox_round_trip`, parametrized over `([], "supervisor")` and `(["--tag", "t"], "t")`:
    1. `install --dry-run` exits 0 and creates neither `.config/claude-<tag>` nor
       `.local/bin/claude-<tag>`.
    2. `install` exits 0. Then:
       - the manifest's `launcher` equals the launcher path;
       - the launcher is executable and line 2 starts with `LAUNCHER_MARKER`;
       - the launcher contains `CLAUDE_CONFIG_DIR='<sandbox>'` and no `ANTHROPIC_`;
       - "Seed" is absent from stdout, because `tmp_path/.claude` does not exist.
    3. Run the launcher with the args `["a b", "--", ""]` under the stub env. Stdout must equal
       `"<sandbox>\n\n\na b\n--\n\n"`.
    4. `status` prints `Target: <sandbox>`, `Launcher: <path>`, and
       `Settings agent: 'supervisor' (managed)`.
    5. `uninstall --yes` exits 0 and removes the sandbox and the launcher.
  - `test_sandbox_token_provider`:
    1. `install --tag t --base-url https://llm.example --token s3cret` exits 0. Then:
       - `<sandbox>/token` reads `s3cret` and has mode 0600, and the sandbox dir has mode 0700;
       - the launcher contains `ANTHROPIC_BASE_URL='https://llm.example'; export ANTHROPIC_BASE_URL`
         and `ANTHROPIC_AUTH_TOKEN="$(cat '<sandbox>/token')"; export ANTHROPIC_AUTH_TOKEN`;
       - `s3cret` is absent from the install's stdout and stderr, from the manifest text, from
         `settings.json`, and from `status --tag t` output.
    2. Run the launcher with no args under the stub env. Stdout must equal
       `"<sandbox>\nhttps://llm.example\ns3cret\n"`.
    3. A plain `install --tag t` leaves the launcher text unchanged.
    4. Write `tmp_path/tok` containing `f1le\n`, then run `install --tag u --token-file <that file>`.
       Then:
       - `<sandbox-u>/token` holds those exact bytes and has mode 0600;
       - the launcher has the `ANTHROPIC_AUTH_TOKEN` line and no `ANTHROPIC_BASE_URL` line.
  - `test_global_round_trip`, using `global_target`:
    1. `install` puts the manifest in `tmp_path/.claude`. Its `launcher` is `None`, and neither
       `.local/bin` nor `.config` exists.
    2. `status --global` shows the managed agent.
    3. `uninstall --global --yes` removes the pack files and the manifest. `tmp_path/.claude` and
       a user file placed in it survive.
  - `test_sandbox_seeds_from_global_once`:
    1. Run an install on `global_target`, then set the global `settings.json` to also hold
       `"theme": "dark"`.
    2. Add these to `tmp_path/.claude`:
       - to be copied: `CLAUDE.md`, `agents/mine.md`, `commands/c.md`;
       - to be skipped: `agents/mine.md.bak-1`, `skills/synced/x.md`, `skills/.trash/y.md`,
         `plugins/p.json`, `history.jsonl`.
    3. `install --tag t` exits 0 with no "not managed" errors. Then:
       - the copied set is present and the skipped set is absent;
       - the sandbox `settings.json` equals `{"theme": "dark", "agent": "supervisor"}`;
       - its manifest has `managed_agent_key` set to `True`.
    4. Change the global `CLAUDE.md` and re-run `install --tag t`. The sandbox copy is
       unchanged.
  - `test_tag_with_target_dir`. Run `install --tag work --target <tmp>/box`. Then:
    - the launcher is `tmp_path/.local/bin/claude-work`, with
      `CLAUDE_CONFIG_DIR='<tmp>/box'` baked in;
    - the manifest has `tag` set to `work` and records that launcher;
    - `status --target <tmp>/box` prints the `Launcher:` line;
    - `uninstall --target <tmp>/box --yes` removes both the dir and the launcher.
  - `test_sandbox_refusals`. Each case exits 2 and creates no target dir:
    - `--tag a/b`
    - `--tag ""`
    - `install` on `global_target` (so `run()` adds only `--global`) combined with each of:
      `--tag t`, `--target d`, `--bin-dir d`, `--base-url u`, `--token x`, `--token-file f`.
      Stderr contains `"--global cannot be combined with " + flag`.
    - `status --global --tag t`
    - `install --tag t --token x --token-file y` (argparse)
    - `install` with `target_args=["--target", str(tmp_path / ".claude")]`. Stderr contains
      "use --global".
    - a regular file `tmp_path/.local/bin/claude-t` without the marker; stderr must contain "is
      not a claude-supervisor launcher"
    - a directory `tmp_path/.local/bin/claude-u`, with `--tag u`
  - `test_bin_dir_recorded_for_uninstall`: `install --tag t --bin-dir <tmp>/xbin` writes
    `xbin/claude-t` and nothing in `.local/bin`. A later `uninstall --tag t --yes`, without
    `--bin-dir`, removes it.
  - `test_sandbox_uninstall_without_manifest_keeps_dir`: a pre-existing
    `tmp_path/.config/claude-t/keep` survives `uninstall --tag t --yes`, which exits 0.
- Removed: none.

### `docs/deploy.md`

Keep the existing style: one line per paragraph and `"$REPO/scripts/deploy"` command blocks.

- L15: the comment becomes
  `# sandbox ~/.config/claude-supervisor + launcher; add --fable to deploy the Fable agents on Fable (see Fable Or Opus)`.
- L20 becomes:

  > Start it with `claude-supervisor` and log in once; each sandbox has its own login,
  > settings, and history, and plain `claude` is untouched. The session runs as `supervisor`
  > because install sets `"agent": "supervisor"` in the sandbox's `settings.json`.

  The `/agents` sentence after it stays.
- L24: the second sentence, about target resolution, becomes:

  > The target is a sandbox, `~/.config/claude-<tag>` (`--tag`, default `supervisor`;
  > `--target DIR` sets another dir), or `~/.claude` with `--global`, which installs as before
  > with no copy and no launcher. `$CLAUDE_CONFIG_DIR` is ignored.

  The first sentence stays.
- L35: change `claude --agent supervisor` to `claude-supervisor --agent supervisor`.
- Add two bullets to What Install Does:

  > On a sandbox's first install, copies from `~/.claude`: `settings.json` (without `agent`),
  > `CLAUDE.md`, `commands/`, `output-styles/`, `keybindings.json`, and your own files in
  > `agents/` and `skills/` (not `skills/.trash` or `skills/synced`). Plugins, logins,
  > history, and sessions stay behind.

  > Writes the launcher `~/.local/bin/claude-<tag>` (`--bin-dir DIR` to change), which runs
  > `claude` with `CLAUDE_CONFIG_DIR` set to the sandbox. Install refuses a tag whose launcher
  > path exists and was not written by the deploy.
- New subsection `### Token Provider`, at the end of What Install Does: one command line, then
  one paragraph.

  ```bash
  "$REPO/scripts/deploy" install --tag work --base-url https://llm.example.com --token-file ~/work.token
  ```

  > Install copies the token to `<dir>/token` (mode 0600), and the launcher exports
  > `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN`. `--token VALUE` also works but leaves the
  > value in your shell history, so prefer `--token-file`. A later plain `install` keeps both;
  > `--base-url ''` drops the URL, and deleting `<dir>/token` drops the token at the next
  > install.
- Uninstall: before L64, add:

  > For a sandbox, uninstall deletes its dir, including sessions, history, login, and token,
  > and its launcher. With `--global` it removes only the pack's files:

  L64 stays.
- New section `## Moving From A Global Install`, before `## Notes For Claude Running This`:
  1. "Versions before 1.10 installed into `~/.claude`. After the first sandboxed install,
     remove that copy once:"
  2. A bash block: `"$REPO/scripts/deploy" uninstall --global --yes`.
  3. "Plain `claude` then starts plain Claude Code."

### `README.md`

- L19: `scripts/deploy install     # installs into ~/.config/claude-supervisor`.
- L22 becomes:

  > Then run `claude-supervisor` and log in once. It runs as the supervisor; type `/agents` to
  > see the pack. `--global` installs into `~/.claude` instead; `--tag <t>` makes another
  > sandbox, `claude-<t>`.
- After L27, add one line:

  > **Token provider:** add `--base-url URL --token-file PATH` to a sandbox install
  > ([docs/deploy.md](docs/deploy.md#token-provider)).
- L26: change "Files you edited in `~/.claude`" to "Files you edited in the install dir".
- L142: replace the paragraph with:

  > Not every session needs the supervisor: plain `claude` starts plain Claude Code, and
  > `claude-supervisor` starts the supervisor.
- L148: change "Start a new session" to "Start a new `claude-supervisor` session".
- L151 and L152: change `~/.claude` to "the install dir".
- L159 and L160: change `(deployed to ~/.claude/agents)` and `(... ~/.claude/skills)` to
  `(deployed to <install dir>/agents)` and `(.../skills)`.
- The inventory and the L161 subcommand list do not change.

### `CLAUDE.md`

- L3: change "is deployed into `~/.claude` by `scripts/deploy`" to:

  > is deployed by `scripts/deploy` into `~/.config/claude-supervisor` (run with
  > `claude-supervisor`), or into `~/.claude` with `--global`
- L9: change "Agents in `~/.claude/agents` pick up changes in new sessions." to "Deployed agents
  pick up changes in new sessions."

### `ROADMAP.md`

- Delete the item 2 block (lines 25-50). Do not renumber.
- Item 6: delete `- **Depends on:** item 2 (launcher).`. In Pointers, change "the item 2
  launcher" to "`launcher_text`".

### `VERSION`

Change `1.9` to `1.10`, once.

### Not touched

- `pack/`, so the `supervisor.md` body stays 76 lines.
- `docs/architecture.md`: no agent's name, scope, model, or tools change, and the file has no
  deploy-target text.
- `tests/test_pack_lint.py` and `tests/test_version.py`.

## Interfaces And Data

- CLI:
  - `install`, `status`, `uninstall`, and `doctor` gain `--tag TAG` and `--global`.
    `--target DIR` now sets the sandbox dir.
  - `install` gains `--bin-dir DIR` (default `~/.local/bin`), `--base-url URL`, and one of
    `--token-file PATH` or `--token VALUE`.
  - `--global` excludes all of these.
- Manifest: three new keys, `tag`, `launcher`, and `base_url`, each a string or `null`.
- Sandbox files: `<dir>/token` (mode 0600) and the dir itself (mode 0700 when new).
- New output lines:
  - `Seeded from <home>: <names>` (dry run: `Would seed from ...`)
  - `Launcher: <path>` (install and status)
  - `Removed <dir> and <launcher>` (dry run: `[dry-run] would remove ...`)
- New errors, all exit 2:
  - `error: invalid tag '<t>' (use letters, digits, '-' or '_')`
  - `error: <path> exists and is not a claude-supervisor launcher`
  - `error: --global cannot be combined with --<flag>`
  - `error: <path> is the global dir; use --global`

## Risks And Compatibility

- A plain `scripts/deploy install` no longer touches `~/.claude`. Anyone who relied on
  `$CLAUDE_CONFIG_DIR` must now pass `--target`, which makes a sandbox. docs/deploy.md L24
  documents this.
- A pre-1.10 `--target` install becomes a sandbox. Its next install writes a launcher, and
  uninstall deletes its whole dir.
- Each sandbox has its own login. A sandbox uninstall leaves that dir's Keychain entry behind.
  This is harmless, and a re-install at the same path reuses the entry.
- A `HOME` or `--base-url` containing `'` breaks the launcher's quoting. This is not handled,
  per the simplicity rule.
- If `~/.claude` holds pack files but no manifest, seeding copies them. When their content
  differs, install reports "exists but is not managed", which `--overwrite-local` resolves.
- Re-installing with a different `--bin-dir` leaves the old launcher in place.

## Acceptance Criteria

- `install`, `status`, and `uninstall` work in sandbox mode (the default, `--tag`, and
  `--target`) and in `--global` mode, and the tests cover both modes.
- Provider tests:
  - `<dir>/token` is written 0600 from both `--token` and `--token-file`;
  - the launcher has each export line exactly when a base URL is recorded or `<dir>/token`
    exists;
  - `--token` together with `--token-file` errors, and so does `--global` with any sandbox
    flag;
  - `status` output never contains the token.
- `python3 -m pytest -q` passes, and the `/usr/bin/python3` (3.9.6) dry runs succeed.
  `scripts/deploy` imports only the standard library.
- `git diff --stat HEAD` lists no `pack/` path, `VERSION` is `1.10`, and ROADMAP has no `### 2.`
  heading.
- `docs/deploy.md`, `README.md`, and `CLAUDE.md` describe:
  - the sandbox default, `--tag`, and `--global`;
  - the launcher and the token provider;
  - the migration one-liner.
- On this machine:
  - `~/.local/bin/claude-supervisor --version` prints the same as `claude --version`;
  - after the final step, `scripts/deploy status --global` reports no manifest, and
    `~/.claude/settings.json` has no `agent` key.
- `docs/research-sandboxed-install.md` and this plan are in `docs/archive/` in the commit.

## Scope Notes

- In:
  - the two modes and their flags, seeding, the launcher, the provider flags and `token` file,
    the uninstall branch, and the status line;
  - the tests, the docs listed above, the ROADMAP edit, and the VERSION bump;
  - the migration on this machine.
- Out:
  - item 6 (`--fable` at launch) and version pinning;
  - plugins (never copied), Linux credential testing, and IDE integration;
  - Keychain cleanup, PATH checks, new doctor checks, and `XDG_CONFIG_HOME`;
  - migration detection or auto-migration, and a re-seed command;
  - an `ANTHROPIC_API_KEY` variant, and validating the URL or token.
- Likely creep to resist:
  - extra confirmation when a sandbox holds sessions;
  - status lines for the token or URL;
  - refactoring `run()` or the existing tests beyond `target_args`, `global_target`, and the
    listed swaps;
  - rewording docs beyond the lines listed;
  - touching `--fable`.
- Owner decisions not to reopen:
  - the sandbox is the default, `--global` is opt-in, and installs copy rather than symlink;
  - the copy and never-copy lists;
  - flags-only target resolution: `$CLAUDE_CONFIG_DIR` is ignored, and conflicting flags are
    errors;
  - the launcher shape, with `claude` taken from PATH;
  - tag validation and the marker check;
  - migration by a single manual `uninstall --global`;
  - no model or subscription detection;
  - the `--fable` install flag and manifest key stay as they are;
  - provider flags: `--token` and `--token-file` are mutually exclusive, the file is
    `<dir>/token` with mode 0600, and the variables are exactly `ANTHROPIC_AUTH_TOKEN` and
    `ANTHROPIC_BASE_URL`;
  - the secret never appears in the manifest, settings, or output;
  - two modes: in sandbox mode `--target` overrides only the dir, and the launcher is always
    `claude-<tag>`; `--global` rejects `--tag`, `--target`, `--bin-dir`, and the provider
    flags;
  - the manifest records the tag, the launcher, and `base_url`.

## Orchestration

- Wave 1, three units in parallel with disjoint files:
  - U1 `scripts/deploy`. Validate with `python3 scripts/deploy install --help` and
    `HOME=$(mktemp -d) python3 scripts/deploy install --dry-run --tag t`.
  - U2 `tests/test_deploy.py`. Write it against the interfaces above. It is validated in glue.
  - U3 `docs/deploy.md`, `README.md`, `CLAUDE.md`, and `ROADMAP.md`. Validate with
    `grep -n '~/.claude' README.md CLAUDE.md docs/deploy.md`: only intended mentions remain.
- Glue (`executor`, sequential): run the full pytest, reconcile the U1 and U2 messages, and
  follow the sequence below.

### Executor Sequence

```bash
cd <checkout>
# after U1-U3:
printf '1.10\n' > VERSION
python3 -m pytest -q
/usr/bin/python3 scripts/deploy install --dry-run          # Would seed ..., Launcher: ~/.local/bin/claude-supervisor
/usr/bin/python3 scripts/deploy install --dry-run --global
/usr/bin/python3 scripts/deploy status --global
/usr/bin/python3 scripts/deploy doctor
test ! -e ~/.config/claude-supervisor && test ! -e ~/.local/bin/claude-supervisor
# critic + scope-critic rounds and fixes here (re-run pytest), before installing and staging
scripts/deploy install                                     # sandbox default, Opus: no --fable, no provider flags
scripts/deploy status                                      # version 1.10 match, Launcher line, agent managed
head -4 ~/.local/bin/claude-supervisor
test "$(~/.local/bin/claude-supervisor --version)" = "$(claude --version)"
# tick every Todo box in this plan
git add docs/research-sandboxed-install.md docs/plan-sandboxed-install.md
git mv docs/research-sandboxed-install.md docs/plan-sandboxed-install.md docs/archive/
git add scripts/deploy tests/test_deploy.py docs/deploy.md README.md CLAUDE.md ROADMAP.md VERSION
git diff --cached --stat                                   # no pack/ paths; VERSION staged
git commit   # "feat(deploy): sandboxed installs with a claude-<tag> launcher", trailer exactly: Co-Authored-By: Claude
git push
```

After the push, as the last step and outside the Todo:

```bash
scripts/deploy uninstall --global --yes
scripts/deploy status --global                             # No manifest
```

Then tell the owner to start `claude-supervisor` and log in once.

## Open Questions

None.

## Todo

- [x] U1: constants `DEFAULT_TAG`, `SEED`, `LAUNCHER_MARKER`; `launcher_text`
- [x] U1: `target_tag`, new `resolve_target`, `is_launcher`, `seed_sandbox`
- [x] U1: install: launcher refusal, token read, 0700 dir, seeding, `base_url`
- [x] U1: install: manifest `tag`, `launcher`, and `base_url`; token write, launcher write,
  `Launcher:` line
- [x] U1: status `Launcher:` line
- [x] U1: uninstall: mode-dependent prompt, sandbox branch
- [x] U1: parser: `--tag`, `--target`, and `--global` in `common()`; `--bin-dir`, `--base-url`,
  token mutex, epilog, docstring
- [x] U2: `global_target`, `run()` switch and `target_args`, `claude_stub`, `test_help` asserts
- [x] U2: move the 4 uninstall and in-process tests and the `legacy_install` fixture to
  `global_target` (in-process: patch `HOME`, use `--global`)
- [x] U2: `test_sandbox_round_trip` (default and `--tag`)
- [x] U2: `test_sandbox_token_provider`
- [x] U2: `test_global_round_trip`
- [x] U2: `test_sandbox_seeds_from_global_once`
- [x] U2: `test_tag_with_target_dir`
- [x] U2: `test_sandbox_refusals`
- [x] U2: `test_bin_dir_recorded_for_uninstall`
- [x] U2: `test_sandbox_uninstall_without_manifest_keeps_dir`
- [x] U3: `docs/deploy.md`:
  - L15, L20, L24, L35
  - two bullets and Token Provider
  - uninstall sentence and migration section
- [x] U3: `README.md`: L19, L22, the token line, L26, L142, L148, L151-152, L159-160
- [x] U3: `CLAUDE.md` (L3, L9)
- [x] U3: `ROADMAP.md`: delete item 2, edit item 6 Depends on and Pointers
- [x] Bump `VERSION` to 1.10
- [x] `python3 -m pytest -q` green
- [x] `/usr/bin/python3` dry runs and doctor
- [x] critic and scope-critic review, with fixes
- [x] `scripts/deploy install`, `status`, and the launcher `--version` check
- [x] Archive the research doc and this plan with `git mv`, then commit and push
