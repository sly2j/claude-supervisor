# Plan: Repo versioning with a `VERSION` file

Fact base: `scripts/deploy` line numbers below were verified against the working tree at commit 7c55ca7 (clean tree). Test line numbers refer to `tests/test_deploy.py` at the same commit. Re-verify both before editing. Commits 605e017, ff60106, and 7c55ca7 (the lead-loop work) did not touch any file this plan changes.

## Goal

Give the repo a version beyond the commit hash: a one-line `VERSION` file with a `1.x` scheme, raised in every commit on `main` (normally by one), recorded by `scripts/deploy` in the installed manifest, compared by `scripts/deploy status`, and enforced by a test plus a repo-local rule.

## Approach

- `VERSION` at the repo root holds `1.x` (initial `1.0`). On `main` it is bumped once per change set by whoever edits the files (under fan-out, the lead or the unit it names). Feature branches never touch it; a branch lands as `git rebase main` on the branch, then `git merge --squash` on `main`, and the squash commit bumps it.
- `scripts/deploy` reads `VERSION` from the directory that contains the pack (`source.parent`), records it in the manifest as `pack_version`, prints a `Version:` line on `install`, and prints `Version: installed=…, source=…` with a `MISMATCH` marker in `status`. There is no `update` subcommand; `install` is the update path, so "install/update print the version" means `install` prints it.
- Enforcement is two-layered: (a) `tests/test_version.py`, on `main` only, fails when tracked files differ from `HEAD` and the working-tree `VERSION` is not strictly greater than `HEAD:VERSION`, and skips with a stated reason on any other branch, on a detached `HEAD`, or when git, `HEAD`, or `HEAD:VERSION` is unavailable; (b) a rule in this repo's `CLAUDE.md` tells the editing agent to bump with the change on `main`, tells `git-ops` to stage `VERSION` and not to commit on `main` with it unchanged, and keeps branches away from the file.

Rejected alternatives, one line each:
- Reading `VERSION` from `REPO_ROOT` (line 32): correct for the normal case, but the subprocess tests pass `--source <tmp>/pack` and could not exercise the missing-file case without an environment hook; `source.parent` also records the right version when `--source` points at another clone.
- A tracked pre-commit hook: not active without `core.hooksPath` in every clone, and `scripts/deploy` targets `~/.claude`, not the repo's git config; per-clone setup is the fragile part.
- Comparing against `origin/main`: depends on a fetched remote ref and fails right after a push; the every-commit rule needs only `HEAD`, which works offline.
- Adding the rule to `pack/skills/git-safety`: that skill ships to every repo; the rule is specific to this one.
- A branch-agnostic rule: rejected by the user; branches that bump produce duplicate numbers and merge conflicts on `VERSION`.

## Files

Modify:
- `scripts/deploy`: `read_pack_version()`, `install_cmd` read/print/record, `status_cmd` comparison line.
- `tests/test_deploy.py`: four new tests under a `# ---- version` section.
- `CLAUDE.md`: two rule bullets.
- `README.md`: one `**Version:**` line and one Repository Layout row.
- `docs/deploy.md`: one bullet under What Install Does, one under Notes For Claude Running This.

Create:
- `VERSION`: exactly `1.0\n`.
- `tests/test_version.py`: format test, pure bump-rule test, git-backed bump test.

Unchanged: `pack/` (everything), `docs/architecture.md`, `tests/test_pack_lint.py`, `MANIFEST_VERSION`.

## Interfaces And Data Changes

### `VERSION`

- Content: `1.0\n` (one line, ASCII, trailing newline, no leading zeros, no `v` prefix). Grammar: `[1-9][0-9]*\.(0|[1-9][0-9]*)\n`.
- Semantics: `1.x`; x is raised in every commit on `main`, normally by one, and is unbounded; feature branches never change it. The bump test only requires an increase. Major bumps are out of scope.
- Initial value `1.0` in the commit that introduces the file; that commit is exempt from the bump test because `HEAD:VERSION` does not exist yet. Every later commit on `main` bumps.
- Tracked by git (no `.gitignore` change). Not copied by deploy (it is outside `pack/`).

