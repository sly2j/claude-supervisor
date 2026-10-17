"""Behavior tests for deploy, run as a subprocess against temp dirs."""

import fcntl
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "deploy"
MANIFEST = ".claude-supervisor-manifest.json"
LEGACY_MANIFEST = ".claude-agents-manifest.json"
LAUNCHER_MARKER = "# managed by claude-supervisor"


def agent_md(name: str, body: str = "Body.") -> str:
    return "---\nname: %s\ndescription: The %s agent.\nmodel: sonnet\n---\n\n%s\n" % (name, name, body)


@pytest.fixture
def pack(tmp_path: Path) -> Path:
    src = tmp_path / "pack"
    (src / "agents").mkdir(parents=True)
    (src / "agents" / "supervisor.md").write_text(agent_md("supervisor"))
    (src / "agents" / "helper.md").write_text(agent_md("helper"))
    (src / "agents" / ".DS_Store").write_text("junk")
    skill = src / "skills" / "demo"
    (skill / "scripts").mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: demo\ndescription: Demo skill.\n---\n\nUse it.\n")
    (skill / "scripts" / "run.sh").write_text("#!/bin/sh\necho hi\n")
    (skill / "scripts" / "__pycache__").mkdir()
    (skill / "scripts" / "__pycache__" / "x.pyc").write_bytes(b"\0")
    return src


@pytest.fixture
def target(tmp_path: Path) -> Path:
    return tmp_path / "claude"


@pytest.fixture
def global_target(tmp_path: Path) -> Path:
    return tmp_path / ".claude"


ENV_WHITELIST = ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL")


def run(pack: Path, target: Path, *args: str, target_args=None, path=None,
        env=None) -> subprocess.CompletedProcess:
    """Run deploy with a whitelisted environment (no CLAUDE_CODE_*, GIT_*, XDG_* leaks) plus `env`."""
    full = {k: os.environ[k] for k in ENV_WHITELIST if k in os.environ}
    full["PATH"] = path or str(target.parent / "bin")  # hides the real claude (and git)
    full["HOME"] = str(target.parent)  # hides the real ~/.claude.json
    full.update(env or {})
    if target_args is None:
        target_args = ["--global"] if target.name == ".claude" else ["--target", str(target)]
    cmd = [sys.executable, str(SCRIPT), args[0]] + list(target_args)
    if args[0] in ("install", "status"):
        cmd += ["--source", str(pack)]
    cmd += list(args[1:])
    return subprocess.run(cmd, capture_output=True, text=True, env=full, timeout=60,
                          stdin=subprocess.DEVNULL)


