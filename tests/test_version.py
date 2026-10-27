"""Checks on the repo-root VERSION file: its format, and a bump in every commit on main that
touches a versioned path."""
import re
import subprocess
from pathlib import Path
from typing import Iterable, Optional, Tuple

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = REPO_ROOT / "VERSION"
FORMAT = re.compile(r"[1-9]\d*\.(0|[1-9]\d*)\n")
# The versioned set (CLAUDE.md): everything else is ancillary and needs no bump.
VERSIONED_DIRS = ("pack/",)
VERSIONED_FILES = ("deploy",)


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


def versioned(path: str) -> bool:
    return path in VERSIONED_FILES or path.startswith(VERSIONED_DIRS)


def bump_ok(committed: str, worktree: str, changed: Iterable[str]) -> bool:
    """The rule: when a changed tracked path is versioned, the working-tree VERSION must exceed
    HEAD's; otherwise anything goes."""
    return not any(versioned(p) for p in changed) or parse(worktree) > parse(committed)


def test_version_file_format():
    assert VERSION_FILE.is_file()
    assert FORMAT.fullmatch(VERSION_FILE.read_text(encoding="utf-8"))


PACK = ["pack/agents/git-ops.md"]
ANCILLARY = [".supervisor/memory/x.md", "docs/deploy.md", "tests/test_version.py", "CLAUDE.md",
             "README.md", "VERSION", "docs/pack/x.md", "deploy.md"]


@pytest.mark.parametrize("committed, worktree, changed, expected", [
    ("1.0\n", "1.1\n", PACK, True),
    ("1.0\n", "1.0\n", PACK, False),
    ("1.0\n", "1.0\n", ["deploy"], False),
    ("1.0\n", "1.0\n", [], True),
    ("1.0\n", "1.0\n", ANCILLARY, True),
    ("1.0\n", "1.0\n", ANCILLARY + PACK, False),
    ("1.0\n", "1.1\n", ANCILLARY + ["deploy"], True),
    ("1.9\n", "1.10\n", PACK, True),
    ("1.2\n", "1.1\n", PACK, False),
    ("1.17\n", "2.0\n", PACK, True),
    ("2.0\n", "1.18\n", PACK, False),
])
def test_bump_rule(committed, worktree, changed, expected):
    assert bump_ok(committed, worktree, changed) is expected


def test_version_bumped_with_changes():
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch is None or branch.strip() != "main":
        pytest.skip("bump rule applies on main only (on %s)" % (branch.strip() if branch else "no git"))
    committed = git("show", "HEAD:VERSION")
    if committed is None:
        pytest.skip("HEAD:VERSION unavailable")
    changed = git("diff", "HEAD", "--name-only", "--no-renames")
    if changed is None:
        pytest.skip("git diff unavailable")
    worktree = VERSION_FILE.read_text(encoding="utf-8")
    assert bump_ok(committed, worktree, changed.splitlines()), (
        "VERSION is %r in the working tree and %r at HEAD, but tracked files under a versioned "
        "path changed: every such commit on main bumps VERSION" % (worktree.strip(), committed.strip()))