### `scripts/deploy`

New helper, placed after `git_info` (ends line 279) and before `FABLE_TOKEN` (line 284). `Optional` is already imported (line 25). The file's format is enforced by `tests/test_version.py`, not here.

```python
def read_pack_version(source: Path) -> Optional[str]:
    """The checkout's VERSION (the file next to the pack dir), or None when there is none."""
    path = source.parent / "VERSION"
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip() or None
```

`install_cmd` (493-625):
- After `src_files = collect_source(source)` (line 495): `pack_version = read_pack_version(source)`.
- After the `Fable:` print (lines 508-509), inside the lock so `manifest` is loaded:

```python
prev = manifest.get("pack_version")
print("Version: %s%s" % (pack_version or "unknown (no VERSION file in %s)" % source.parent,
                         " (was %s)" % prev if pack_version and prev and prev != pack_version else ""))
```

- In `new_manifest` (599-608), add `"pack_version": pack_version,` after `"source_dirty": dirty,`.

`status_cmd` (655-686), in the `else` branch, after `source = ...` (line 670) and before `rows = file_states(...)`:

```python
recorded = manifest.get("pack_version")
current = read_pack_version(source) if source.is_dir() else None
flag = " (MISMATCH: run scripts/deploy install)" if recorded and current and recorded != current else ""
print("Version: installed=%s, source=%s%s" % (recorded or "not recorded", current or "unknown", flag))
```

Output order in `status` becomes: Target, Source, Commit, Installed, Fable, Version, file rows, Files, Settings agent. The new line must not start with two spaces: existing tests select file rows with `l.startswith("  ")` (lines 411-412, 490-491).

No parser changes (`build_parser`, 855-904). No new flags. `MANIFEST_VERSION` stays 1.

Python 3.9 rules for the executor: `Optional[str]`, not `str | None`; `%` formatting, no f-strings; no `match`, no walrus; stdlib only.

### Manifest

`<target>/.claude-agents-manifest.json` gains one key: `"pack_version": "1.0"` (string) or `null` when the source has no `VERSION`. Manifests written before this change lack the key; `status` prints `installed=not recorded` and the next `install` records it. `load_manifest` is unchanged.

### Output

| Command | Line | When |
|---|---|---|
| install | `Version: 1.7` | fresh install, or re-install at the same version |
| install | `Version: 1.8 (was 1.7)` | re-install at a new version |
| install | `Version: unknown (no VERSION file in <source.parent>)` | no `VERSION` next to the pack |
| status | `Version: installed=1.7, source=1.7` | match |
| status | `Version: installed=1.7, source=1.8 (MISMATCH: run scripts/deploy install)` | mismatch, exit code stays 0 |
| status | `Version: installed=not recorded, source=1.7` | manifest predates this change, or was installed without `VERSION` |
| status | `Version: installed=1.7, source=unknown` | source dir has no `VERSION` or is gone |

### Enforcement

`tests/test_version.py` (new, stdlib + pytest):

```python
"""Checks on the repo-root VERSION file: its format, and a bump in every commit on main."""
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = REPO_ROOT / "VERSION"
FORMAT = re.compile(r"[1-9]\d*\.(0|[1-9]\d*)\n")


def git(*args: str) -> Optional[str]:
    """stdout of a git command in the repo, or None when git is missing or the command fails."""
    try:
        r = subprocess.run(["git", "-C", str(REPO_ROOT)] + list(args),
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def parse(text: str) -> Tuple[int, int]:
    major, minor = text.strip().split(".")
    return int(major), int(minor)


def bump_ok(committed: str, worktree: str, changed: bool) -> bool:
    """The rule: with tracked changes, the working-tree VERSION must exceed HEAD's; otherwise anything goes."""
    return not changed or parse(worktree) > parse(committed)
```

