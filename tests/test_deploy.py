"""Behavior tests for scripts/deploy, run as a subprocess against temp dirs."""

import fcntl
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "deploy"
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


def run(pack: Path, target: Path, *args: str, target_args=None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_DIR"}
    env["PATH"] = str(target.parent / "bin")  # hides the real claude (and git)
    env["HOME"] = str(target.parent)  # hides the real ~/.claude.json
    if target_args is None:
        target_args = ["--global"] if target.name == ".claude" else ["--target", str(target)]
    cmd = [sys.executable, str(SCRIPT), args[0]] + list(target_args)
    if args[0] in ("install", "status"):
        cmd += ["--source", str(pack)]
    cmd += list(args[1:])
    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60,
                          stdin=subprocess.DEVNULL)


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
    assert r.returncode == 2 and "--yes" in r.stderr
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
    assert "lock" in r.stderr
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
    assert r.returncode == 0 and "--overwrite-local" in r.stdout and "--fable" in r.stdout
    for flag in ("--tag", "--global", "--bin-dir", "--base-url", "--token", "--token-file"):
        assert flag in r.stdout, flag


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
    args = deploy.build_parser().parse_args(["install", "--global", "--source", str(pack), "--fable"])
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
        ["install", "--global", "--source", str(pack), "--no-default-agent", "--fable"])
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


def test_default_install_rewrites_agents(fable_pack, target):
    r = run(fable_pack, target, "install")
    assert r.returncode == 0, r.stdout + r.stderr
    planner = (target / "agents" / "planner.md").read_text()
    assert "\nmodel: opus\neffort: xhigh\n" in planner
    assert "`model: opus`" in planner and "Critic runs on Fable." in planner
    assert "model: fable" not in "".join(p.read_text() for p in (target / "agents").iterdir())
    for key in ("agents/helper.md", "skills/demo/SKILL.md", "skills/demo/scripts/run.sh"):
        assert (target / key).read_bytes() == (fable_pack / key).read_bytes()
    assert manifest(target)["fable"] is False
    assert "Fable: off" in r.stdout


def test_fable_flag_is_verbatim(fable_pack, target):
    r = run(fable_pack, target, "install", "--fable")
    assert r.returncode == 0, r.stdout + r.stderr
    for key in manifest(target)["files"]:
        assert (target / key).read_bytes() == (fable_pack / key).read_bytes()
    assert manifest(target)["fable"] is True
    assert "Fable: on" in r.stdout


def test_status_matches_installed_variant(fable_pack, target):
    for args, expect in (("--fable",), "Fable: on"), ((), "Fable: off"):
        assert run(fable_pack, target, "install", *args).returncode == 0
        r = run(fable_pack, target, "status")
        assert expect in r.stdout
        assert "outdated" not in r.stdout and "modified" not in r.stdout
        rows = [l for l in r.stdout.splitlines() if l.startswith("  ")]
        assert rows and all(l.endswith("ok") for l in rows)


def test_fable_switch_updates(fable_pack, target):
    run(fable_pack, target, "install")
    r = run(fable_pack, target, "install", "--fable")
    assert "updated=1" in r.stdout
    assert (target / "agents" / "planner.md").read_bytes() == (fable_pack / "agents" / "planner.md").read_bytes()
    r = run(fable_pack, target, "install")
    assert "updated=1" in r.stdout
    assert "model: opus" in (target / "agents" / "planner.md").read_text()


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
    assert "Version: installed=1.7, source=1.8 (MISMATCH: run scripts/deploy install)" in r.stdout
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
    assert "run scripts/deploy install to migrate" in r.stdout
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
    assert after["fable"] is False


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
    assert "CLAUDE_CONFIG_DIR='%s'" % sbx in text and "ANTHROPIC_" not in text
    assert "Seed" not in r.stdout

    r = run_launcher(launcher, claude_stub(tmp_path), "a b", "--", "")
    assert r.returncode == 0, r.stderr
    assert r.stdout == "%s\n\n\na b\n--\n\n" % sbx

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
    def check(r, msg=None):
        assert r.returncode == 2, r.stdout + r.stderr
        if msg:
            assert msg in r.stderr, r.stderr
        assert not (tmp_path / ".config").exists() and not global_target.exists()

    check(run(pack, target, "install", target_args=["--tag", "a/b"]), "invalid tag")
    check(run(pack, target, "install", target_args=["--tag", ""]), "invalid tag")
    for flag, value in (("--tag", "t"), ("--target", "d"), ("--bin-dir", "d"), ("--base-url", "u"),
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
          "is not a claude-supervisor launcher")
    assert (bin_dir / "claude-t").read_text() == "#!/bin/sh\necho mine\n"
    (bin_dir / "claude-u").mkdir()
    check(run(pack, target, "install", target_args=["--tag", "u"]),
          "is not a claude-supervisor launcher")


def test_bin_dir_recorded_for_uninstall(pack, target, tmp_path):
    xbin = tmp_path / "xbin"
    r = run(pack, target, "install", target_args=["--tag", "t", "--bin-dir", str(xbin)])
    assert r.returncode == 0, r.stdout + r.stderr
    assert (xbin / "claude-t").is_file()
    assert not list((tmp_path / ".local" / "bin").glob("*"))
    r = run(pack, target, "uninstall", "--yes", target_args=["--tag", "t"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (xbin / "claude-t").exists()


def test_sandbox_uninstall_without_manifest_keeps_dir(pack, target, tmp_path):
    keep = tmp_path / ".config" / "claude-t" / "keep"
    keep.parent.mkdir(parents=True)
    keep.write_text("x")
    r = run(pack, target, "uninstall", "--yes", target_args=["--tag", "t"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert keep.read_text() == "x"