def stub_claude(bin_dir: Path, version: str = "2.1.300") -> Path:
    """Write an executable `claude` that answers --version and records any other argv to claude.argv."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    stub = bin_dir / "claude"
    stub.write_text("#!/bin/sh\n"
                    "if [ \"$1\" = --version ]; then echo '%s (Claude Code)'; exit 0; fi\n"
                    "printf '%%s\\n' \"$@\" >> '%s'\n" % (version, bin_dir / "claude.argv"))
    stub.chmod(0o755)
    return stub


def load_deploy():
    loader = importlib.machinery.SourceFileLoader("deploy_script", str(SCRIPT))
    spec = importlib.util.spec_from_loader("deploy_script", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def snapshot(root: Path) -> dict:
    if not root.exists():
        return {}
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def manifest(target: Path) -> dict:
    return json.loads((target / MANIFEST).read_text())


def settings(target: Path) -> dict:
    return json.loads((target / "settings.json").read_text())


def test_fresh_install(pack, target):
    r = run(pack, target, "install")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (target / "agents" / "supervisor.md").read_text() == agent_md("supervisor")
    assert (target / "skills" / "demo" / "scripts" / "run.sh").is_file()
    assert not (target / "agents" / ".DS_Store").exists()
    assert not (target / "skills" / "demo" / "scripts" / "__pycache__").exists()
    m = manifest(target)
    assert m["version"] == 1
    assert set(m["files"]) == {"agents/supervisor.md", "agents/helper.md",
                               "skills/demo/SKILL.md", "skills/demo/scripts/run.sh"}
    assert m["settings"] == {"managed_agent_key": True, "previous_agent": None}
    assert m["source_commit"] is None and m["source_dirty"] is None  # the temp pack is not in a repo
    assert settings(target) == {"agent": "supervisor"}


def test_idempotent_rerun(pack, target):
    run(pack, target, "install")
    before = snapshot(target / "agents"), snapshot(target / "skills"), (target / "settings.json").read_text()
    r = run(pack, target, "install")
    assert r.returncode == 0
    assert "copied=0, updated=0, unchanged=4" in r.stdout
    assert before == (snapshot(target / "agents"), snapshot(target / "skills"),
                      (target / "settings.json").read_text())
    assert not list(target.glob("settings.json.bak-*"))


def test_source_update_propagates(pack, target):
    run(pack, target, "install")
    (pack / "agents" / "helper.md").write_text(agent_md("helper", "New body."))
    r = run(pack, target, "install")
    assert r.returncode == 0
    assert "New body." in (target / "agents" / "helper.md").read_text()
    assert "updated=1" in r.stdout


def test_local_modification_kept_then_overwritten(pack, target):
    run(pack, target, "install")
    dst = target / "agents" / "helper.md"
    dst.write_text("my edits")
    (pack / "agents" / "helper.md").write_text(agent_md("helper", "v2"))
    r = run(pack, target, "install")
    assert r.returncode == 0
    assert dst.read_text() == "my edits"
    assert "locally modified" in r.stdout
    r = run(pack, target, "install", "--overwrite-local", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "v2" in dst.read_text()
    baks = list(dst.parent.glob("helper.md.bak-*"))
    assert len(baks) == 1 and baks[0].read_text() == "my edits"


def test_unmanaged_collision(pack, target):
    (target / "agents").mkdir(parents=True)
    dst = target / "agents" / "helper.md"
    dst.write_text("someone else's agent")
    r = run(pack, target, "install")
    assert r.returncode != 0
    assert "not managed" in r.stdout
    assert dst.read_text() == "someone else's agent"
    assert (target / "agents" / "supervisor.md").exists()  # other files still installed
    assert "agents/helper.md" not in manifest(target)["files"]
    assert "run ./deploy install --overwrite-local from your checkout" in r.stdout
    r = run(pack, target, "install", "--overwrite-local", "--yes")
    assert r.returncode == 0, r.stdout
    assert dst.read_text() == agent_md("helper")
    assert list(dst.parent.glob("helper.md.bak-*"))


def test_file_removed_from_source(pack, target):
    run(pack, target, "install")
    (pack / "agents" / "helper.md").unlink()
    (pack / "skills" / "demo" / "scripts" / "run.sh").unlink()
    r = run(pack, target, "install")
    assert r.returncode == 0
    assert not (target / "agents" / "helper.md").exists()
    assert not (target / "skills" / "demo" / "scripts").exists()  # empty dir pruned
    assert (target / "skills" / "demo" / "SKILL.md").exists()
    assert "agents/helper.md" not in manifest(target)["files"]


def test_settings_other_keys_preserved(pack, target):
    target.mkdir()
    (target / "settings.json").write_text(json.dumps({"model": "opus", "env": {"A": "1"}, "zzz": [1]}))
    r = run(pack, target, "install")
    assert r.returncode == 0
    s = settings(target)
    assert s["agent"] == "supervisor"
    assert list(s) == ["model", "env", "zzz", "agent"]
    assert s["env"] == {"A": "1"}
    assert list(target.glob("settings.json.bak-*"))


def test_existing_agent_not_overwritten(pack, target):
    target.mkdir()
    (target / "settings.json").write_text(json.dumps({"agent": "mine"}))
    r = run(pack, target, "install")
    assert r.returncode == 0
    assert settings(target)["agent"] == "mine"
    assert "--force-default-agent" in r.stdout
    r = run(pack, target, "install", "--force-default-agent")
    assert settings(target)["agent"] == "supervisor"
    assert manifest(target)["settings"] == {"managed_agent_key": True, "previous_agent": "mine"}


def test_invalid_settings_json(pack, target):
    target.mkdir()
    (target / "settings.json").write_text("{not json")
    r = run(pack, target, "install")
    assert r.returncode != 0
    assert "cannot parse" in r.stdout
    assert (target / "settings.json").read_text() == "{not json"
    assert (target / "agents" / "supervisor.md").exists()


def test_no_default_agent(pack, target):
    r = run(pack, target, "install", "--no-default-agent")
    assert r.returncode == 0
    assert not (target / "settings.json").exists()
    assert manifest(target)["settings"]["managed_agent_key"] is False


def test_dry_run_writes_nothing(pack, target):
    r = run(pack, target, "install", "--dry-run")
    assert r.returncode == 0
    assert "would copy" in r.stdout
    assert not target.exists()
    run(pack, target, "install")
    (pack / "agents" / "helper.md").write_text(agent_md("helper", "v2"))
    before = snapshot(target)
    r = run(pack, target, "install", "--dry-run")
    assert "would update agents/helper.md" in r.stdout
    assert snapshot(target) == before


def test_uninstall_restores_previous_agent(pack, global_target):
    global_target.mkdir()
    (global_target / "settings.json").write_text(json.dumps({"agent": "mine", "x": 1}))
    run(pack, global_target, "install", "--force-default-agent")
    (global_target / "skills" / "demo" / "SKILL.md").write_text("edited")
    r = run(pack, global_target, "uninstall", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (global_target / "agents" / "supervisor.md").exists()
    assert not (global_target / "skills" / "demo" / "scripts").exists()
    assert (global_target / "skills" / "demo" / "SKILL.md").read_text() == "edited"  # modified kept
    assert "now unmanaged; delete it by hand" in r.stdout
    assert settings(global_target) == {"agent": "mine", "x": 1}
    assert not (global_target / MANIFEST).exists()


def test_uninstall_removes_agent_key(pack, global_target):
    run(pack, global_target, "install")
    r = run(pack, global_target, "uninstall", "--yes")
    assert r.returncode == 0
    assert settings(global_target) == {}
    assert not (global_target / "agents" / "helper.md").exists()


def test_uninstall_without_yes_and_no_tty_refuses(pack, target):
    run(pack, target, "install")
    r = run(pack, target, "uninstall")
    assert r.returncode == 2 and "cannot ask '" in r.stderr and "--yes" in r.stderr
    assert (target / "agents" / "helper.md").exists()


def test_invalid_frontmatter_aborts(pack, target):
    (pack / "agents" / "helper.md").write_text(agent_md("wrong-name"))
    r = run(pack, target, "install")
    assert r.returncode == 2
    assert "source validation failed" in r.stderr
    assert "Traceback" not in r.stderr
    assert not target.exists()


def test_symlink_in_source_rejected(pack, target):
    (pack / "skills" / "demo" / "link.md").symlink_to(pack / "skills" / "demo" / "SKILL.md")
    r = run(pack, target, "install")
    assert r.returncode == 2 and "symlink" in r.stderr
    assert not target.exists()


def test_lock_contention(pack, target):
    target.mkdir()
    with open(target / ".claude-supervisor.lock", "a") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        r = run(pack, target, "install")
    assert r.returncode == 2
    assert "lock" in r.stderr and "wait for it to finish" in r.stderr
    assert not (target / "agents").exists()


def test_status_reports_states(pack, target):
    run(pack, target, "install")
    (target / "agents" / "helper.md").write_text("edit")
    (target / "skills" / "demo" / "scripts" / "run.sh").unlink()
    r = run(pack, target, "status")
    assert r.returncode == 0
    assert "modified" in r.stdout and "missing" in r.stdout
    assert "Settings agent: 'supervisor'" in r.stdout


def test_help():
    r = subprocess.run([sys.executable, str(SCRIPT), "install", "--help"], capture_output=True, text=True)
    assert r.returncode == 0 and "--overwrite-local" in r.stdout and "--fable" not in r.stdout
    for flag in ("--tag", "--global", "--prefix", "--base-url", "--token", "--token-file"):
        assert flag in r.stdout, flag
    assert "--bin-dir" not in r.stdout


def test_symlinked_settings_survive_install(pack, target, tmp_path):
    target.mkdir()
    real = tmp_path / "dotfiles" / "settings.json"
    real.parent.mkdir()
    real.write_text(json.dumps({"model": "opus", "env": {"A": "1"}}))
    real.chmod(0o644)
    (target / "settings.json").symlink_to(real)
    r = run(pack, target, "install")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (target / "settings.json").is_symlink()
    assert json.loads(real.read_text()) == {"model": "opus", "env": {"A": "1"}, "agent": "supervisor"}
    assert real.stat().st_mode & 0o777 == 0o644
    assert not list(real.parent.glob(".tmp-*"))


@pytest.mark.parametrize("write_first", [True, False])
def test_settings_write_failure_keeps_manifest_consistent(pack, global_target, write_first, monkeypatch):
    monkeypatch.setenv("HOME", str(global_target.parent))
    deploy = load_deploy()
    real_save = deploy.save_settings

    def failing_save(tgt, data):
        if write_first:
            real_save(tgt, data)  # crash after the settings write, before anything else
        raise RuntimeError("simulated crash")

    deploy.save_settings = failing_save
    args = deploy.build_parser().parse_args(["install", "--global", "--source", str(pack)])
    with pytest.raises(RuntimeError):
        deploy.install_cmd(args)
    assert manifest(global_target)["settings"] == {"managed_agent_key": True, "previous_agent": None}
    r = run(pack, global_target, "uninstall", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    if (global_target / "settings.json").exists():
        assert "agent" not in settings(global_target)
    assert not (global_target / MANIFEST).exists()


@pytest.mark.parametrize("write_first", [True, False])
def test_release_write_failure_leaves_agent_revertible(pack, global_target, write_first, monkeypatch):
    assert run(pack, global_target, "install").returncode == 0
    monkeypatch.setenv("HOME", str(global_target.parent))
    deploy = load_deploy()
    real_save = deploy.save_settings

    def failing_save(tgt, data):
        if write_first:
            real_save(tgt, data)
        raise RuntimeError("simulated crash")

    deploy.save_settings = failing_save
    args = deploy.build_parser().parse_args(
        ["install", "--global", "--source", str(pack), "--no-default-agent"])
    with pytest.raises(RuntimeError):
        deploy.install_cmd(args)
    r = run(pack, global_target, "uninstall", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "agent" not in settings(global_target)


def test_non_utf8_source_file_exits_2(pack, target):
    (pack / "agents" / "helper.md").write_bytes(b"---\nname: helper\ndescription: \xff\xfe bad\n---\n")
    r = run(pack, target, "install")
    assert r.returncode == 2
    assert "helper.md" in r.stderr and "UTF-8" in r.stderr
    assert "Traceback" not in r.stderr
    assert not target.exists()


def test_status_reports_source_validation_error(pack, target):
    run(pack, target, "install")
    (pack / "agents" / "helper.md").write_text(agent_md("wrong-name"))
    r = run(pack, target, "status")
    assert r.returncode == 2
    assert "source validation failed" in r.stderr
    assert "removed from source" not in r.stdout


# --------------------------------------------------------------------------- fable

@pytest.fixture
def fable_pack(pack: Path) -> Path:
    (pack / "agents" / "planner.md").write_text(
        "---\nname: planner\ndescription: The planner agent.\nmodel: fable\neffort: xhigh\n---\n\n"
        "Dispatch `critic` (`model: fable`, domain `plan`).\nCritic runs on Fable.\n")
    return pack


def test_install_is_verbatim_for_fable_agents(fable_pack, target):
    r = run(fable_pack, target, "install")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Fable:" not in r.stdout
    assert "model: fable" in (target / "agents" / "planner.md").read_text()
    files = manifest(target)["files"]
    assert "agents/planner.md" in files and "fable" not in manifest(target)
    for key in files:
        assert (target / key).read_bytes() == (fable_pack / key).read_bytes()
    r = run(fable_pack, target, "status")
    assert "Fable:" not in r.stdout
    rows = [l for l in r.stdout.splitlines() if l.startswith("  ")]
    assert rows and all(l.endswith("ok") for l in rows)


def fable_stub(tmp_path: Path) -> dict:
    """A stub `claude` that prints the Fable model variable, then its args."""
    stub = tmp_path / "bin" / "claude"
    stub.parent.mkdir(exist_ok=True)
    stub.write_text("#!/bin/sh\nprintf '%s\\n' \"${ANTHROPIC_DEFAULT_FABLE_MODEL-unset}\" \"$@\"\n")
    stub.chmod(0o755)
    return {"PATH": "%s:/usr/bin:/bin" % (tmp_path / "bin"), "HOME": str(tmp_path)}


@pytest.mark.parametrize("args, caller, expect", [
    (["-p", "x"], {}, ["OPUS", "-p", "x"]),
    (["--fable", "-p", "x"], {}, ["unset", "-p", "x"]),
    (["--fable"], {}, ["unset"]),
    (["--fable", "-p", "x"], {"ANTHROPIC_DEFAULT_FABLE_MODEL": "mine"}, ["unset", "-p", "x"]),
    (["-p", "x"], {"ANTHROPIC_DEFAULT_FABLE_MODEL": "mine"}, ["OPUS", "-p", "x"]),
    (["x", "--fable"], {}, ["OPUS", "x", "--fable"]),
])
def test_launcher_fable_switch(pack, target, tmp_path, args, caller, expect, monkeypatch):
    assert run(pack, target, "install").returncode == 0
    _, launcher = sandbox_paths(tmp_path, "supervisor")
    monkeypatch.setenv("HOME", str(tmp_path))
    opus = load_deploy().OPUS_MODEL
    assert opus == "claude-opus-5-5"
    r = run_launcher(launcher, dict(fable_stub(tmp_path), **caller), *args)
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines() == [opus if e == "OPUS" else e for e in expect]


@pytest.mark.parametrize("dry", [[], ["--dry-run"]])
def test_global_install_notes_fable_variable(pack, global_target, dry):
    note = "set ANTHROPIC_DEFAULT_FABLE_MODEL to run fable agents on Opus"
    r = run(pack, global_target, "install", *dry)
    assert r.returncode == 0, r.stdout + r.stderr
    assert note in r.stdout


def test_sandbox_install_has_no_fable_note(pack, target):
    for dry in ([], ["--dry-run"]):
        r = run(pack, target, "install", *dry)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "ANTHROPIC_DEFAULT_FABLE_MODEL to run" not in r.stdout + r.stderr


# --------------------------------------------------------------------------- version

def version_file(pack: Path, text: str) -> None:
    (pack.parent / "VERSION").write_text(text)


def test_install_records_pack_version(pack, target):
    version_file(pack, "1.7\n")
    r = run(pack, target, "install")
    assert r.returncode == 0
    assert "Version: 1.7" in r.stdout
    assert manifest(target)["pack_version"] == "1.7"


def test_install_without_version_file(pack, target):
    r = run(pack, target, "install")
    assert r.returncode == 0
    assert "Version: unknown (no VERSION file in" in r.stdout
    assert manifest(target)["pack_version"] is None
    r = run(pack, target, "status")
    assert "Version: installed=not recorded, source=unknown" in r.stdout


def test_status_version_match_and_mismatch(pack, target):
    version_file(pack, "1.7\n")
    run(pack, target, "install")
    r = run(pack, target, "status")
    assert "Version: installed=1.7, source=1.7" in r.stdout
    assert "MISMATCH" not in r.stdout
    version_file(pack, "1.8\n")
    r = run(pack, target, "status")
    assert r.returncode == 0
    assert "Version: installed=1.7, source=1.8 (MISMATCH: run ./deploy install from your checkout)" in r.stdout
    r = run(pack, target, "install")
    assert "Version: 1.8 (was 1.7)" in r.stdout
    assert manifest(target)["pack_version"] == "1.8"


def test_status_old_manifest_without_pack_version(pack, target):
    version_file(pack, "1.7\n")
    run(pack, target, "install")
    m = manifest(target)
    del m["pack_version"]
    (target / MANIFEST).write_text(json.dumps(m))
    r = run(pack, target, "status")
    assert "Version: installed=not recorded, source=1.7" in r.stdout
    rows = [l for l in r.stdout.splitlines() if l.startswith("  ")]
    assert rows and all(l.endswith("ok") for l in rows)


# --------------------------------------------------------------------------- legacy migration

MIGRATION = ".claude-agents-manifest.json -> .claude-supervisor-manifest.json"


@pytest.fixture
def legacy_install(pack, global_target):
    """An install whose manifest and lock carry the pre-rebrand names."""
    assert run(pack, global_target, "install").returncode == 0
    (global_target / MANIFEST).rename(global_target / LEGACY_MANIFEST)
    (global_target / ".claude-agents.lock").write_text("")
    return global_target


def test_status_detects_legacy_install(pack, legacy_install):
    r = run(pack, legacy_install, "status")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "No manifest" not in r.stdout
    assert "legacy manifest .claude-agents-manifest.json" in r.stdout
    assert "run ./deploy install from your checkout to migrate" in r.stdout
    assert (legacy_install / LEGACY_MANIFEST).exists() and not (legacy_install / MANIFEST).exists()


def test_install_migrates_legacy_manifest(pack, legacy_install):
    before = json.loads((legacy_install / LEGACY_MANIFEST).read_text())
    r = run(pack, legacy_install, "install")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "migrated " + MIGRATION in r.stdout
    assert "not managed" not in r.stdout and "copied=0, updated=0, unchanged=4" in r.stdout
    assert (legacy_install / MANIFEST).exists()
    assert not (legacy_install / LEGACY_MANIFEST).exists()
    assert not (legacy_install / ".claude-agents.lock").exists()
    after = manifest(legacy_install)
    assert after["settings"] == before["settings"]
    assert "fable" not in after


def test_install_dry_run_does_not_migrate(pack, legacy_install):
    r = run(pack, legacy_install, "install", "--dry-run")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "would migrate " + MIGRATION in r.stdout
    assert (legacy_install / LEGACY_MANIFEST).exists() and not (legacy_install / MANIFEST).exists()
    assert (legacy_install / ".claude-agents.lock").exists()


def test_uninstall_removes_legacy_install(pack, legacy_install):
    r = run(pack, legacy_install, "uninstall", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (legacy_install / "agents" / "helper.md").exists()
    assert not (legacy_install / "skills" / "demo" / "SKILL.md").exists()
    for name in (MANIFEST, LEGACY_MANIFEST, ".claude-supervisor.lock", ".claude-agents.lock"):
        assert not (legacy_install / name).exists(), name


def test_install_warns_when_both_manifests_exist(pack, legacy_install):
    (legacy_install / MANIFEST).write_text((legacy_install / LEGACY_MANIFEST).read_text())
    r = run(pack, legacy_install, "install")
    assert r.returncode == 0, r.stdout + r.stderr
    assert ("WARNING: both .claude-agents-manifest.json and .claude-supervisor-manifest.json exist; "
            "using .claude-supervisor-manifest.json") in r.stdout
    assert (legacy_install / LEGACY_MANIFEST).exists()


# --------------------------------------------------------------------------- sandbox

def claude_stub(tmp_path: Path) -> dict:
    """A stub `claude` that echoes its env and args; returns the env for running a launcher."""
    stub = tmp_path / "bin" / "claude"
    stub.parent.mkdir(exist_ok=True)
    stub.write_text("#!/bin/sh\n"
                    "printf '%s\\n' \"$CLAUDE_CONFIG_DIR\" \"$ANTHROPIC_BASE_URL\" "
                    "\"$ANTHROPIC_AUTH_TOKEN\" \"$@\"\n")
    stub.chmod(0o755)
    return {"PATH": "%s:/usr/bin:/bin" % (tmp_path / "bin")}


def run_launcher(launcher: Path, env: dict, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(launcher)] + list(args), capture_output=True, text=True, env=env,
                          timeout=60, stdin=subprocess.DEVNULL)


def sandbox_paths(tmp_path: Path, tag: str):
    return ((tmp_path / ".config" / ("claude-" + tag)).resolve(),
            (tmp_path / ".local" / "bin" / ("claude-" + tag)).resolve())


@pytest.mark.parametrize("extra, tag", [([], "supervisor"), (["--tag", "t"], "t")])
def test_sandbox_round_trip(pack, target, tmp_path, extra, tag):
    sbx, launcher = sandbox_paths(tmp_path, tag)
    r = run(pack, target, "install", "--dry-run", target_args=extra)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not sbx.exists() and not launcher.exists()

    r = run(pack, target, "install", target_args=extra)
    assert r.returncode == 0, r.stdout + r.stderr
    assert manifest(sbx)["launcher"] == str(launcher)
    assert os.access(launcher, os.X_OK)
    text = launcher.read_text()
    assert text.splitlines()[1].startswith(LAUNCHER_MARKER)
    assert "CLAUDE_CONFIG_DIR='%s'" % sbx in text
    assert "ANTHROPIC_BASE_URL" not in text and "ANTHROPIC_AUTH_TOKEN" not in text
    assert "Seed" not in r.stdout

    env = dict(claude_stub(tmp_path), HOME=str(tmp_path))
    r = run_launcher(launcher, env, "a b", "--", "")
    assert r.returncode == 0, r.stderr
    assert r.stdout == "%s\n\n\na b\n--\n\n" % sbx
    # only a leading update/uninstall is the launcher's own
    r = run_launcher(launcher, env, "--help", "updates", "x", "update", "uninstall")
    assert r.returncode == 0, r.stderr
    assert r.stdout == "%s\n\n\n--help\nupdates\nx\nupdate\nuninstall\n" % sbx

    r = run(pack, target, "status", target_args=extra)
    assert "Target: %s" % sbx in r.stdout
    assert "Launcher: %s" % launcher in r.stdout
    assert "Settings agent: 'supervisor' (managed)" in r.stdout

    r = run(pack, target, "uninstall", "--yes", target_args=extra)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not sbx.exists() and not launcher.exists()


def test_sandbox_token_provider(pack, target, tmp_path):
    sbx, launcher = sandbox_paths(tmp_path, "t")
    r = run(pack, target, "install", "--base-url", "https://llm.example", "--token", "s3cret",
            target_args=["--tag", "t"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert (sbx / "token").read_text() == "s3cret"
    assert (sbx / "token").stat().st_mode & 0o777 == 0o600
    assert sbx.stat().st_mode & 0o777 == 0o700
    text = launcher.read_text()
    assert "ANTHROPIC_BASE_URL='https://llm.example'; export ANTHROPIC_BASE_URL" in text
    assert "ANTHROPIC_AUTH_TOKEN=\"$(cat '%s/token')\"; export ANTHROPIC_AUTH_TOKEN" % sbx in text
    status = run(pack, target, "status", target_args=["--tag", "t"])
    for seen in (r.stdout, r.stderr, (sbx / MANIFEST).read_text(), (sbx / "settings.json").read_text(),
                 status.stdout, status.stderr):
        assert "s3cret" not in seen

    r = run_launcher(launcher, claude_stub(tmp_path))
    assert r.stdout == "%s\nhttps://llm.example\ns3cret\n" % sbx

    assert run(pack, target, "install", target_args=["--tag", "t"]).returncode == 0
    assert launcher.read_text() == text

    tok = tmp_path / "tok"
    tok.write_bytes(b"f1le\n")
    r = run(pack, target, "install", "--token-file", str(tok), target_args=["--tag", "u"])
    assert r.returncode == 0, r.stdout + r.stderr
    sbx_u, launcher_u = sandbox_paths(tmp_path, "u")
    assert (sbx_u / "token").read_bytes() == b"f1le\n"
    assert (sbx_u / "token").stat().st_mode & 0o777 == 0o600
    text_u = launcher_u.read_text()
    assert "ANTHROPIC_AUTH_TOKEN=" in text_u and "ANTHROPIC_BASE_URL" not in text_u


def test_global_round_trip(pack, global_target, tmp_path):
    r = run(pack, global_target, "install")
    assert r.returncode == 0, r.stdout + r.stderr
    assert manifest(global_target)["launcher"] is None
    assert not (tmp_path / ".local" / "bin").exists() and not (tmp_path / ".config").exists()
    assert "is not on your PATH" not in r.stdout  # no launcher, so no PATH hint

    r = run(pack, global_target, "status")
    assert "Settings agent: 'supervisor' (managed)" in r.stdout

    (global_target / "mine.txt").write_text("mine")
    r = run(pack, global_target, "uninstall", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (global_target / "agents" / "helper.md").exists()
    assert not (global_target / MANIFEST).exists()
    assert (global_target / "mine.txt").read_text() == "mine"


def test_sandbox_seeds_from_global_once(pack, global_target, target, tmp_path):
    assert run(pack, global_target, "install").returncode == 0
    (global_target / "settings.json").write_text(json.dumps({"agent": "supervisor", "theme": "dark"}))
    for rel in ("CLAUDE.md", "agents/mine.md", "commands/c.md",
                "agents/mine.md.bak-1", "skills/synced/x.md", "skills/.trash/y.md",
                "plugins/p.json", "history.jsonl"):
        (global_target / rel).parent.mkdir(parents=True, exist_ok=True)
        (global_target / rel).write_text("global v1")
    (global_target / "agents" / "helper.md").write_text("global edit")
    sbx, _ = sandbox_paths(tmp_path, "t")

    r = run(pack, target, "install", target_args=["--tag", "t"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "not managed" not in r.stdout + r.stderr
    for rel in ("CLAUDE.md", "agents/mine.md", "commands/c.md"):
        assert (sbx / rel).read_text() == "global v1", rel
    for rel in ("agents/mine.md.bak-1", "skills/synced/x.md", "skills/.trash/y.md",
                "plugins/p.json", "history.jsonl"):
        assert not (sbx / rel).exists(), rel
    assert settings(sbx) == {"theme": "dark", "agent": "supervisor"}
    assert manifest(sbx)["settings"]["managed_agent_key"] is True

    (global_target / "CLAUDE.md").write_text("global v2")
    assert run(pack, target, "install", target_args=["--tag", "t"]).returncode == 0
    assert (sbx / "CLAUDE.md").read_text() == "global v1"


def test_tag_with_target_dir(pack, target, tmp_path):
    box = tmp_path / "box"
    _, launcher = sandbox_paths(tmp_path, "work")
    args = ["--tag", "work", "--target", str(box)]
    r = run(pack, target, "install", target_args=args)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "CLAUDE_CONFIG_DIR='%s'" % box.resolve() in launcher.read_text()
    m = manifest(box)
    assert m["tag"] == "work" and m["launcher"] == str(launcher)
    r = run(pack, target, "status", target_args=["--target", str(box)])
    assert "Launcher: %s" % launcher in r.stdout
    r = run(pack, target, "uninstall", "--yes", target_args=["--target", str(box)])
    assert r.returncode == 0, r.stdout + r.stderr
    assert not box.exists() and not launcher.exists()


def test_sandbox_refusals(pack, target, global_target, tmp_path):
    def check(r, *msgs):
        assert r.returncode == 2, r.stdout + r.stderr
        for msg in msgs:
            assert msg in r.stderr, r.stderr
        assert not (tmp_path / ".config").exists() and not global_target.exists()

    check(run(pack, target, "install", target_args=["--tag", "a/b"]), "invalid tag")
    check(run(pack, target, "install", target_args=["--tag", ""]), "invalid tag")
    for flag, value in (("--tag", "t"), ("--target", "d"), ("--base-url", "u"),
                        ("--token", "x"), ("--token-file", "f")):
        check(run(pack, global_target, "install", flag, value),
              "--global cannot be combined with " + flag)
    check(run(pack, global_target, "status", "--tag", "t"), "--global cannot be combined with --tag")
    check(run(pack, target, "install", "--token", "x", "--token-file", "y", target_args=["--tag", "t"]))
    check(run(pack, target, "install", target_args=["--target", str(tmp_path / ".claude")]),
          "use --global")

    bin_dir = tmp_path / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "claude-t").write_text("#!/bin/sh\necho mine\n")
    check(run(pack, target, "install", target_args=["--tag", "t"]),
          "is not a claude-supervisor launcher", "move it aside, or choose another --tag or --prefix")
    assert (bin_dir / "claude-t").read_text() == "#!/bin/sh\necho mine\n"
    (bin_dir / "claude-u").mkdir()
    check(run(pack, target, "install", target_args=["--tag", "u"]),
          "is not a claude-supervisor launcher", "move it aside, or choose another --tag or --prefix")


def test_prefix_launcher_recorded_for_uninstall(pack, target, tmp_path):
    px = tmp_path / "px"
    r = run(pack, target, "install", target_args=["--tag", "t", "--prefix", str(px)])
    assert r.returncode == 0, r.stdout + r.stderr
    assert (px / "bin" / "claude-t").is_file()
    assert not (tmp_path / ".local").exists()
    r = run(pack, target, "uninstall", "--yes", target_args=["--tag", "t", "--prefix", str(px)])
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (px / "bin" / "claude-t").exists()


def test_sandbox_uninstall_without_manifest_keeps_dir(pack, target, tmp_path):
    keep = tmp_path / ".config" / "claude-t" / "keep"
    keep.parent.mkdir(parents=True)
    keep.write_text("x")
    r = run(pack, target, "uninstall", "--yes", target_args=["--tag", "t"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert keep.read_text() == "x"
    assert "nothing to uninstall" in r.stdout and "The directory still exists" in r.stdout


# --------------------------------------------------------------------------- registry and update

def state_dir(tmp_path: Path, prefix: Path = None) -> Path:
    return (prefix or tmp_path / ".local") / "state" / "claude-supervisor"


def registry(tmp_path: Path, prefix: Path = None) -> dict:
    return json.loads((state_dir(tmp_path, prefix) / "installs.json").read_text())["installs"]


def entry(tag, remote=None, branch="main") -> dict:
    return {"tag": tag, "remote": remote, "branch": branch}


def test_install_records_registry_and_tool_copy(pack, target, tmp_path):
    sbx, _ = sandbox_paths(tmp_path, "t")
    r = run(pack, target, "install", target_args=["--tag", "t"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert registry(tmp_path) == {str(sbx): entry("t")}
    copy = state_dir(tmp_path) / "deploy"
    assert copy.read_bytes() == SCRIPT.read_bytes()
    assert os.access(copy, os.X_OK)

    # a reinstall refreshes both
    reg = state_dir(tmp_path) / "installs.json"
    reg.write_text(json.dumps({"version": 1, "installs": {str(sbx): {"tag": "t", "remote": "stale"}}}))
    copy.write_bytes(b"old")
    r = run(pack, target, "install", target_args=["--tag", "t"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert registry(tmp_path) == {str(sbx): entry("t")}
    assert copy.read_bytes() == SCRIPT.read_bytes() and os.access(copy, os.X_OK)


def test_uninstall_removes_registry_entries(pack, target, global_target, tmp_path):
    sbx, _ = sandbox_paths(tmp_path, "t")
    assert run(pack, target, "install", target_args=["--tag", "t"]).returncode == 0
    assert run(pack, global_target, "install").returncode == 0
    assert registry(tmp_path) == {str(sbx): entry("t"),
                                  str(global_target.resolve()): entry(None)}
    assert run(pack, target, "uninstall", "--yes", target_args=["--tag", "t"]).returncode == 0
    assert registry(tmp_path) == {str(global_target.resolve()): entry(None)}
    assert run(pack, global_target, "uninstall", "--yes").returncode == 0
    assert registry(tmp_path) == {}


@pytest.mark.parametrize("use_global", [False, True])
def test_dry_run_install_skips_registry_and_copy(pack, target, global_target, tmp_path, use_global):
    state = tmp_path / ".local" / "state"
    tgt, args = (global_target, None) if use_global else (target, ["--tag", "t"])
    r = run(pack, tgt, "install", "--dry-run", target_args=args)
    assert r.returncode == 0, r.stdout + r.stderr
    assert snapshot(state) == {} and not state.exists()
    assert run(pack, tgt, "install", target_args=args).returncode == 0
    before = snapshot(state)
    assert set(before) == {"claude-supervisor/installs.json", "claude-supervisor/deploy"}
    (pack / "agents" / "helper.md").write_text(agent_md("helper", "v2"))
    assert run(pack, tgt, "install", "--dry-run", target_args=args).returncode == 0
    assert snapshot(state) == before


def test_update_and_uninstall_selection_errors(pack, target, tmp_path):
    assert run(pack, target, "install", target_args=["--tag", "t"]).returncode == 0
    r = run(pack, target, "update", "--yes", target_args=["--tag", "t"])
    assert r.returncode == 1, r.stdout + r.stderr
    assert "no recorded remote; run ./deploy install from your checkout, or pass --from" in r.stdout + r.stderr
    r = run(pack, target, "update", "--yes", target_args=["--all"])
    assert r.returncode == 1, r.stdout + r.stderr
    assert "no recorded remote" in r.stdout + r.stderr

    r = run(pack, target, "update", "--yes", target_args=["--tag", "never"])
    assert r.returncode == 2
    assert "is not registered under prefix" in r.stderr and "run ./deploy install once" in r.stderr

    for cmd in ("update", "uninstall"):
        for extra in (["--tag", "t"], ["--target", str(target)], ["--global"]):
            r = run(pack, target, cmd, "--yes", target_args=["--all"] + extra)
            assert r.returncode == 2, (cmd, extra, r.stdout + r.stderr)
            assert "--all cannot be combined with --tag, --target or --global" in r.stderr
    assert list(registry(tmp_path)) == [str(sandbox_paths(tmp_path, "t")[0])]


def test_prefixes_are_independent(pack, target, tmp_path):
    pa, pb = tmp_path / "pa", tmp_path / "pb"
    sbx_a, _ = sandbox_paths(tmp_path, "a")
    sbx_b, _ = sandbox_paths(tmp_path, "b")
    for tag, px in (("a", pa), ("b", pb)):
        r = run(pack, target, "install", target_args=["--tag", tag, "--prefix", str(px)])
        assert r.returncode == 0, r.stdout + r.stderr
        assert (px / "bin" / ("claude-" + tag)).is_file()
        assert (state_dir(tmp_path, px) / "deploy").read_bytes() == SCRIPT.read_bytes()
        assert manifest(sandbox_paths(tmp_path, tag)[0])["prefix"] == str(px.resolve())
    assert registry(tmp_path, pa) == {str(sbx_a): entry("a")}
    assert registry(tmp_path, pb) == {str(sbx_b): entry("b")}
    assert not (tmp_path / ".local").exists()

    r = run(pack, target, "update", "--yes", target_args=["--all", "--prefix", str(pa)])
    assert r.returncode == 1 and str(sbx_a) in r.stdout + r.stderr
    assert str(sbx_b) not in r.stdout + r.stderr

    before_b = snapshot(pb)
    r = run(pack, target, "uninstall", "--yes", target_args=["--all", "--prefix", str(pa)])
    assert r.returncode == 0, r.stdout + r.stderr
    assert not sbx_a.exists() and not (pa / "bin" / "claude-a").exists()
    assert registry(tmp_path, pa) == {}
    assert (sbx_b / MANIFEST).is_file() and (pb / "bin" / "claude-b").is_file()
    assert registry(tmp_path, pb) == {str(sbx_b): entry("b")}
    assert snapshot(pb) == before_b


def test_prefix_mismatch_refuses(pack, target, tmp_path):
    pa, pb = tmp_path / "pa", tmp_path / "pb"
    args = ["--tag", "t", "--prefix", str(pa)]
    assert run(pack, target, "install", target_args=args).returncode == 0
    before = snapshot(tmp_path)
    for cmd in (["install"], ["install", "--dry-run"], ["uninstall", "--yes"]):
        r = run(pack, target, *cmd, target_args=["--tag", "t", "--prefix", str(pb)])
        assert r.returncode == 2, (cmd, r.stdout + r.stderr)
        assert "was installed with --prefix" in r.stderr and str(pa.resolve()) in r.stderr
        assert snapshot(tmp_path) == before and not pb.exists()
    # the default prefix is another prefix too
    r = run(pack, target, "install", target_args=["--tag", "t"])
    assert r.returncode == 2 and "was installed with --prefix" in r.stderr
    assert snapshot(tmp_path) == before
    assert run(pack, target, "install", target_args=args).returncode == 0


def test_manifest_without_prefix_counts_as_default(pack, target, tmp_path):
    sbx, _ = sandbox_paths(tmp_path, "t")
    default = str((tmp_path / ".local").resolve())

    def strip_prefix():
        m = manifest(sbx)
        del m["prefix"]
        (sbx / MANIFEST).write_text(json.dumps(m))

    assert run(pack, target, "install", target_args=["--tag", "t"]).returncode == 0
    assert manifest(sbx)["prefix"] == default
    strip_prefix()
    r = run(pack, target, "install", target_args=["--tag", "t"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert manifest(sbx)["prefix"] == default

    strip_prefix()
    before = snapshot(tmp_path)
    r = run(pack, target, "install", target_args=["--tag", "t", "--prefix", str(tmp_path / "px")])
    assert r.returncode == 2 and "was installed with --prefix" in r.stderr
    assert snapshot(tmp_path) == before


# update from a file:// remote

@pytest.fixture
def remote(tmp_path: Path) -> SimpleNamespace:
    """A bare repo (branch main: deploy, VERSION, a small pack) plus an install clone of it."""
    git_bin = shutil.which("git")
    if git_bin is None:
        pytest.skip("git not available")
    tmpdir = tmp_path / "tmpdir"
    tmpdir.mkdir()
    env = {"HOME": str(tmp_path), "PATH": "%s:/usr/bin:/bin" % Path(git_bin).parent,
           "TMPDIR": str(tmpdir), "GIT_CONFIG_NOSYSTEM": "1"}
    bare, work, clone = tmp_path / "remote.git", tmp_path / "work", tmp_path / "clone"
    (work / "pack" / "agents").mkdir(parents=True)
    (work / "pack" / "skills" / "demo").mkdir(parents=True)
    (work / "pack" / "agents" / "supervisor.md").write_text(agent_md("supervisor"))
    (work / "pack" / "agents" / "helper.md").write_text(agent_md("helper", "v1"))
    (work / "pack" / "skills" / "demo" / "SKILL.md").write_text(
        "---\nname: demo\ndescription: Demo skill.\n---\n\nUse it.\n")
    (work / "deploy").write_bytes(SCRIPT.read_bytes())
    (work / "VERSION").write_text("1.0\n")
    ns = SimpleNamespace(url="file://%s" % bare, bare=bare, work=work, clone=clone, env=env,
                         tmpdir=tmpdir, state=state_dir(tmp_path))

    def git(cwd: Path, *args: str) -> None:
        r = subprocess.run([git_bin, "-c", "user.name=t", "-c", "user.email=t@t"] + list(args),
                           cwd=str(cwd), env=env, capture_output=True, text=True, timeout=60,
                           stdin=subprocess.DEVNULL)
        assert r.returncode == 0, "git %s: %s" % (args, r.stderr)

    ns.git = git
    git(tmp_path, "init", "--bare", "-q", str(bare))
    git(work, "init", "-q")
    git(work, "remote", "add", "origin", ns.url)
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "init")
    git(work, "push", "-q", "origin", "HEAD:main")
    git(tmp_path, "clone", "-q", "--branch", "main", ns.url, str(clone))
    return ns


def deploy_run(remote: SimpleNamespace, script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script)] + list(args), capture_output=True, text=True,
                          env=remote.env, timeout=120, stdin=subprocess.DEVNULL)


def install_from_clone(remote: SimpleNamespace, *args: str) -> None:
    r = deploy_run(remote, remote.clone / "deploy", "install", *args)
    assert r.returncode == 0, r.stdout + r.stderr


def update(remote: SimpleNamespace, *args: str) -> subprocess.CompletedProcess:
    return deploy_run(remote, remote.state / "deploy", "update", *args)


def push_change(remote: SimpleNamespace, body: str) -> None:
    """Push a pack change from the work tree, then delete the install clone."""
    (remote.work / "pack" / "agents" / "helper.md").write_text(agent_md("helper", body))
    remote.git(remote.work, "add", "-A")
    remote.git(remote.work, "commit", "-q", "-m", body)
    remote.git(remote.work, "push", "-q", "origin", "HEAD:main")
    shutil.rmtree(remote.clone)


def helper_text(target: Path) -> str:
    return (target / "agents" / "helper.md").read_text()


def test_update_from_remote_replays_options(remote, tmp_path):
    px = tmp_path / "px"
    sbx, _ = sandbox_paths(tmp_path, "t")
    launcher = px / "bin" / "claude-t"
    install_from_clone(remote, "--tag", "t", "--prefix", str(px), "--no-default-agent",
                       "--base-url", "https://llm.example")
    assert registry(tmp_path, px) == {str(sbx): entry("t", remote.url)}
    assert "v1" in helper_text(sbx)
    legacy = json.loads((sbx / MANIFEST).read_text())
    legacy["fable"] = True  # a manifest written before the launcher took over the switch
    (sbx / MANIFEST).write_text(json.dumps(legacy))
    push_change(remote, "v2 pushed")

    r = deploy_run(remote, state_dir(tmp_path, px) / "deploy", "update", "--prefix", str(px),
                   "--tag", "t", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "v2 pushed" in helper_text(sbx)
    assert launcher.is_file()
    assert not (tmp_path / ".local").exists()
    assert not (sbx / "settings.json").exists() or "agent" not in settings(sbx)
    m = manifest(sbx)
    assert "fable" not in m and m["base_url"] == "https://llm.example"
    assert m["settings"]["managed_agent_key"] is False
    assert m["launcher"] == str(launcher) and m["prefix"] == str(px.resolve())
    assert "ANTHROPIC_BASE_URL='https://llm.example'" in launcher.read_text()
    assert list(remote.tmpdir.iterdir()) == []
    assert registry(tmp_path, px) == {str(sbx): entry("t", remote.url)}


@pytest.fixture
def three(remote, tmp_path) -> list:
    """Two sandboxes and a global install, all from the same remote."""
    for args in (["--tag", "t"], ["--tag", "u"], ["--global"]):
        install_from_clone(remote, *args)
    targets = [sandbox_paths(tmp_path, "t")[0], sandbox_paths(tmp_path, "u")[0],
               (tmp_path / ".claude").resolve()]
    assert set(registry(tmp_path)) == set(map(str, targets))
    assert {e["remote"] for e in registry(tmp_path).values()} == {remote.url}
    return targets


def test_update_all(remote, three):
    push_change(remote, "v3 all")
    r = update(remote, "--all", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    for t in three:
        assert "v3 all" in helper_text(t), t
    assert list(remote.tmpdir.iterdir()) == []


def test_uninstall_all(remote, three, tmp_path):
    r = deploy_run(remote, remote.state / "deploy", "uninstall", "--all", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    for t in three:
        assert not (t / MANIFEST).exists() and not (t / "agents" / "helper.md").exists(), t
        assert "== uninstall %s ==" % t in r.stdout
    assert not three[0].exists() and not three[1].exists()
    assert registry(tmp_path) == {}


@pytest.mark.parametrize("cmd", ["update", "uninstall"])
def test_all_without_yes_and_no_tty_refuses(remote, three, tmp_path, cmd):
    push_change(remote, "v4 unseen")
    roots = [tmp_path / ".config", tmp_path / ".claude", tmp_path / ".local"]
    before = [snapshot(p) for p in roots]
    r = deploy_run(remote, remote.state / "deploy", cmd, "--all")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "--yes" in r.stderr
    assert [snapshot(p) for p in roots] == before
    assert len(registry(tmp_path)) == 3


def test_stale_entry_skipped_by_update_and_pruned_by_uninstall(remote, three, tmp_path):
    t, u, _ = three
    shutil.rmtree(u)  # registered, but no manifest any more
    push_change(remote, "v5 stale")

    r = update(remote, "--all", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "SKIP %s: no manifest" % u in r.stdout
    assert "v5 stale" in helper_text(t) and "v5 stale" in helper_text(three[2])
    assert not u.exists()
    assert str(u) in registry(tmp_path)

    r = deploy_run(remote, remote.state / "deploy", "uninstall", "--all", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Removed stale registry entry for %s" % u in r.stdout
    assert registry(tmp_path) == {}
    assert not t.exists() and not u.exists()


# launcher update and uninstall

def launcher_env(remote: SimpleNamespace, tmp_path: Path, stub_exit: int = 0) -> dict:
    """Env for a launcher run: fake HOME, stub `claude` first on PATH (never the real one), git on PATH."""
    claude_stub(tmp_path)
    env = dict(remote.env, PATH="%s:%s" % (tmp_path / "bin", remote.env["PATH"]))
    if stub_exit:
        stub = tmp_path / "bin" / "claude"
        stub.write_text(stub.read_text() + "exit %d\n" % stub_exit)
    return env


def claude_launcher(tmp_path: Path, tag: str) -> Path:
    return tmp_path / ".local" / "bin" / ("claude-" + tag)


def test_launcher_update_yes(remote, tmp_path):
    install_from_clone(remote, "--tag", "t")
    sbx, _ = sandbox_paths(tmp_path, "t")
    push_change(remote, "v6 launcher")
    r = run_launcher(claude_launcher(tmp_path, "t"), launcher_env(remote, tmp_path), "update", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "== claude update ==" in r.stdout and "\n\n\nupdate\n" in r.stdout
    assert "v6 launcher" in helper_text(sbx)
    assert list(remote.tmpdir.iterdir()) == []


def test_launcher_update_survives_claude_update_failure(remote, tmp_path):
    install_from_clone(remote, "--tag", "t")
    sbx, _ = sandbox_paths(tmp_path, "t")
    push_change(remote, "v7 despite")
    r = run_launcher(claude_launcher(tmp_path, "t"), launcher_env(remote, tmp_path, stub_exit=3),
                     "update", "--yes")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "ERROR claude update failed (exit 3); updating the pack anyway" in r.stdout + r.stderr
    assert "v7 despite" in helper_text(sbx)


def test_launcher_uninstall_yes(remote, tmp_path):
    for tag in ("t", "u"):
        install_from_clone(remote, "--tag", tag)
    (t, _), (u, _) = sandbox_paths(tmp_path, "t"), sandbox_paths(tmp_path, "u")
    r = run_launcher(claude_launcher(tmp_path, "t"), launcher_env(remote, tmp_path), "uninstall", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not t.exists() and not claude_launcher(tmp_path, "t").exists()
    assert list(registry(tmp_path)) == [str(u)]
    assert (u / MANIFEST).is_file() and claude_launcher(tmp_path, "u").is_file()
    assert (remote.state / "deploy").is_file()


def test_launcher_update_all_yes(remote, three, tmp_path):
    push_change(remote, "v8 all")
    r = run_launcher(claude_launcher(tmp_path, "t"), launcher_env(remote, tmp_path),
                     "update", "--all", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    for t in three:
        assert "v8 all" in helper_text(t), t
    assert list(remote.tmpdir.iterdir()) == []


def test_launcher_uninstall_all_refused(remote, three, tmp_path):
    roots = [tmp_path / ".config", tmp_path / ".claude", tmp_path / ".local"]
    before = [snapshot(p) for p in roots]
    for extra in ([], ["--yes"]):
        r = run_launcher(claude_launcher(tmp_path, "t"), launcher_env(remote, tmp_path),
                         "uninstall", "--all", *extra)
        assert r.returncode == 2, r.stdout + r.stderr
        assert "use ./deploy uninstall --all" in r.stderr
        assert [snapshot(p) for p in roots] == before
        assert len(registry(tmp_path)) == 3


@pytest.mark.parametrize("cmd", ["update", "uninstall"])
def test_launcher_without_yes_and_no_tty_refuses(remote, three, tmp_path, cmd):
    push_change(remote, "v9 unseen")
    roots = [tmp_path / ".config", tmp_path / ".claude", tmp_path / ".local"]
    before = [snapshot(p) for p in roots]
    r = run_launcher(claude_launcher(tmp_path, "t"), launcher_env(remote, tmp_path), cmd)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "--yes" in r.stderr and "update" not in r.stdout.splitlines()
    assert [snapshot(p) for p in roots] == before
    assert len(registry(tmp_path)) == 3


def test_launcher_missing_tool_copy(remote, tmp_path):
    install_from_clone(remote, "--tag", "t")
    (remote.state / "deploy").unlink()
    before = snapshot(tmp_path / ".config")
    r = run_launcher(claude_launcher(tmp_path, "t"), launcher_env(remote, tmp_path), "update", "--yes")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "missing; run ./deploy install from your checkout" in r.stderr
    assert "update" not in r.stdout.splitlines()
    assert snapshot(tmp_path / ".config") == before


@pytest.mark.parametrize("cmd", ["update", "uninstall"])
def test_launcher_ignores_user_selection(remote, tmp_path, cmd):
    for tag in ("t", "other"):
        install_from_clone(remote, "--tag", tag)
    (t, _), (other, _) = sandbox_paths(tmp_path, "t"), sandbox_paths(tmp_path, "other")
    push_change(remote, "v10 own")
    before = snapshot(other)
    r = run_launcher(claude_launcher(tmp_path, "t"), launcher_env(remote, tmp_path),
                     cmd, "--tag", "other", "--target", str(other), "--prefix", str(tmp_path / "px"), "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert snapshot(other) == before and claude_launcher(tmp_path, "other").is_file()
    assert str(other) in registry(tmp_path) and not (tmp_path / "px").exists()
    if cmd == "update":
        assert "v10 own" in helper_text(t)
    else:
        assert not t.exists() and str(t) not in registry(tmp_path)


# branches: install records one, update follows it

def push_feat(remote: SimpleNamespace, body: str, create: bool = False) -> None:
    """Commit a pack change on branch feat in the work tree and push it; work returns to its own branch."""
    remote.git(remote.work, "checkout", "-q", *(["-b"] if create else []), "feat")
    (remote.work / "pack" / "agents" / "helper.md").write_text(agent_md("helper", body))
    remote.git(remote.work, "add", "-A")
    remote.git(remote.work, "commit", "-q", "-m", body)
    remote.git(remote.work, "push", "-q", "origin", "feat")
    remote.git(remote.work, "checkout", "-q", "-")


@pytest.fixture
def feat_tree(remote, tmp_path) -> Path:
    """A worktree of the install clone on branch feat, which exists on the remote (the dev workflow)."""
    push_feat(remote, "feat v1", create=True)
    remote.git(remote.clone, "fetch", "-q", "origin")
    tree = tmp_path / "feat-tree"
    remote.git(remote.clone, "worktree", "add", "-q", "-b", "feat", str(tree), "origin/feat")
    return tree


def install_dev(remote: SimpleNamespace, tree: Path, tmp_path: Path) -> Path:
    r = deploy_run(remote, tree / "deploy", "install", "--tag", "dev")
    assert r.returncode == 0, r.stdout + r.stderr
    return sandbox_paths(tmp_path, "dev")[0]


def stale_line(sbx: Path, remote_url: str, branch: str = "feat", tag: str = "dev") -> str:
    return ("STALE %s: nothing to update; branch %s is gone from %s; this install is stale. "
            "Remove it with: claude-%s uninstall (or ./deploy uninstall --tag %s --target %s)"
            % (sbx, branch, remote_url, tag, tag, sbx))


def test_install_records_checkout_branch(remote, feat_tree, tmp_path):
    dev = install_dev(remote, feat_tree, tmp_path)
    install_from_clone(remote, "--tag", "t")
    assert "feat v1" in helper_text(dev)
    assert registry(tmp_path) == {str(dev): entry("dev", remote.url, "feat"),
                                  str(sandbox_paths(tmp_path, "t")[0]): entry("t", remote.url)}


def test_branch_shadowed_by_tag_records_plain_name(remote, feat_tree, tmp_path):
    remote.git(feat_tree, "tag", "feat")  # makes `symbolic-ref --short HEAD` print heads/feat
    dev = install_dev(remote, feat_tree, tmp_path)
    assert registry(tmp_path)[str(dev)] == entry("dev", remote.url, "feat")


def test_install_on_detached_head_records_main(remote, tmp_path):
    remote.git(remote.clone, "checkout", "-q", "--detach")
    r = deploy_run(remote, remote.clone / "deploy", "install", "--tag", "t")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "is on a detached HEAD; recording branch main for update" in r.stdout + r.stderr
    assert registry(tmp_path) == {str(sandbox_paths(tmp_path, "t")[0]): entry("t", remote.url)}


def test_update_follows_recorded_branch(remote, feat_tree, tmp_path):
    dev = install_dev(remote, feat_tree, tmp_path)
    install_from_clone(remote, "--tag", "t")
    t = sandbox_paths(tmp_path, "t")[0]
    push_feat(remote, "feat v2")
    push_change(remote, "main v2")

    r = update(remote, "--all", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "feat v2" in helper_text(dev) and "main v2" in helper_text(t)
    assert registry(tmp_path) == {str(dev): entry("dev", remote.url, "feat"), str(t): entry("t", remote.url)}
    assert list(remote.tmpdir.iterdir()) == []

    push_feat(remote, "feat v3")
    r = run_launcher(claude_launcher(tmp_path, "dev"), launcher_env(remote, tmp_path), "update", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "feat v3" in helper_text(dev) and "main v2" in helper_text(t)
    assert registry(tmp_path)[str(dev)] == entry("dev", remote.url, "feat")
    assert list(remote.tmpdir.iterdir()) == []


def test_update_entry_without_branch_counts_as_main(remote, tmp_path):
    install_from_clone(remote, "--tag", "t")
    t = sandbox_paths(tmp_path, "t")[0]
    reg = state_dir(tmp_path) / "installs.json"
    data = json.loads(reg.read_text())
    del data["installs"][str(t)]["branch"]
    reg.write_text(json.dumps(data))
    push_change(remote, "main legacy")
    r = update(remote, "--tag", "t", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "main legacy" in helper_text(t)
    assert list(remote.tmpdir.iterdir()) == []


def test_update_gone_branch_is_stale(remote, feat_tree, tmp_path):
    dev = install_dev(remote, feat_tree, tmp_path)
    before, reg_before = snapshot(dev), registry(tmp_path)
    remote.git(remote.work, "push", "-q", "origin", "--delete", "feat")

    r = update(remote, "--tag", "dev", "--yes")
    assert r.returncode == 3, r.stdout + r.stderr
    assert stale_line(dev, remote.url) in r.stdout.splitlines()
    assert snapshot(dev) == before and registry(tmp_path) == reg_before
    assert list(remote.tmpdir.iterdir()) == []

    # under --all the other installs carry on, and the exit code is still 3
    install_from_clone(remote, "--tag", "t")
    t = sandbox_paths(tmp_path, "t")[0]
    push_change(remote, "main after stale")
    r = update(remote, "--all", "--yes")
    assert r.returncode == 3, r.stdout + r.stderr
    assert stale_line(dev, remote.url) in r.stdout.splitlines()
    assert "main after stale" in helper_text(t) and snapshot(dev) == before
    assert list(remote.tmpdir.iterdir()) == []


def test_update_ls_remote_failure_is_error_not_stale(remote, tmp_path):
    install_from_clone(remote, "--tag", "t")
    t = sandbox_paths(tmp_path, "t")[0]
    before = snapshot(t)
    bad = "file://%s" % (tmp_path / "nowhere.git")
    reg = state_dir(tmp_path) / "installs.json"
    data = json.loads(reg.read_text())
    data["installs"][str(t)]["remote"] = bad
    reg.write_text(json.dumps(data))

    r = update(remote, "--tag", "t", "--yes")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "ERROR %s: cannot read branch main" % bad in r.stdout
    assert "STALE" not in r.stdout + r.stderr and snapshot(t) == before


def test_update_from_checkout_skips_other_branches(remote, feat_tree, tmp_path):
    dev = install_dev(remote, feat_tree, tmp_path)
    install_from_clone(remote, "--tag", "t")
    t = sandbox_paths(tmp_path, "t")[0]
    before = snapshot(dev)
    (remote.clone / "pack" / "agents" / "helper.md").write_text(agent_md("helper", "local main"))
    r = deploy_run(remote, remote.clone / "deploy", "update", "--from", str(remote.clone), "--all", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "local main" in helper_text(t)
    assert snapshot(dev) == before and "feat v1" in helper_text(dev)
    assert registry(tmp_path)[str(dev)] == entry("dev", remote.url, "feat")


def test_status_shows_remote_and_branch(remote, feat_tree, tmp_path):
    install_dev(remote, feat_tree, tmp_path)
    r = deploy_run(remote, feat_tree / "deploy", "status", "--tag", "dev")
    assert "Remote: %s" % remote.url in r.stdout.splitlines() and "Branch: feat" in r.stdout.splitlines()

    reg = state_dir(tmp_path) / "installs.json"
    reg.write_text(json.dumps({"version": 1, "installs": {}}))
    r = deploy_run(remote, feat_tree / "deploy", "status", "--tag", "dev")
    assert "Remote: not registered" in r.stdout.splitlines() and "Branch:" not in r.stdout


# --------------------------------------------------------------------------- migrate

SANDBOX_AGENT = "agents/supervisor.md"
OLD_FILES = ("agents/helper.md", "agents/supervisor.md", "skills/demo/SKILL.md", "skills/demo/scripts/run.sh")
OLD_NAMES = {MANIFEST, LEGACY_MANIFEST, ".claude-supervisor.lock", ".claude-agents.lock"}


def migrate(pack, global_target, *args, **kw) -> subprocess.CompletedProcess:
    return run(pack, global_target, "migrate", *args, target_args=[], **kw)


def old_install(request, pack, global_target, legacy=False) -> None:
    if legacy:
        request.getfixturevalue("legacy_install")
    else:
        assert run(pack, global_target, "install").returncode == 0


def backups(global_target: Path) -> list:
    return sorted(global_target.glob("claude-supervisor-backup-*"))


@pytest.mark.parametrize("legacy", [False, True])
def test_migrate_moves_old_install_to_sandbox(request, pack, global_target, tmp_path, legacy):
    old_install(request, pack, global_target, legacy)
    sbx, launcher = sandbox_paths(tmp_path, "supervisor")
    r = migrate(pack, global_target, "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    for name in OLD_NAMES:
        assert not (global_target / name).exists(), name
    for rel in OLD_FILES:
        assert not (global_target / rel).exists(), rel
    assert (sbx / MANIFEST).is_file() and (sbx / SANDBOX_AGENT).is_file()
    assert launcher.is_file()
    reg = registry(tmp_path)
    assert str(sbx) in reg and str(global_target.resolve()) not in reg


def test_migrate_backs_up_edited_files_only(request, pack, global_target, tmp_path):
    old_install(request, pack, global_target)
    sbx, _ = sandbox_paths(tmp_path, "supervisor")
    (global_target / "agents" / "helper.md").write_text("my edits")
    settings_before = (global_target / "settings.json").read_text()
    r = migrate(pack, global_target, "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    (backup,) = backups(global_target)
    assert snapshot(backup).keys() == {"agents/helper.md", "settings.json"}
    assert (backup / "agents" / "helper.md").read_text() == "my edits"
    assert (backup / "settings.json").read_text() == settings_before
    assert "  backed up agents/helper.md" in r.stdout
    assert not (global_target / "agents" / "helper.md").exists()
    assert not (sbx / "agents" / "helper.md").exists()


def test_migrate_leaves_other_files_alone(request, pack, global_target):
    old_install(request, pack, global_target)
    user = {"CLAUDE.md": "notes", "agents/mine.md": "mine", "skills/own/SKILL.md": "own",
            "history.jsonl": "{}", "plugins/p.json": "[]"}
    for rel, text in user.items():
        (global_target / rel).parent.mkdir(parents=True, exist_ok=True)
        (global_target / rel).write_text(text)
    before_files = {rel: (global_target / rel).read_bytes() for rel in user}
    before = {p.name for p in global_target.iterdir()}
    r = migrate(pack, global_target, "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    for rel, data in before_files.items():
        assert (global_target / rel).read_bytes() == data, rel
    after = {p.name for p in global_target.iterdir()}
    extras = {n for n in after if n.startswith(("claude-supervisor-backup-", "settings.json.bak-"))}
    assert len(backups(global_target)) == 1
    assert after - extras == before - OLD_NAMES


@pytest.mark.parametrize("prior_agent, expected", [
    ("other", {"agent": "other", "theme": "dark"}),
    (None, {"theme": "dark"}),
])
def test_migrate_restores_agent_setting(pack, global_target, tmp_path, prior_agent, expected):
    global_target.mkdir()
    prior = {"theme": "dark"} if prior_agent is None else {"agent": prior_agent, "theme": "dark"}
    (global_target / "settings.json").write_text(json.dumps(prior))
    assert run(pack, global_target, "install", "--force-default-agent").returncode == 0
    assert settings(global_target)["agent"] == "supervisor"
    r = migrate(pack, global_target, "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert settings(global_target) == expected
    assert settings(sandbox_paths(tmp_path, "supervisor")[0])["agent"] == "supervisor"


@pytest.mark.parametrize("user_files", [{}, {"CLAUDE.md": "notes"}])
def test_migrate_without_old_install(pack, global_target, tmp_path, user_files):
    for rel, text in user_files.items():
        global_target.mkdir(exist_ok=True)
        (global_target / rel).write_text(text)
    before = snapshot(global_target)
    sbx, launcher = sandbox_paths(tmp_path, "supervisor")
    r = migrate(pack, global_target)  # no --yes and no terminal: nothing to confirm
    assert r.returncode == 0, r.stdout + r.stderr
    assert "No pack install in %s; installing the default sandbox." % global_target.resolve() in r.stdout
    assert (sbx / MANIFEST).is_file() and launcher.is_file()
    assert snapshot(global_target) == before and not backups(global_target)


def test_migrate_dry_run_writes_nothing(request, pack, global_target, tmp_path):
    old_install(request, pack, global_target)
    (global_target / "agents" / "helper.md").write_text("my edits")
    before = snapshot(tmp_path)
    r = migrate(pack, global_target, "--dry-run")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "  would back up agents/helper.md" in r.stdout
    assert snapshot(tmp_path) == before
    assert not backups(global_target) and not (tmp_path / ".config").exists()


def test_migrate_without_yes_and_no_tty_refuses(request, pack, global_target, tmp_path):
    old_install(request, pack, global_target)
    (global_target / "agents" / "helper.md").write_text("my edits")
    before = snapshot(tmp_path)
    r = migrate(pack, global_target)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "re-run with --yes" in r.stderr
    home, sbx = global_target.resolve(), sandbox_paths(tmp_path, "supervisor")[0]
    assert ("Remove the agent pack from %s (4 files, 1 edited) and install the default sandbox %s? "
            "settings.json and edited files are backed up to %s/claude-supervisor-backup-"
            % (home, sbx, home)) in r.stderr
    assert snapshot(tmp_path) == before


def test_migrate_stops_when_uninstall_fails(request, pack, global_target, tmp_path):
    old_install(request, pack, global_target)
    (global_target / "settings.json").write_text("{bad")
    sbx, launcher = sandbox_paths(tmp_path, "supervisor")
    r = migrate(pack, global_target, "--yes")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "pack files were removed from ~/.claude (backup:" in r.stdout
    assert "re-run ./deploy migrate" in r.stdout
    assert not sbx.exists() and not launcher.exists()
    (backup,) = backups(global_target)
    assert (backup / "settings.json").read_text() == "{bad"


@pytest.mark.parametrize("on_path", [False, True])
def test_migrate_path_warning(pack, global_target, tmp_path, on_path):
    bin_dir = (tmp_path / ".local" / "bin").resolve()
    path = None
    if on_path:
        path = str(tmp_path / ".local" / "bin") + os.pathsep + str(tmp_path / "bin")
    r = migrate(pack, global_target, "--yes", path=path)
    assert r.returncode == 0, r.stdout + r.stderr
    if on_path:
        assert "PATH: %s is on PATH" % bin_dir in r.stdout
        assert "export PATH=" not in r.stdout
    else:
        assert "WARNING: %s is not on PATH" % bin_dir in r.stdout
        assert 'export PATH="%s:$PATH"' % bin_dir in r.stdout


def test_migrate_honors_prefix(request, pack, global_target, tmp_path):
    old_install(request, pack, global_target)
    px = tmp_path / "px"
    bin_dir = (px / "bin").resolve()
    r = migrate(pack, global_target, "--yes", "--prefix", str(px))
    assert r.returncode == 0, r.stdout + r.stderr
    assert (px / "bin" / "claude-supervisor").is_file()
    assert not (tmp_path / ".local" / "bin").exists()
    assert str(bin_dir) in r.stdout and 'export PATH="%s:$PATH"' % bin_dir in r.stdout
    assert str(sandbox_paths(tmp_path, "supervisor")[0]) in registry(tmp_path, px)


# --------------------------------------------------------------------------- doctor

def doctor_bin(tmp_path: Path, version=None, tools=()) -> str:
    """A PATH holding only a stub `claude` (none when version is None) and links to the named tools."""
    bin_dir = tmp_path / "dbin"
    bin_dir.mkdir(exist_ok=True)
    if version is not None:
        stub_claude(bin_dir, version)
    for tool in tools:
        found = shutil.which(tool)
        if found is None:
            pytest.skip("%s not available" % tool)
        (bin_dir / tool).symlink_to(found)
    return str(bin_dir)


def run_doctor(pack, target, tmp_path, version="2.1.300", tools=(), env=None):
    return run(pack, target, "doctor", path=doctor_bin(tmp_path, version, tools), env=env)


def rows_of(r) -> list:
    return [l for l in r.stdout.splitlines() if l[:5] in ("PASS ", "WARN ", "FAIL ")]


def row(r, fragment: str) -> str:
    hits = [l for l in rows_of(r) if fragment in l]
    assert len(hits) == 1, (fragment, r.stdout)
    return hits[0]


def test_doctor_all_pass(pack, target, tmp_path):
    assert run(pack, target, "install").returncode == 0
    r = run_doctor(pack, target, tmp_path, tools=("git", "zip"))
    assert r.returncode == 0, r.stdout + r.stderr
    assert len(rows_of(r)) >= 6 and all(l.startswith("PASS") for l in rows_of(r)), r.stdout
    assert "0 FAIL, 0 WARN" in r.stdout
    assert not (tmp_path / "dbin" / "claude.argv").exists()  # doctor only asks for --version


def test_doctor_claude_missing_fails(pack, target, tmp_path):
    r = run_doctor(pack, target, tmp_path, version=None)
    assert r.returncode == 1, r.stdout + r.stderr
    line = row(r, "claude CLI not found on PATH")
    assert line.startswith("FAIL") and "install Claude Code" in line


def test_doctor_old_claude_fails(pack, target, tmp_path):
    r = run_doctor(pack, target, tmp_path, version="2.0.5")
    assert r.returncode == 1, r.stdout + r.stderr
    line = row(r, "older than")
    assert line.startswith("FAIL") and "claude 2.0.5" in line and "claude update" in line


def test_doctor_unparsable_claude_version_fails(pack, target, tmp_path):
    r = run_doctor(pack, target, tmp_path, version="unknown-build")
    assert r.returncode == 1, r.stdout + r.stderr
    line = row(r, "cannot determine claude version")
    assert line.startswith("FAIL") and "reinstall Claude Code" in line


def test_doctor_missing_managed_file_fails(pack, target, tmp_path):
    assert run(pack, target, "install").returncode == 0
    (target / "agents" / "helper.md").unlink()
    r = run_doctor(pack, target, tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    line = row(r, "managed files missing:")
    assert line.startswith("FAIL") and "agents/helper.md" in line and "./deploy install" in line


def test_doctor_modified_managed_file_warns(pack, target, tmp_path):
    assert run(pack, target, "install").returncode == 0
    (target / "agents" / "helper.md").write_text("my edits")
    r = run_doctor(pack, target, tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    line = row(r, "managed files modified:")
    assert line.startswith("WARN") and "agents/helper.md" in line and "--overwrite-local" in line
    assert "managed files missing" not in r.stdout


@pytest.mark.parametrize("origin", ["environment", "settings.json env"])
@pytest.mark.parametrize("var, value", [
    ("CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH", "1"),
    ("CLAUDE_CODE_SUBAGENT_MODEL_FORCE", "1"),
    ("CLAUDE_CODE_EFFORT_LEVEL", "high"),
])
def test_doctor_env_var_warns_with_remedy(pack, target, tmp_path, var, value, origin):
    assert run(pack, target, "install").returncode == 0
    env = None
    if origin == "environment":
        env = {var: value}
    else:
        data = settings(target)
        data["env"] = {var: value}
        (target / "settings.json").write_text(json.dumps(data))
    r = run_doctor(pack, target, tmp_path, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    line = row(r, var)
    assert line.startswith("WARN") and "in " + origin in line
    assert "unset it, or remove it from settings.json env" in line


def test_doctor_without_manifest_gives_one_warn(pack, target, tmp_path):
    r = run_doctor(pack, target, tmp_path, tools=("git", "zip"))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "0 FAIL, 1 WARN" in r.stdout
    line = row(r, "pack not installed")
    assert line.startswith("WARN") and "./deploy install" in line
    assert "settings agent" not in r.stdout  # D-59: no row before an install


def test_doctor_agent_not_default_warns_with_remedy(pack, target, tmp_path):
    assert run(pack, target, "install", "--no-default-agent").returncode == 0
    r = run_doctor(pack, target, tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    line = row(r, "settings agent")
    assert line.startswith("WARN") and "./deploy install" in line and "--force-default-agent" in line


@pytest.mark.parametrize("content, fragments", [
    ("{bad", ["cannot read manifest", "restore it from a backup, or delete it"]),
    (json.dumps({"version": 99, "files": {}}), ["unsupported version", "written by a newer deploy"]),
])
def test_doctor_corrupt_manifest_fails(pack, target, tmp_path, content, fragments):
    target.mkdir()
    (target / MANIFEST).write_text(content)
    r = run_doctor(pack, target, tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    line = row(r, "manifest")
    assert line.startswith("FAIL")
    for fragment in fragments:
        assert fragment in line
    assert "Traceback" not in r.stderr


def test_doctor_unparsable_settings_fails(pack, target, tmp_path):
    assert run(pack, target, "install").returncode == 0
    (target / "settings.json").write_text("{bad")
    r = run_doctor(pack, target, tmp_path)
    assert r.returncode == 1, r.stdout + r.stderr
    line = row(r, "cannot parse")
    assert line.startswith("FAIL") and "fix the JSON" in line and "settings step skipped" not in line


def test_doctor_git_missing_warns(pack, target, tmp_path):
    r = run_doctor(pack, target, tmp_path, tools=("zip",))
    assert r.returncode == 0, r.stdout + r.stderr
    line = row(r, "git not found")
    assert line.startswith("WARN") and "needed for ./deploy update" in line


def test_doctor_old_python_fails(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", doctor_bin(tmp_path, "2.1.300"))
    deploy = load_deploy()
    deploy.sys = SimpleNamespace(version_info=(3, 8, 0), version="3.8.0 (fake)", executable=sys.executable,
                                 stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, argv=sys.argv)
    args = deploy.build_parser().parse_args(["doctor", "--target", str(tmp_path / "claude")])
    assert deploy.doctor_cmd(args) == 1
    out = capsys.readouterr().out
    line = [l for l in out.splitlines() if l.startswith("FAIL") and "python" in l]
    assert line and "deploy needs 3.9 or newer" in line[0]


# --------------------------------------------------------------------------- prompts (in-process)

def tty_deploy(monkeypatch, answers: list):
    """The deploy module with a terminal stdin whose `input` returns (or raises) each answer in turn."""
    deploy = load_deploy()
    asked = []

    def fake_input(prompt=""):
        asked.append(prompt)
        answer = answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        return answer

    monkeypatch.setattr(sys, "stdin", SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr("builtins.input", fake_input)
    return deploy, asked


@pytest.mark.parametrize("answer, expected", [
    ("y", True), ("YES", True), (" yes ", True), ("n", False), ("", False), ("maybe", False)])
def test_confirm_answers(monkeypatch, answer, expected):
    deploy, asked = tty_deploy(monkeypatch, [answer])
    assert deploy.confirm("Proceed?", False) is expected
    assert asked == ["Proceed? [y/N] "]


@pytest.mark.parametrize("answer, expected", [("t", True), (" t ", True), ("T", False), ("", False), ("y", False)])
def test_confirm_typed_answers(monkeypatch, answer, expected):
    deploy, asked = tty_deploy(monkeypatch, [answer])
    assert deploy.confirm_typed("Delete it?", "t", False) is expected
    assert "Type t to confirm" in asked[0]


def test_uninstall_launcher_requires_typed_tag(pack, target, tmp_path, monkeypatch, capsys):
    sbx, launcher = sandbox_paths(tmp_path, "t")
    assert run(pack, target, "install", target_args=["--tag", "t"]).returncode == 0
    monkeypatch.setenv("HOME", str(tmp_path))
    deploy, asked = tty_deploy(monkeypatch, ["yes", "t"])
    assert deploy.main(["uninstall", "--tag", "t", "--launcher"]) == 1  # "yes" is not the tag
    assert "aborted" in capsys.readouterr().err
    assert (sbx / MANIFEST).is_file() and launcher.is_file()
    assert deploy.main(["uninstall", "--tag", "t", "--launcher"]) == 0
    assert not sbx.exists() and not launcher.exists()
    assert all("Type t to confirm" in q for q in asked)


def test_eof_at_prompt_aborts(pack, global_target, target, tmp_path, monkeypatch, capsys):
    assert run(pack, global_target, "install").returncode == 0
    assert run(pack, target, "install", target_args=["--tag", "t"]).returncode == 0
    monkeypatch.setenv("HOME", str(tmp_path))
    deploy, _ = tty_deploy(monkeypatch, [EOFError()])
    assert deploy.main(["uninstall", "--global"]) == 1
    assert "aborted" in capsys.readouterr().err
    assert (global_target / "agents" / "helper.md").exists()
    assert (sandbox_paths(tmp_path, "t")[0] / MANIFEST).is_file()


def test_keyboard_interrupt_names_the_next_step(pack, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path))
    deploy = load_deploy()

    def interrupted(args):
        raise KeyboardInterrupt

    deploy.install_cmd = interrupted
    assert deploy.main(["install", "--global", "--source", str(pack)]) == 130
    assert "interrupted; re-run ./deploy install" in capsys.readouterr().err


# --------------------------------------------------------------------------- errors without tracebacks

def test_missing_token_file_is_a_clean_error(pack, target, tmp_path):
    r = run(pack, target, "install", "--token-file", str(tmp_path / "nope"), target_args=["--tag", "t"])
    assert r.returncode == 2, r.stdout + r.stderr
    assert "cannot read --token-file" in r.stderr and "Traceback" not in r.stderr
    assert not (tmp_path / ".config").exists() and not (tmp_path / ".local").exists()  # validated first


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores directory permissions")
def test_oserror_is_a_clean_error(pack, global_target):
    global_target.mkdir()
    global_target.chmod(0o500)
    try:
        r = run(pack, global_target, "install")
    finally:
        global_target.chmod(0o700)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "error:" in r.stderr and "Traceback" not in r.stderr


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads any file")
def test_seed_failure_cleans_up_and_names_the_source(pack, target, tmp_path):
    sbx, _ = sandbox_paths(tmp_path, "t")
    unreadable = tmp_path / ".claude" / "skills" / "own" / "x.md"
    unreadable.parent.mkdir(parents=True)
    unreadable.write_text("x")
    unreadable.chmod(0)
    try:
        r = run(pack, target, "install", target_args=["--tag", "t"])
    finally:
        unreadable.chmod(0o644)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "cannot seed from" in r.stderr and "Traceback" not in r.stderr
    assert "Seeded" not in r.stdout
    assert not (sbx / "skills").exists()  # no partial copy left to make a re-run skip the seed


def test_seed_preserves_symlinks(pack, target, tmp_path):
    sbx, _ = sandbox_paths(tmp_path, "t")
    own = tmp_path / ".claude" / "skills" / "own"
    own.mkdir(parents=True)
    (own / "SKILL.md").write_text("own")
    (own / "link.md").symlink_to("SKILL.md")
    (own / "dangling.md").symlink_to("missing.md")
    r = run(pack, target, "install", target_args=["--tag", "t"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert (sbx / "skills" / "own" / "link.md").is_symlink()
    assert os.readlink(str(sbx / "skills" / "own" / "link.md")) == "SKILL.md"
    assert (sbx / "skills" / "own" / "dangling.md").is_symlink()
    assert r.stdout.index("Seeded") < r.stdout.index("Summary")


def test_seed_with_invalid_global_settings_uses_seed_wording(pack, target, tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text("{bad")
    r = run(pack, target, "install", target_args=["--tag", "t"])
    assert r.returncode == 2, r.stdout + r.stderr
    assert "cannot seed from" in r.stderr and "Traceback" not in r.stderr
    assert "settings step skipped" not in r.stdout + r.stderr and "Seeded" not in r.stdout


def test_seed_dry_run_reports_and_writes_nothing(pack, target, tmp_path):
    sbx, _ = sandbox_paths(tmp_path, "t")
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "CLAUDE.md").write_text("notes")
    r = run(pack, target, "install", "--dry-run", target_args=["--tag", "t"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Would seed" in r.stdout and "CLAUDE.md" in r.stdout
    assert not sbx.exists()


@pytest.mark.parametrize("content", ["{bad", '{"version": 1, "installs": []}', '{"version": 2, "installs": {}}'])
def test_corrupt_registry_refuses_before_writing(pack, target, tmp_path, content):
    reg = state_dir(tmp_path) / "installs.json"
    reg.parent.mkdir(parents=True)
    reg.write_text(content)
    r = run(pack, target, "install", target_args=["--tag", "t"])
    assert r.returncode == 2, r.stdout + r.stderr
    assert "Traceback" not in r.stderr
    assert "delete or fix that file, then re-run ./deploy install" in r.stderr
    assert not (tmp_path / ".config").exists() and not (tmp_path / ".local" / "bin").exists()
    assert snapshot(state_dir(tmp_path)) == {"installs.json": hashlib.sha256(content.encode()).hexdigest()}


@pytest.mark.parametrize("content, fragments", [
    ("{bad", ["cannot read manifest", "restore it from a backup, or delete it"]),
    (json.dumps({"version": 99, "files": {}}), ["unsupported version", "written by a newer deploy"]),
    (json.dumps({"version": 1, "files": {"agents/x.md": "oops"}}), ["manifest"]),
    (json.dumps([1]), ["manifest"]),
])
def test_corrupt_manifest_is_a_clean_error(pack, target, content, fragments):
    target.mkdir()
    (target / MANIFEST).write_text(content)
    before = snapshot(target)
    r = run(pack, target, "install")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "Traceback" not in r.stderr
    for fragment in fragments:
        assert fragment in r.stderr, r.stderr
    assert snapshot(target) == before


@pytest.mark.parametrize("content, fragment", [("{bad", "cannot parse"), ("[]", "not a JSON object")])
def test_malformed_settings_is_reported_not_overwritten(pack, target, content, fragment):
    target.mkdir()
    (target / "settings.json").write_text(content)
    r = run(pack, target, "install")
    assert r.returncode == 1, r.stdout + r.stderr
    assert fragment in r.stdout and "Traceback" not in r.stderr
    assert "settings step skipped" in r.stdout  # install wording stays on install
    assert (target / "settings.json").read_text() == content
    r = run(pack, target, "status")
    assert r.returncode == 0 and fragment in r.stdout
    assert "settings step skipped" not in r.stdout


# --------------------------------------------------------------------------- source validation

def _no_dirs(p):
    shutil.rmtree(str(p / "agents"))
    shutil.rmtree(str(p / "skills"))


def _gone(p):
    shutil.rmtree(str(p))


def _agent_without_frontmatter(p):
    (p / "agents" / "helper.md").write_text("no frontmatter here\n")


def _agent_without_description(p):
    (p / "agents" / "helper.md").write_text("---\nname: helper\n---\n\nBody.\n")


def _skill_without_skill_md(p):
    (p / "skills" / "demo" / "SKILL.md").unlink()


def _skill_wrong_name(p):
    (p / "skills" / "demo" / "SKILL.md").write_text("---\nname: other\ndescription: d.\n---\n")


def _skill_without_frontmatter(p):
    (p / "skills" / "demo" / "SKILL.md").write_text("Just text, no frontmatter.\n")


def _symlinked_skill_dir(p):
    (p / "skills" / "alias").symlink_to(p / "skills" / "demo")


def _symlinked_agent(p):
    (p / "agents" / "alias.md").symlink_to(p / "agents" / "helper.md")


@pytest.mark.parametrize("mutate, fragment", [
    (_no_dirs, "has neither agents/ nor skills/"),
    (_gone, "source directory not found"),
    (_agent_without_frontmatter, "missing --- frontmatter"),
    (_agent_without_description, "missing description"),
    (_skill_without_skill_md, "missing SKILL.md"),
    (_skill_wrong_name, "frontmatter name 'other' != directory 'demo'"),
    (_skill_without_frontmatter, "missing --- frontmatter"),
    (_symlinked_skill_dir, "symlink not allowed"),
    (_symlinked_agent, "symlink not allowed"),
])
def test_source_validation_branches(pack, target, mutate, fragment):
    mutate(pack)
    r = run(pack, target, "install")
    assert r.returncode == 2, r.stdout + r.stderr
    assert fragment in r.stderr and "Traceback" not in r.stderr
    assert "frontmatter name None" not in r.stderr
    if mutate is _gone:
        assert "run ./deploy from the repo checkout or pass --source DIR" in r.stderr
    assert not target.exists()


# --------------------------------------------------------------------------- reconcile and status branches

def test_status_reports_outdated_and_not_installed(pack, target):
    assert run(pack, target, "install").returncode == 0
    (pack / "agents" / "helper.md").write_text(agent_md("helper", "v2"))
    (pack / "agents" / "extra.md").write_text(agent_md("extra"))
    r = run(pack, target, "status")
    assert r.returncode == 0, r.stdout + r.stderr
    states = dict(l.strip().split(None, 1) for l in r.stdout.splitlines() if l.startswith("  "))
    assert states["agents/helper.md"] == "outdated"
    assert states["agents/extra.md"] == "not installed"
    assert states["agents/supervisor.md"] == "ok"


def test_status_after_source_dir_removed_says_what_to_do(pack, target):
    assert run(pack, target, "install").returncode == 0
    shutil.rmtree(str(pack))
    env = {"PATH": str(target.parent / "bin"), "HOME": str(target.parent)}
    r = subprocess.run([sys.executable, str(SCRIPT), "status", "--target", str(target)], capture_output=True,
                       text=True, env=env, timeout=60, stdin=subprocess.DEVNULL)  # no --source, as after update
    assert r.returncode == 0, r.stdout + r.stderr
    assert "source dir gone; pass --source" in r.stdout


def test_symlink_at_target_is_skipped_with_next_step(pack, target, tmp_path):
    assert run(pack, target, "install").returncode == 0
    dst = target / "agents" / "helper.md"
    elsewhere = tmp_path / "elsewhere.md"
    elsewhere.write_text("elsewhere")
    dst.unlink()
    dst.symlink_to(elsewhere)
    r = run(pack, target, "install")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "target is a symlink or not a regular file; skipped" in r.stdout
    assert "replace it with a regular file or remove it, then re-run" in r.stdout
    assert dst.is_symlink() and elsewhere.read_text() == "elsewhere"
    assert "agents/helper.md" in manifest(target)["files"]  # the baseline survives


def test_removed_from_source_but_modified_is_kept_unmanaged(pack, target):
    assert run(pack, target, "install").returncode == 0
    (pack / "agents" / "helper.md").unlink()
    (target / "agents" / "helper.md").write_text("mine")
    r = run(pack, target, "install")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "removed from source but locally modified; kept and no longer managed" in r.stdout
    assert (target / "agents" / "helper.md").read_text() == "mine"
    assert "agents/helper.md" not in manifest(target)["files"]


def test_base_url_empty_string_clears(pack, target, tmp_path):
    _, launcher = sandbox_paths(tmp_path, "t")
    args = ["--tag", "t"]
    assert run(pack, target, "install", "--base-url", "https://llm.example", target_args=args).returncode == 0
    assert "ANTHROPIC_BASE_URL" in launcher.read_text()
    r = run(pack, target, "install", "--base-url", "", target_args=args)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ANTHROPIC_BASE_URL" not in launcher.read_text()
    assert manifest(sandbox_paths(tmp_path, "t")[0])["base_url"] is None


def test_second_target_with_same_tag_refused(pack, target, tmp_path):
    sbx, launcher = sandbox_paths(tmp_path, "t")
    assert run(pack, target, "install", target_args=["--tag", "t"]).returncode == 0
    text, before = launcher.read_text(), snapshot(sbx)
    other = tmp_path / "other"
    r = run(pack, target, "install", target_args=["--tag", "t", "--target", str(other)])
    assert r.returncode == 2, r.stdout + r.stderr
    assert "already launches" in r.stderr and "Traceback" not in r.stderr
    assert launcher.read_text() == text and snapshot(sbx) == before and not other.exists()


@pytest.mark.parametrize("on_path", [False, True])
def test_install_warns_when_launcher_dir_is_off_path(pack, target, tmp_path, on_path):
    bin_dir = (tmp_path / ".local" / "bin").resolve()
    path = (str(tmp_path / ".local" / "bin") + os.pathsep + str(tmp_path / "bin")) if on_path else None
    r = run(pack, target, "install", target_args=["--tag", "t"], path=path)
    assert r.returncode == 0, r.stdout + r.stderr
    if on_path:
        assert "is not on your PATH" not in r.stdout
    else:
        assert "is not on your PATH; add export PATH=" in r.stdout
        assert 'export PATH="%s:$PATH"' % bin_dir in r.stdout


def test_uninstall_help_states_the_sandbox_default():
    r = subprocess.run([sys.executable, str(SCRIPT), "uninstall", "--help"], capture_output=True, text=True)
    text = " ".join(r.stdout.split())
    assert r.returncode == 0
    assert "deletes the whole sandbox dir and its launcher" in text
    assert "--global: removes only pack files" in text


@pytest.mark.parametrize("kind", ["foreign", "missing"])
def test_uninstall_reports_only_what_it_removed(pack, target, tmp_path, kind):
    sbx, launcher = sandbox_paths(tmp_path, "t")
    assert run(pack, target, "install", target_args=["--tag", "t"]).returncode == 0
    if kind == "foreign":
        launcher.write_text("#!/bin/sh\necho mine\n")
    else:
        launcher.unlink()
    r = run(pack, target, "uninstall", "--yes", target_args=["--tag", "t"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert not sbx.exists()
    removed = [l for l in r.stdout.splitlines() if l.startswith("Removed ")]
    assert removed and str(launcher) not in removed[0]
    if kind == "foreign":
        assert "is not a claude-supervisor launcher; left in place" in r.stdout
        assert launcher.read_text() == "#!/bin/sh\necho mine\n"


def test_uninstall_prunes_dirs_holding_only_junk(pack, global_target):
    assert run(pack, global_target, "install").returncode == 0
    for rel in ("skills/demo", "skills/demo/scripts"):
        (global_target / rel / ".DS_Store").write_text("junk")
    r = run(pack, global_target, "uninstall", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (global_target / "skills" / "demo").exists()


@pytest.mark.parametrize("url, expected", [
    ("https://user:tok3n@example.com/o/r.git", "https://example.com/o/r.git"),
    ("https://tok3n@example.com/o/r.git", "https://example.com/o/r.git"),
    ("file:///srv/r.git", "file:///srv/r.git"),
    ("git@github.com:o/r.git", "git@github.com:o/r.git"),
])
def test_git_remote_strips_credentials(tmp_path, monkeypatch, url, expected):
    git_bin = shutil.which("git")
    if git_bin is None:
        pytest.skip("git not available")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    repo = tmp_path / "repo"
    for cmd in (["init", "-q", str(repo)], ["-C", str(repo), "remote", "add", "origin", url]):
        assert subprocess.run([git_bin] + cmd, capture_output=True).returncode == 0
    assert load_deploy().git_remote(repo) == expected


# --------------------------------------------------------------------------- update (remote fixture)

def test_update_dry_run_changes_nothing(remote, tmp_path):
    install_from_clone(remote, "--tag", "t")
    sbx, _ = sandbox_paths(tmp_path, "t")
    push_change(remote, "v11 dry")
    before = (snapshot(sbx), snapshot(remote.state), registry(tmp_path))
    r = update(remote, "--tag", "t", "--yes", "--dry-run")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "[dry-run]" in r.stdout and "would update agents/helper.md" in r.stdout
    assert "v11 dry" not in helper_text(sbx)
    assert (snapshot(sbx), snapshot(remote.state), registry(tmp_path)) == before
    assert list(remote.tmpdir.iterdir()) == []


def test_update_clone_failure_names_the_next_step(remote, tmp_path):
    install_from_clone(remote, "--tag", "t")
    sbx, _ = sandbox_paths(tmp_path, "t")
    before = snapshot(sbx)
    shim = tmp_path / "shim"
    shim.mkdir()
    real_git = shutil.which("git", path=remote.env["PATH"])
    (shim / "git").write_text('#!/bin/sh\n[ "$1" = clone ] && exit 128\nexec %s "$@"\n' % real_git)
    (shim / "git").chmod(0o755)
    env = dict(remote.env, PATH="%s:%s" % (shim, remote.env["PATH"]))
    r = subprocess.run([sys.executable, str(remote.state / "deploy"), "update", "--tag", "t", "--yes"],
                       capture_output=True, text=True, env=env, timeout=120, stdin=subprocess.DEVNULL)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "clone failed" in r.stdout
    assert "check network access, credentials and that the branch exists, or pass --from DIR" in r.stdout
    assert snapshot(sbx) == before and list(remote.tmpdir.iterdir()) == []


def test_update_without_git_says_so(remote, tmp_path):
    install_from_clone(remote, "--tag", "t")
    nogit = tmp_path / "nogit"
    nogit.mkdir()
    r = subprocess.run([sys.executable, str(remote.state / "deploy"), "update", "--tag", "t", "--yes"],
                       capture_output=True, text=True, env=dict(remote.env, PATH=str(nogit)),
                       timeout=120, stdin=subprocess.DEVNULL)
    assert r.returncode == 1, r.stdout + r.stderr
    assert "git not found on PATH" in r.stdout + r.stderr
    assert "Traceback" not in r.stderr


def test_update_collision_names_the_real_fix(remote, tmp_path):
    install_from_clone(remote, "--tag", "t")
    sbx, _ = sandbox_paths(tmp_path, "t")
    (remote.clone / "pack" / "agents" / "extra.md").write_text(agent_md("extra"))
    (sbx / "agents" / "extra.md").write_text("mine")
    r = deploy_run(remote, remote.state / "deploy", "update", "--from", str(remote.clone), "--tag", "t", "--yes")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "run ./deploy install --overwrite-local from your checkout" in r.stdout
    assert (sbx / "agents" / "extra.md").read_text() == "mine"


def test_update_all_from_checkout_on_other_branch_says_nothing_updated(remote, feat_tree, tmp_path):
    install_from_clone(remote, "--tag", "t")
    before = snapshot(sandbox_paths(tmp_path, "t")[0])
    r = deploy_run(remote, remote.state / "deploy", "update", "--from", str(feat_tree), "--all", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "no registered install follows branch feat" in r.stdout and "nothing updated" in r.stdout
    assert snapshot(sandbox_paths(tmp_path, "t")[0]) == before


def test_update_from_other_branch_reports_new_tracking(remote, feat_tree, tmp_path):
    dev = install_dev(remote, feat_tree, tmp_path)
    r = deploy_run(remote, remote.state / "deploy", "update", "--from", str(remote.clone), "--tag", "dev", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "now tracking branch main" in r.stdout + r.stderr
    assert registry(tmp_path)[str(dev)] == entry("dev", remote.url, "main")


def test_install_records_source_commit_and_dirty(remote, tmp_path):
    sbx, _ = sandbox_paths(tmp_path, "t")
    git_bin = shutil.which("git", path=remote.env["PATH"])
    head = subprocess.run([git_bin, "-C", str(remote.clone), "rev-parse", "HEAD"], capture_output=True,
                          text=True, env=remote.env).stdout.strip()
    install_from_clone(remote, "--tag", "t")
    assert manifest(sbx)["source_commit"] == head and manifest(sbx)["source_dirty"] is False
    (remote.clone / "pack" / "agents" / "helper.md").write_text(agent_md("helper", "uncommitted"))
    install_from_clone(remote, "--tag", "t")
    assert manifest(sbx)["source_commit"] == head and manifest(sbx)["source_dirty"] is True


# --------------------------------------------------------------------------- migrate (preflight)

@pytest.mark.parametrize("breakage", ["launcher", "registry"])
def test_migrate_preflight_failure_leaves_the_pack_in_place(request, pack, global_target, tmp_path, breakage):
    old_install(request, pack, global_target)
    if breakage == "launcher":
        (tmp_path / ".local" / "bin").mkdir(parents=True)
        (tmp_path / ".local" / "bin" / "claude-supervisor").write_text("#!/bin/sh\necho mine\n")
    else:
        (state_dir(tmp_path) / "installs.json").write_text("{bad")
    before = snapshot(tmp_path)
    r = migrate(pack, global_target, "--yes")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "Traceback" not in r.stderr and "pack files were removed" not in r.stdout + r.stderr
    assert snapshot(tmp_path) == before  # ~/.claude still holds the pack, nothing backed up or installed
    assert (global_target / MANIFEST).is_file() and (global_target / "agents" / "helper.md").is_file()
    assert not backups(global_target) and not sandbox_paths(tmp_path, "supervisor")[0].exists()


def test_migrate_prefix_mismatch_refuses(request, pack, global_target, tmp_path):
    old_install(request, pack, global_target)
    pa = tmp_path / "pa"
    r = run(pack, global_target, "install", target_args=["--prefix", str(pa)])  # the default sandbox, prefix pa
    assert r.returncode == 0, r.stdout + r.stderr
    before = snapshot(tmp_path)
    r = migrate(pack, global_target, "--yes")
    assert r.returncode == 2, r.stdout + r.stderr
    assert "was installed with --prefix" in r.stderr and str(pa.resolve()) in r.stderr
    assert snapshot(tmp_path) == before and not backups(global_target)
    assert (global_target / "agents" / "helper.md").is_file()