Tests:
- `test_version_file_format`: `VERSION_FILE.is_file()` and `FORMAT.fullmatch(VERSION_FILE.read_text(encoding="utf-8"))`.
- `test_bump_rule`, parametrized over `(committed, worktree, changed, expected)`: `("1.0\n", "1.1\n", True, True)`, `("1.0\n", "1.0\n", True, False)`, `("1.0\n", "1.0\n", False, True)`, `("1.9\n", "1.10\n", True, True)`, `("1.2\n", "1.1\n", True, False)`. This is the deterministic test of the rule; it needs no git.
- `test_version_bumped_with_changes`: `branch = git("rev-parse", "--abbrev-ref", "HEAD")`; `if branch is None or branch.strip() != "main": pytest.skip("bump rule applies on main only (on %s)" % (branch.strip() if branch else "no git"))` (a detached `HEAD` prints `HEAD`, so it skips too). `committed = git("show", "HEAD:VERSION")`; `if committed is None: pytest.skip("HEAD:VERSION unavailable")`. `changed = git("status", "--porcelain", "--untracked-files=no")`; `if changed is None: pytest.skip("git status unavailable")` (an empty string is a clean tree, not a skip). Then `assert bump_ok(committed, VERSION_FILE.read_text(encoding="utf-8"), bool(changed.strip()))`, with a message naming both values and the rule ("every commit on main bumps VERSION"). A clean `main` passes trivially; any other branch, a tarball, or a repo without git skips; the commit that introduces `VERSION` skips.

Why this is the least fragile mechanism: it needs only `HEAD`, so it works offline and immediately after a push; it never touches remote refs or hooks; the only state it reads is the working tree, which is exactly what the next commit will contain; and the skip conditions cover every environment where the rule cannot apply, including every branch other than `main`. The pure `bump_ok` keeps the rule testable without git state.

`CLAUDE.md` rule (append as the last two bullets):

```
- `VERSION` holds the pack version as `1.x`. Every commit on `main` raises x (normally by one), once per change set: the editing agent (under fan-out, the lead or the unit it names, not every worker) bumps `VERSION` with the change before running the tests; `tests/test_version.py` fails on `main` when tracked files differ from `HEAD` and `VERSION` was not raised. `git-ops` stages `VERSION` with the commit when it is modified in the working tree and, on `main`, escalates instead of committing when the staged diff leaves it unchanged (`git diff --cached --stat -- VERSION` is empty).
- Feature branches never touch `VERSION`. To land a branch: `git rebase main` on the branch, then `git merge --squash <branch>` on `main`, and bump `VERSION` in the squash commit. These two rules are specific to this repo and stay out of the `git-safety` skill.
```

Why the rule works: Claude Code injects the project `CLAUDE.md` into subagents (this planning session, itself a subagent, received it), and `git-ops` already runs `git diff --cached --stat` before committing (`git-safety` l.21). `git-ops` stages only the paths its brief names (`git-ops.md` l.17), so the rule tells it to add `VERSION` itself; it has no Write or Edit tool, so the bump belongs to the editing agent and the rule says so.

### Tests in `tests/test_deploy.py`

Append a `# ---- version` section at the end of the file. Helper:

```python
def version_file(pack: Path, text: str) -> None:
    (pack.parent / "VERSION").write_text(text)
```

(`pack` is `tmp_path/pack`, so this writes `tmp_path/VERSION`, outside the target `tmp_path/claude`.)

- `test_install_records_pack_version(pack, target)`: `version_file(pack, "1.7\n")`; install; returncode 0; `"Version: 1.7" in r.stdout`; `manifest(target)["pack_version"] == "1.7"`.
- `test_install_without_version_file(pack, target)`: install with the fixture as is; returncode 0; `"Version: unknown (no VERSION file in" in r.stdout`; `manifest(target)["pack_version"] is None`; then status: `"Version: installed=not recorded, source=unknown" in r.stdout`.
- `test_status_version_match_and_mismatch(pack, target)`: `1.7`, install, status shows `Version: installed=1.7, source=1.7` and no `MISMATCH`; write `1.8`, status returncode 0 and shows `Version: installed=1.7, source=1.8 (MISMATCH: run scripts/deploy install)`; install shows `Version: 1.8 (was 1.7)` and the manifest holds `"1.8"`.
- `test_status_old_manifest_without_pack_version(pack, target)`: `1.7`, install, delete `pack_version` from the manifest JSON and rewrite it (model: `test_fable_old_manifest_not_recorded`, 483-494); status shows `Version: installed=not recorded, source=1.7`; file rows (`l.startswith("  ")`) are non-empty and all end with `ok`, which guards the two-space pitfall.

