"""Behavior tests for `deploy memory` (externalize, link, status), run as a subprocess against scratch repos."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from test_deploy import SCRIPT, load_deploy

TEMPLATE_REL = Path("skills") / "project-memory" / "templates" / "store-readme.md"
REAL_TEMPLATE = SCRIPT.parent / "pack" / TEMPLATE_REL
MARKER = "<!-- claude-supervisor memory: rewritten on every run -->"
GIT = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
GIT_ENV = dict({k: os.environ[k] for k in ("PATH", "TMPDIR", "LANG", "LC_ALL") if k in os.environ},
               HOME=os.devnull, GIT_CONFIG_NOSYSTEM="1", **GIT)  # no inherited GIT_DIR or user config


def base_env(tmp_path: Path) -> dict:
    env = {k: os.environ[k] for k in ("PATH", "TMPDIR", "LANG", "LC_ALL") if k in os.environ}
    env.update(GIT)
    env["HOME"] = str(tmp_path / "home")
    env["XDG_DATA_HOME"] = str(tmp_path / "xdg")
    return env


def git(cwd: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(cwd)] + list(args), capture_output=True, text=True,
                       env=GIT_ENV, timeout=60, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, "git %s: %s" % (args, r.stderr)
    return r.stdout


def git_rc(cwd: Path, *args: str) -> int:
    return subprocess.run(["git", "-C", str(cwd)] + list(args), capture_output=True, env=GIT_ENV,
                          stdin=subprocess.DEVNULL, timeout=60).returncode


@pytest.fixture
def tgt(tmp_path: Path) -> Path:
    """A target with the installed project-memory template."""
    t = tmp_path / "target"
    (t / TEMPLATE_REL).parent.mkdir(parents=True)
    (t / TEMPLATE_REL).write_text(REAL_TEMPLATE.read_text())
    return t


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "proj"
    r.mkdir()
    git(r, "init", "-q")
    git(r, "commit", "-q", "--allow-empty", "-m", "init")
    return r


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path / "mem"


def memory(tmp_path: Path, target: Path, cwd: Path, verb: str, *args: str, env=None):
    env_ = base_env(tmp_path)
    env_.update(env or {})
    cmd = [sys.executable, str(SCRIPT), "memory", "--target", str(target), verb] + list(args)
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, env=env_, timeout=60,
                          stdin=subprocess.DEVNULL)


def store(repo: Path, claude_local: str = "local\n") -> None:
    (repo / ".supervisor").mkdir()
    (repo / ".supervisor" / "note.md").write_text("note\n")
    (repo / "CLAUDE.local.md").write_text(claude_local)


def exclude_lines(repo: Path) -> list:
    p = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-path", "info/exclude").strip())
    return p.read_text().splitlines() if p.exists() else []


def extern(tmp_path, tgt, repo, root, *args):
    r = memory(tmp_path, tgt, repo, "externalize", "--root", str(root), *args)
    assert r.returncode == 0, r.stdout + r.stderr
    return r


def test_externalize_moves_existing_store(tmp_path, tgt, repo, root):
    store(repo)
    r = extern(tmp_path, tgt, repo, root)
    ext = root.resolve() / "proj"
    for n in (".supervisor", "CLAUDE.local.md"):
        assert (repo / n).is_symlink()
        assert os.readlink(str(repo / n)) == str(ext / n)
        assert git_rc(repo, "check-ignore", "-q", n) == 0
    assert (ext / ".supervisor" / "note.md").read_text() == "note\n"
    assert (repo / "CLAUDE.local.md").read_text() == "local\n"
    assert git(repo, "status", "--porcelain") == ""
    assert "moved: " in r.stdout and "externalized: %s" % ext in r.stdout


def test_externalize_creates_new_store(tmp_path, tgt, repo, root):
    r = extern(tmp_path, tgt, repo, root)
    ext = root.resolve() / "proj"
    assert (ext / ".supervisor" / "README.md").read_bytes() == REAL_TEMPLATE.read_bytes()
    assert (ext / "CLAUDE.local.md").read_bytes() == b""
    assert (repo / ".supervisor").is_symlink() and (repo / "CLAUDE.local.md").is_symlink()
    assert (ext / "README.md").read_text().splitlines()[0] == MARKER
    assert "created: " in r.stdout and "linked: " in r.stdout


def test_externalize_name_from_origin(tmp_path, tgt, repo, root):
    git(repo, "remote", "add", "origin", "git@h:org/proj.git")
    extern(tmp_path, tgt, repo, root)
    assert (root / "proj" / ".supervisor").is_dir()
    # no origin: toplevel basename
    other = tmp_path / "other-checkout"
    other.mkdir()
    git(other, "init", "-q")
    extern(tmp_path, tgt, other, root)
    assert (root / "other-checkout" / ".supervisor").is_dir()
    # --name
    third = tmp_path / "third"
    third.mkdir()
    git(third, "init", "-q")
    extern(tmp_path, tgt, third, root, "--name", "x")
    assert (root / "x" / ".supervisor").is_dir()
    # bad names
    for bad in ("a/b", ".", ".."):
        r = memory(tmp_path, tgt, third, "externalize", "--root", str(root), "--name", bad)
        assert r.returncode == 2 and "invalid project name" in r.stderr and r.stderr.startswith("error: ")


def test_externalize_refuses_tracked_store(tmp_path, tgt, repo, root):
    store(repo)
    git(repo, "add", ".supervisor/note.md")
    git(repo, "commit", "-q", "-m", "track")
    r = memory(tmp_path, tgt, repo, "externalize", "--root", str(root))
    assert r.returncode == 2
    assert "git rm -r --cached .supervisor" in r.stderr
    assert (repo / ".supervisor").is_dir() and not (repo / ".supervisor").is_symlink()
    assert not root.exists()


def test_tracked_but_deleted_refused(tmp_path, tgt, repo, root):
    store(repo)
    git(repo, "add", ".supervisor/note.md")
    git(repo, "commit", "-q", "-m", "track")
    git(repo, "rm", "-q", "-r", "--cached", ".supervisor")
    git(repo, "commit", "-q", "-m", "untrack")
    git(repo, "add", "CLAUDE.local.md")
    git(repo, "commit", "-q", "-m", "track local")
    (repo / "CLAUDE.local.md").unlink()
    (root / "proj" / ".supervisor").mkdir(parents=True)
    for verb in ("externalize", "link"):
        r = memory(tmp_path, tgt, repo, verb, "--root", str(root))
        assert r.returncode == 2 and "git rm -r --cached CLAUDE.local.md" in r.stderr, (verb, r.stderr)
        assert not (repo / "CLAUDE.local.md").is_symlink()


def test_externalize_refuses_symlinked_project_dir(tmp_path, tgt, repo, root):
    root.mkdir()
    (root / "proj").symlink_to(repo / "mem")
    r = memory(tmp_path, tgt, repo, "externalize", "--root", str(root))
    assert r.returncode == 2 and "lies inside the checkout" in r.stderr
    assert not (repo / "mem").exists()


def test_externalize_refuses_existing_external(tmp_path, tgt, repo, root):
    (root / "proj" / ".supervisor").mkdir(parents=True)
    before = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
    r = memory(tmp_path, tgt, repo, "externalize", "--root", str(root))
    assert r.returncode == 2
    assert "claude-supervisor memory link" in r.stderr
    assert sorted(p.relative_to(root).as_posix() for p in root.rglob("*")) == before
    assert not (repo / ".supervisor").exists() and not (repo / ".supervisor").is_symlink()
    assert exclude_lines(repo) == [] or "/.supervisor" not in exclude_lines(repo)


def test_externalize_refuses_other_link(tmp_path, tgt, repo, root):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (repo / ".supervisor").symlink_to(elsewhere)
    r = memory(tmp_path, tgt, repo, "externalize", "--root", str(root))
    assert r.returncode == 2
    assert "is a link to %s, not to" % elsewhere in r.stderr
    assert os.readlink(str(repo / ".supervisor")) == str(elsewhere)
    assert not root.exists()


def test_externalize_preflight_atomic(tmp_path, tgt, repo, root):
    store(repo)
    (root / "proj").mkdir(parents=True)
    (root / "proj" / "CLAUDE.local.md").write_text("already\n")
    r = memory(tmp_path, tgt, repo, "externalize", "--root", str(root))
    assert r.returncode == 2 and "both exist" in r.stderr
    assert (repo / ".supervisor").is_dir() and not (repo / ".supervisor").is_symlink()
    assert not (root / "proj" / ".supervisor").exists()


def test_externalize_refuses_inside_project(tmp_path, tgt, repo):
    r = memory(tmp_path, tgt, repo, "externalize", "--root", str(repo / "mem"))
    assert r.returncode == 2 and "lies inside the checkout" in r.stderr
    assert not (repo / "mem").exists() and not (repo / ".supervisor").is_symlink()
    wt = tmp_path / "wt"
    git(repo, "worktree", "add", "-q", str(wt), "-b", "side")
    r = memory(tmp_path, tgt, repo, "externalize", "--root", str(wt / "mem"))
    assert r.returncode == 2 and "lies inside the checkout" in r.stderr
    assert not (wt / "mem").exists()


def test_externalize_refuses_foreign_readme(tmp_path, tgt, repo, root):
    store(repo)
    (root / "proj").mkdir(parents=True)
    (root / "proj" / "README.md").write_text("mine\n")
    r = memory(tmp_path, tgt, repo, "externalize", "--root", str(root))
    assert r.returncode == 2 and "is not written by claude-supervisor" in r.stderr
    assert (root / "proj" / "README.md").read_text() == "mine\n"
    assert (repo / ".supervisor").is_dir() and not (repo / ".supervisor").is_symlink()


def test_externalize_in_linked_worktree(tmp_path, tgt, repo, root):
    wt = tmp_path / "wt"
    git(repo, "worktree", "add", "-q", str(wt), "-b", "side")
    r = memory(tmp_path, tgt, wt, "externalize", "--root", str(root))
    assert r.returncode == 2
    assert "externalize runs in the main checkout (%s)" % repo.resolve() in r.stderr
    assert not (wt / ".supervisor").exists()


def test_externalize_idempotent(tmp_path, tgt, repo, root):
    store(repo)
    extern(tmp_path, tgt, repo, root)
    r = extern(tmp_path, tgt, repo, root)
    assert "externalized: " in r.stdout
    lines = exclude_lines(repo)
    assert lines.count("/.supervisor") == 1 and lines.count("/CLAUDE.local.md") == 1
    gi = (root / "proj" / ".gitignore").read_text().splitlines()
    assert gi.count(".supervisor/working/residue/") == 1


def test_externalize_refreshes_old_readme(tmp_path, tgt, repo, root):
    extern(tmp_path, tgt, repo, root)
    readme = root.resolve() / "proj" / ".supervisor" / "README.md"
    readme.write_text("old text: add .supervisor/ to .gitignore\n")
    r = extern(tmp_path, tgt, repo, root)
    assert readme.read_bytes() == REAL_TEMPLATE.read_bytes()
    assert "refreshed README" in r.stdout


def test_externalize_gitignore_before_git(tmp_path, tgt, repo, root):
    extern(tmp_path, tgt, repo, root)
    ext = root / "proj"
    git(root, "init", "-q")
    res = ext / ".supervisor" / "working" / "residue"
    res.mkdir(parents=True)
    (res / "a.md").write_text("x\n")
    assert "residue" not in git(root, "status", "--porcelain")
    extern(tmp_path, tgt, repo, root)
    assert (ext / ".gitignore").read_text().splitlines().count(".supervisor/working/residue/") == 1


def test_externalize_requires_pack(tmp_path, repo, root):
    empty = tmp_path / "empty-target"
    empty.mkdir()
    r = memory(tmp_path, empty, repo, "externalize", "--root", str(root))
    assert r.returncode == 2 and "store-readme.md is missing; install the pack first" in r.stderr
    assert not root.exists()


def test_externalize_outside_git(tmp_path, tgt, root):
    plain = tmp_path / "plain"
    plain.mkdir()
    r = memory(tmp_path, tgt, plain, "externalize", "--root", str(root),
               env={"GIT_CEILING_DIRECTORIES": str(tmp_path)})
    assert r.returncode == 2 and "not a git repository" in r.stderr


def test_default_root_from_env(tmp_path, tgt, repo):
    r = memory(tmp_path, tgt, repo, "externalize")
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "xdg" / "claude-supervisor" / "memory" / "proj" / ".supervisor").is_dir()
    r = memory(tmp_path, tgt, repo, "externalize",
               env={"CLAUDE_SUPERVISOR_MEMORY_ROOT": str(tmp_path / "envroot")})
    assert r.returncode == 2  # the store now lives under xdg: the link is "other" for envroot
    assert str(tmp_path / "envroot") in r.stderr


def test_status_ok(tmp_path, tgt, repo, root):
    extern(tmp_path, tgt, repo, root)
    r = memory(tmp_path, tgt, repo, "status")
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.startswith("ok: %s -> %s" % (repo.resolve(), root.resolve() / "proj"))


def test_status_dangling(tmp_path, tgt, repo, root):
    extern(tmp_path, tgt, repo, root)
    (root / "proj" / "CLAUDE.local.md").unlink()
    r = memory(tmp_path, tgt, repo, "status")
    assert r.returncode == 1
    assert "CLAUDE.local.md: dangling link to" in r.stdout


def test_status_missing_exclude(tmp_path, tgt, repo, root):
    extern(tmp_path, tgt, repo, root)
    p = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-path", "info/exclude").strip())
    p.write_text("")
    r = memory(tmp_path, tgt, repo, "status")
    assert r.returncode == 1
    assert "missing /.supervisor in info/exclude" in r.stdout


def test_launcher_routes_memory():
    deploy = load_deploy()
    assert "memory" in deploy.LAUNCHER_COMMANDS
    text = deploy.launcher_text("TAG", Path("/TARGET"), Path("/PREFIX"), None, False)
    assert "update|uninstall|list|status|memory)" in text
    assert "memory externalize|link|status" in text


# ---- link

def prepared_external(tmp_path, tgt, repo, root):
    """Externalize in `repo`, then return the external dir."""
    extern(tmp_path, tgt, repo, root)
    return root.resolve() / "proj"


def test_link_fresh_machine(tmp_path, tgt, repo, root):
    ext = root.resolve() / "proj"
    (ext / ".supervisor").mkdir(parents=True)
    (ext / ".supervisor" / "k.md").write_text("k\n")
    r = memory(tmp_path, tgt, repo, "link", "--root", str(root))
    assert r.returncode == 0, r.stdout + r.stderr
    assert os.readlink(str(repo / ".supervisor")) == str(ext / ".supervisor")
    assert os.readlink(str(repo / "CLAUDE.local.md")) == str(ext / "CLAUDE.local.md")
    assert (ext / "CLAUDE.local.md").is_file()
    lines = exclude_lines(repo)
    assert "/.supervisor" in lines and "/CLAUDE.local.md" in lines
    assert "linked: %s" % ext in r.stdout


def test_link_explicit_dir(tmp_path, tgt, repo, root):
    d = tmp_path / "somewhere" / "store"
    (d / ".supervisor").mkdir(parents=True)
    r = memory(tmp_path, tgt, repo, "link", "--root", str(root), "--name", "ignored", str(d))
    assert r.returncode == 0, r.stdout + r.stderr
    assert os.readlink(str(repo / ".supervisor")) == str(d.resolve() / ".supervisor")
    assert not root.exists()


def test_link_refuses_real_store(tmp_path, tgt, repo, root):
    store(repo)
    (root / "proj" / ".supervisor").mkdir(parents=True)
    r = memory(tmp_path, tgt, repo, "link", "--root", str(root))
    assert r.returncode == 2
    assert "is a real file in the project; run `claude-supervisor memory externalize`" in r.stderr
    assert not (repo / ".supervisor").is_symlink()


def test_link_missing_external(tmp_path, tgt, repo, root):
    r = memory(tmp_path, tgt, repo, "link", "--root", str(root))
    assert r.returncode == 2
    assert "no external store at %s" % (root.resolve() / "proj") in r.stderr
    assert not (repo / ".supervisor").is_symlink()


def test_link_in_worktree(tmp_path, tgt, repo, root):
    ext = prepared_external(tmp_path, tgt, repo, root)
    wt = tmp_path / "wt"
    git(repo, "worktree", "add", "-q", str(wt), "-b", "side")
    r = memory(tmp_path, tgt, wt, "link", "--root", str(root))
    assert r.returncode == 0, r.stdout + r.stderr
    assert os.readlink(str(wt / ".supervisor")) == str(ext / ".supervisor")
    assert os.readlink(str(wt / "CLAUDE.local.md")) == str(ext / "CLAUDE.local.md")
    assert git(wt, "status", "--porcelain") == ""
    st = memory(tmp_path, tgt, wt, "status")
    assert st.returncode == 0, st.stdout + st.stderr
    git(repo, "worktree", "remove", str(wt))
    assert not wt.exists()


def test_link_repairs_partial(tmp_path, tgt, repo, root):
    ext = prepared_external(tmp_path, tgt, repo, root)
    (repo / "CLAUDE.local.md").unlink()
    p = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-path", "info/exclude").strip())
    p.write_text("")
    r = memory(tmp_path, tgt, repo, "link", "--root", str(root))
    assert r.returncode == 0, r.stdout + r.stderr
    assert os.readlink(str(repo / "CLAUDE.local.md")) == str(ext / "CLAUDE.local.md")
    lines = exclude_lines(repo)
    assert "/.supervisor" in lines and "/CLAUDE.local.md" in lines


def test_link_refuses_other_link(tmp_path, tgt, repo, root):
    (root / "proj" / ".supervisor").mkdir(parents=True)
    (repo / ".supervisor").symlink_to(tmp_path / "nowhere")
    r = memory(tmp_path, tgt, repo, "link", "--root", str(root))
    assert r.returncode == 2
    assert "dangling), not to" in r.stderr and "remove the link, then re-run" in r.stderr
    assert os.readlink(str(repo / ".supervisor")) == str(tmp_path / "nowhere")