Python 3.9 compatibility gets no new test. No existing test checks it either; the validation commands run `py_compile` and a real install under `/usr/bin/python3` (3.9.6), which is the actual check.

### Docs

`README.md`:
- After line 26 (`**Check:** ... **Remove:** ...`): `**Version:** \`VERSION\` holds the pack version (\`1.x\`, bumped in every commit on main). \`scripts/deploy status\` shows the installed version next to the checkout's and marks a \`MISMATCH\`.`
- Repository Layout block (lines 104-110): add a row `VERSION             pack version (1.x, bumped in every commit on main)` after the `docs/` row, aligned with the existing columns.

`docs/deploy.md`:
- What Install Does, new bullet after "Validates every source agent and skill..." (line 36): `- Records the checkout's \`VERSION\` (the file next to \`pack/\`) as \`pack_version\` in the manifest and prints \`Version: 1.x\`, with \`(was 1.y)\` on an update. \`status\` prints \`Version: installed=1.x, source=1.y\` and appends \`(MISMATCH: run scripts/deploy install)\` when they differ. Manifests from before versioning show \`installed=not recorded\` until the next install.`
- Notes For Claude Running This, new bullet after the exit-codes bullet (line 89): `- If \`status\` shows \`MISMATCH\`, the installed pack is not the checkout's version: run \`install\`.`

`CLAUDE.md`: the two rule bullets above. `docs/architecture.md`: no change (it never mentions the manifest).

## Steps

Four units, A-D. Partition, waves, and per-unit validation are under Orchestration.

Unit A, `scripts/deploy`:
1. Add `read_pack_version` after `git_info` (after line 279).
2. In `install_cmd`: read after line 495; print after line 509; add the `pack_version` manifest key after line 603.
3. In `status_cmd`: add the `Version:` block after line 670.
4. Run `/usr/bin/python3 -m py_compile scripts/deploy`.

Unit B, `tests/test_deploy.py`:
5. Append the `# ---- version` section: `version_file` helper and the four tests exactly as specified above.

Unit C, `VERSION` and `tests/test_version.py`:
6. Create `VERSION` with `printf '1.0\n' > VERSION`.
7. Create `tests/test_version.py` with `git`, `parse`, `bump_ok`, and the three tests specified above.

Unit D, docs:
8. `CLAUDE.md`: append the two rule bullets.
9. `README.md`: the `**Version:**` line and the layout row.
10. `docs/deploy.md`: the two bullets.

Integration:
11. Run the validation commands below. Expect `test_version_bumped_with_changes` to skip until the commit that adds `VERSION` exists in `HEAD` on `main`.
12. The commit that introduces `VERSION` (directly on `main`, or the squash commit that lands this work) does not need a bump: there is no `HEAD:VERSION` yet. Every commit on `main` after it bumps.

## Risks And Compatibility

- Status row filter: tests select file rows by a two-space prefix; the `Version:` line starts at column 0. Covered by `test_status_old_manifest_without_pack_version`.
- Old manifests: no `pack_version` key reads as `not recorded`; `load_manifest` is untouched and `MANIFEST_VERSION` stays 1, so older scripts still load new manifests.
- `--source` pointing at a bare pack directory with no sibling `VERSION`: `Version: unknown`, not an error.
- On `main`, the bump test fails by design on a dirty tree without a bump; every change set made on `main` must bump `VERSION` before running `python3 -m pytest -q`, and a squash merge counts as a dirty tree until its commit. The CLAUDE.md rule says so. This is the intended reminder, not a flake.
- A stray branch bump surfaces as a one-line conflict that `git-ops` already classes as mechanical (`pack/agents/git-ops.md`, l.36 and l.42); resolution is out of scope here.
- `git status --porcelain --untracked-files=no` counts staged and unstaged changes to tracked files and ignores untracked and ignored files, so scratch files never trigger the rule.
- No existing test asserts the exact set of manifest keys (checked at ff60106), so the new key breaks nothing.

## Acceptance Criteria

1. `VERSION` exists with content exactly `1.0\n` (`cat -e VERSION` prints `1.0$`).
2. `scripts/deploy install --source pack --target <tmp>` prints `Version: 1.0` and writes `"pack_version": "1.0"` to the manifest; `MANIFEST_VERSION` is still 1.
3. `scripts/deploy status --source <copy-with-1.1> --target <tmp>` prints `Version: installed=1.0, source=1.1 (MISMATCH: run scripts/deploy install)` and exits 0; a re-install prints `Version: 1.1 (was 1.0)`.
4. Without a `VERSION` next to the source: `Version: unknown (no VERSION file in ...)`, manifest `pack_version` is `null`, exit 0.
5. A manifest without `pack_version` yields `installed=not recorded`.
6. `tests/test_version.py`: format test passes, `test_bump_rule` passes all five cases, `test_version_bumped_with_changes` skips before the introducing commit exists, skips on any branch other than `main` and on a detached `HEAD`, and passes on a clean `main` afterwards.
7. `python3 -m pytest -q` passes; `/usr/bin/python3 -m py_compile scripts/deploy` prints nothing; the `/usr/bin/python3` install and status commands below succeed.
8. `CLAUDE.md`, `README.md`, and `docs/deploy.md` carry the lines specified; this work changes nothing under `pack/`.

## Validation Commands

```bash
cd /Users/sjoosten/Work/claude-agents
cat -e VERSION                                       # expect: 1.0$
python3 -m pytest -q                                 # expect: all pass; 1 skip (bump test) until main has VERSION, and always off main
/usr/bin/python3 -m py_compile scripts/deploy        # expect: no output
T=$(mktemp -d)
/usr/bin/python3 scripts/deploy install --source pack --target "$T/claude" --fable yes --yes
#   expect: a "Version: 1.0" line, exit 0
/usr/bin/python3 scripts/deploy status --source pack --target "$T/claude"
#   expect: "Version: installed=1.0, source=1.0", no MISMATCH, exit 0
mkdir -p "$T/src" && cp -R pack "$T/src/pack" && printf '1.1\n' > "$T/src/VERSION"
/usr/bin/python3 scripts/deploy status --source "$T/src/pack" --target "$T/claude"
#   expect: "Version: installed=1.0, source=1.1 (MISMATCH: run scripts/deploy install)", exit 0
/usr/bin/python3 scripts/deploy install --source "$T/src/pack" --target "$T/claude" --fable yes --yes
#   expect: "Version: 1.1 (was 1.0)"
rm -rf "$T"
```

Do not run `scripts/deploy install` against the real `~/.claude` during validation. After the introducing commit exists, on `main`, a one-time manual check of the enforcement path: edit any tracked file, run `python3 -m pytest -q tests/test_version.py` (expect one failure naming `VERSION`), set `VERSION` to `1.1`, run again (expect pass), then revert both edits.

## Open Questions

None.

## Todo

Unit A (`scripts/deploy`)
- [x] `scripts/deploy`: `read_pack_version()` after `git_info`
- [x] `scripts/deploy`: `install_cmd` reads `VERSION` after `collect_source`, prints `Version:` after `Fable:`, records `pack_version` in `new_manifest`
- [x] `scripts/deploy`: `status_cmd` prints `Version: installed=…, source=…` with the `MISMATCH` suffix after `source` is resolved
- [x] `/usr/bin/python3 -m py_compile scripts/deploy` passes

Unit B (`tests/test_deploy.py`)
- [x] `tests/test_deploy.py`: `version_file` helper and `# ---- version` section
- [x] `tests/test_deploy.py`: `test_install_records_pack_version`, `test_install_without_version_file`, `test_status_version_match_and_mismatch`, `test_status_old_manifest_without_pack_version`

Unit C (`VERSION`, `tests/test_version.py`)
- [x] `VERSION`: `1.0\n`
- [x] `tests/test_version.py`: `git`, `parse`, `bump_ok`, `test_version_file_format`, `test_bump_rule`, `test_version_bumped_with_changes`

Unit D (docs)
- [x] `CLAUDE.md`: the two version rule bullets
- [x] `README.md`: `**Version:**` line after the Check/Remove line; `VERSION` row in Repository Layout
- [x] `docs/deploy.md`: What Install Does bullet; Notes For Claude Running This bullet

Integration
- [x] Run the validation commands; `python3 -m pytest -q` passes with the bump test skipped
- [x] Confirm `git diff --stat -- pack/` shows nothing from this work

## Scope Notes

In scope: the files listed under Files, nothing else.

Out of scope: major-version bumps, changelogs, releases, tags, CI, git hooks, a `doctor` check, a `--version` flag, a non-zero `status` exit, a `MANIFEST_VERSION` bump, an environment override for the repo root, anything under `pack/` (including `git-safety` and `git-ops.md`), `docs/architecture.md`, `tests/test_pack_lint.py`.

Where creep is most likely, and what to resist:
- `scripts/deploy`: adding parser flags, help text, or a `doctor` row; validating `VERSION`'s format in deploy (the repo test does that); refactoring `git_info` or the manifest builder while nearby.
- Tests: adding git fixtures or mocks to `tests/test_version.py` (the pure `bump_ok` cases cover the rule); deduplicating `load_deploy` across test files; asserting more of the `install` output than the `Version:` line.
- Docs: rewriting surrounding paragraphs instead of adding the named lines; documenting the manifest schema in full.
- Agents: adding an escalation bullet to `pack/agents/git-ops.md` or a rule to `git-safety`. The rule lives in this repo's `CLAUDE.md` only.

User decisions the executor must not reopen: a one-line `VERSION` file at the repo root; manual bumps; the `1.x` scheme with x unbounded; initial value `1.0`; every commit on `main` bumps x, feature branches never touch `VERSION`, and a branch lands by `git rebase main` then `git merge --squash` on `main` with the squash commit bumping; `scripts/deploy status` keeps exit code 0 on `MISMATCH`; no git tags; this repo only; the rule lives in `CLAUDE.md`, not in `pack/` `git-safety`.

## Orchestration

This is the executor's default partition; deviate only where the code contradicts it. Units are the Steps units above; each owns its files exclusively.

| Unit | Owns | Validation by the worker |
|---|---|---|
| A | `scripts/deploy` | `/usr/bin/python3 -m py_compile scripts/deploy`; `/usr/bin/python3 scripts/deploy install --dry-run --source pack --target "$(mktemp -d)/claude" --fable yes` prints a `Version:` line (`unknown` until unit C lands) |
| B | `tests/test_deploy.py` | `python3 -m py_compile tests/test_deploy.py`; `python3 -m pytest -q tests/test_deploy.py -k version` (the four new tests fail until unit A lands; nothing else may fail) |
| C | `VERSION`, `tests/test_version.py` | `cat -e VERSION` prints `1.0$`; `python3 -m pytest -q tests/test_version.py` reports 6 passed, 1 skipped |
| D | `CLAUDE.md`, `README.md`, `docs/deploy.md` | `grep -n VERSION CLAUDE.md README.md docs/deploy.md` shows the five added lines |

Waves: one. All four units run in parallel; none depends on another's output at edit time (unit B is written against the output strings and manifest key specified in this plan, not against unit A's code).

The lead integrates: re-run the full Validation Commands after the wave. No glue code is expected because the files are disjoint.
