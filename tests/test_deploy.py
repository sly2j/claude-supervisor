"""Behavior tests for scripts/deploy, run as a subprocess against temp dirs."""

import fcntl
import hashlib
import importlib.machinery
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "deploy"
MANIFEST = ".claude-supervisor-manifest.json"
LEGACY_MANIFEST = ".claude-agents-manifest.json"


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


def run(pack: Path, target: Path, *args: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_DIR"}
    env["PATH"] = str(target.parent / "bin")  # hides the real claude (and git); detection finds nothing
    env["HOME"] = str(target.parent)  # hides the real ~/.claude.json
    cmd = [sys.executable, str(SCRIPT), args[0], "--target", str(target)]
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


def test_uninstall_restores_previous_agent(pack, target):
    target.mkdir()
    (target / "settings.json").write_text(json.dumps({"agent": "mine", "x": 1}))
    run(pack, target, "install", "--force-default-agent")
    (target / "skills" / "demo" / "SKILL.md").write_text("edited")
    r = run(pack, target, "uninstall", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (target / "agents" / "supervisor.md").exists()
    assert not (target / "skills" / "demo" / "scripts").exists()
    assert (target / "skills" / "demo" / "SKILL.md").read_text() == "edited"  # modified kept
    assert settings(target) == {"agent": "mine", "x": 1}
    assert not (target / MANIFEST).exists()


def test_uninstall_removes_agent_key(pack, target):
    run(pack, target, "install")
    r = run(pack, target, "uninstall", "--yes")
    assert r.returncode == 0
    assert settings(target) == {}
    assert not (target / "agents" / "helper.md").exists()


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
def test_settings_write_failure_keeps_manifest_consistent(pack, target, write_first):
    deploy = load_deploy()
    real_save = deploy.save_settings

    def failing_save(tgt, data):
        if write_first:
            real_save(tgt, data)  # crash after the settings write, before anything else
        raise RuntimeError("simulated crash")

    deploy.save_settings = failing_save
    args = deploy.build_parser().parse_args(["install", "--target", str(target), "--source", str(pack), "--fable", "yes"])
    with pytest.raises(RuntimeError):
        deploy.install_cmd(args)
    assert manifest(target)["settings"] == {"managed_agent_key": True, "previous_agent": None}
    r = run(pack, target, "uninstall", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    if (target / "settings.json").exists():
        assert "agent" not in settings(target)
    assert not (target / MANIFEST).exists()


@pytest.mark.parametrize("write_first", [True, False])
def test_release_write_failure_leaves_agent_revertible(pack, target, write_first):
    assert run(pack, target, "install").returncode == 0
    deploy = load_deploy()
    real_save = deploy.save_settings

    def failing_save(tgt, data):
        if write_first:
            real_save(tgt, data)
        raise RuntimeError("simulated crash")

    deploy.save_settings = failing_save
    args = deploy.build_parser().parse_args(
        ["install", "--target", str(target), "--source", str(pack), "--no-default-agent", "--fable", "yes"])
    with pytest.raises(RuntimeError):
        deploy.install_cmd(args)
    r = run(pack, target, "uninstall", "--yes")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "agent" not in settings(target)


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

def fake_claude(target: Path, stdout: str, code: int = 0) -> None:
    """Put a `claude` on the isolated PATH that prints `stdout` and exits `code` for any arguments."""
    bin_dir = target.parent / "bin"
    bin_dir.mkdir(exist_ok=True)
    exe = bin_dir / "claude"
    exe.write_text("#!%s\nimport sys\nsys.stdout.write(%r)\nsys.exit(%d)\n" % (sys.executable, stdout, code))
    exe.chmod(exe.stat().st_mode | stat.S_IXUSR)


@pytest.fixture
def fable_pack(pack: Path) -> Path:
    (pack / "agents" / "planner.md").write_text(
        "---\nname: planner\ndescription: The planner agent.\nmodel: fable\neffort: xhigh\n---\n\n"
        "Dispatch `critic` (`model: fable`, domain `plan`).\nCritic runs on Fable.\n")
    return pack


def test_fable_off_rewrites_agents(fable_pack, target):
    r = run(fable_pack, target, "install", "--fable", "no")
    assert r.returncode == 0, r.stdout + r.stderr
    planner = (target / "agents" / "planner.md").read_text()
    assert "\nmodel: opus\neffort: xhigh\n" in planner
    assert "`model: opus`" in planner and "Critic runs on Fable." in planner
    assert "model: fable" not in "".join(p.read_text() for p in (target / "agents").iterdir())
    for key in ("agents/helper.md", "skills/demo/SKILL.md", "skills/demo/scripts/run.sh"):
        assert (target / key).read_bytes() == (fable_pack / key).read_bytes()
    assert manifest(target)["fable"] == {"enabled": False, "reason": "--fable no"}
    assert "Fable: off" in r.stdout


def test_fable_yes_is_verbatim(fable_pack, target):
    r = run(fable_pack, target, "install", "--fable", "yes")
    assert r.returncode == 0, r.stdout + r.stderr
    for key in manifest(target)["files"]:
        assert (target / key).read_bytes() == (fable_pack / key).read_bytes()
    assert manifest(target)["fable"]["enabled"] is True
    assert "Fable: on" in r.stdout


def test_fable_choice_persists(fable_pack, target):
    run(fable_pack, target, "install", "--fable", "no")
    r = run(fable_pack, target, "install")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "copied=0, updated=0" in r.stdout and "Fable: off" in r.stdout
    assert "model: opus" in (target / "agents" / "planner.md").read_text()
    assert manifest(target)["fable"]["enabled"] is False
    r = run(fable_pack, target, "status")
    assert "Fable: off" in r.stdout
    assert "outdated" not in r.stdout and "modified" not in r.stdout
    rows = [l for l in r.stdout.splitlines() if l.startswith("  ")]
    assert rows and all(l.endswith("ok") for l in rows)


def test_fable_switch_updates(fable_pack, target):
    run(fable_pack, target, "install", "--fable", "no")
    r = run(fable_pack, target, "install", "--fable", "yes")
    assert "updated=1" in r.stdout
    assert (target / "agents" / "planner.md").read_bytes() == (fable_pack / "agents" / "planner.md").read_bytes()
    r = run(fable_pack, target, "install", "--fable", "no")
    assert "updated=1" in r.stdout
    assert "model: opus" in (target / "agents" / "planner.md").read_text()


def test_fable_auto_without_claude(fable_pack, target):
    r = run(fable_pack, target, "install")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Fable: off" in r.stdout and "claude CLI not found" in r.stdout
    assert "model: opus" in (target / "agents" / "planner.md").read_text()


def auth_json(**fields) -> str:
    return json.dumps(dict({"apiProvider": "firstParty", "authMethod": "claude.ai", "configDirectory": "@CFG@"}, **fields))


@pytest.mark.parametrize("stdout, code, seat, expect_on, expect_substring", [
    (auth_json(subscriptionType="max"), 0, None, True, "subscriptionType=max"),
    (auth_json(subscriptionType="pro"), 0, None, False, "subscriptionType=pro"),
    (auth_json(subscriptionType="free"), 0, None, False, "subscriptionType=free"),
    (auth_json(subscriptionType="max", apiProvider="bedrock"), 0, None, False, "apiProvider=bedrock"),
    (auth_json(subscriptionType="max", authMethod="api_key"), 0, None, False, "defaulted to opus"),
    (auth_json(subscriptionType="team"), 0, "team_labs_premium", True, "seatTier=team_labs_premium"),
    (auth_json(subscriptionType="enterprise"), 0, "enterprise_premium", True, "seatTier=enterprise_premium"),
    (auth_json(subscriptionType="team"), 0, "team_standard", False, "seatTier=team_standard"),
    (auth_json(subscriptionType="team"), 0, None, False, "defaulted to opus"),
    ("", 1, None, False, "exited 1"),
    ("not json", 0, None, False, "no JSON"),
    ("[1, 2]", 0, None, False, "no JSON"),
    (auth_json(subscriptionType="whatever"), 0, None, False, "not recognized"),
    (auth_json(), 0, None, False, "not recognized"),
])
def test_fable_auto_detection(fable_pack, target, stdout, code, seat, expect_on, expect_substring):
    cfg = target.parent / "cfg"
    if seat is not None:
        cfg.mkdir()
        (cfg / ".claude.json").write_text(json.dumps({"oauthAccount": {"seatTier": seat}}))
    fake_claude(target, stdout.replace("@CFG@", str(cfg)), code)
    r = run(fable_pack, target, "install")
    assert r.returncode == 0, r.stdout + r.stderr
    planner = (target / "agents" / "planner.md").read_text()
    assert ("model: fable" in planner) == expect_on and ("model: opus" in planner) == (not expect_on)
    rec = manifest(target)["fable"]
    assert rec["enabled"] is expect_on
    assert expect_substring in rec["reason"] and expect_substring in r.stdout
    assert ("Fable: on" if expect_on else "Fable: off") in r.stdout


def test_fable_auto_reads_seat_tier_from_home(fable_pack, target):
    (target.parent / ".claude.json").write_text(json.dumps({"oauthAccount": {"seatTier": "team_labs_premium"}}))
    fake_claude(target, auth_json(subscriptionType="team", configDirectory=str(target.parent / ".claude")))
    r = run(fable_pack, target, "install")
    assert "Fable: on" in r.stdout and manifest(target)["fable"]["enabled"] is True


def test_fable_explicit_auto_rediscovers(fable_pack, target):
    run(fable_pack, target, "install", "--fable", "no")
    fake_claude(target, auth_json(subscriptionType="max"))
    r = run(fable_pack, target, "install", "--fable", "auto")
    assert "Fable: on" in r.stdout and "updated=1" in r.stdout
    assert (target / "agents" / "planner.md").read_bytes() == (fable_pack / "agents" / "planner.md").read_bytes()


def test_fable_old_manifest_not_recorded(fable_pack, target):
    run(fable_pack, target, "install", "--fable", "yes")
    m = manifest(target)
    del m["fable"]
    (target / MANIFEST).write_text(json.dumps(m))
    r = run(fable_pack, target, "status")
    assert "Fable: not recorded" in r.stdout
    rows = [l for l in r.stdout.splitlines() if l.startswith("  ")]
    assert rows and all(l.endswith("ok") for l in rows)
    r = run(fable_pack, target, "install")
    assert "Fable: off" in r.stdout and "updated=1" in r.stdout
    assert manifest(target)["fable"]["enabled"] is False


class TtyInput(io.StringIO):
    def isatty(self):
        return True


class NoRead(TtyInput):
    def readline(self, *a):
        raise AssertionError("stdin was read")


def install_in_process(monkeypatch, pack, target, stdin, *extra):
    deploy = load_deploy()
    monkeypatch.setattr(deploy, "detect_fable", lambda: (None, "authMethod=api_key"))
    monkeypatch.setattr(sys, "stdin", stdin)
    args = deploy.build_parser().parse_args(
        ["install", "--target", str(target), "--source", str(pack), "--fable", "auto"] + list(extra))
    assert deploy.install_cmd(args) == 0
    return manifest(target)["fable"]


@pytest.mark.parametrize("answer, expect_on", [("y\n", True), ("yes\n", True), ("\n", False), ("n\n", False)])
def test_fable_prompt_when_unclear(monkeypatch, fable_pack, target, answer, expect_on):
    rec = install_in_process(monkeypatch, fable_pack, target, TtyInput(answer))
    assert rec["enabled"] is expect_on
    assert rec["reason"].startswith("asked:")


def test_fable_prompt_skipped_with_yes(monkeypatch, fable_pack, target):
    rec = install_in_process(monkeypatch, fable_pack, target, NoRead(), "--yes")
    assert rec["enabled"] is False and "defaulted to opus" in rec["reason"]


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
def legacy_install(pack, target):
    """An install whose manifest and lock carry the pre-rebrand names."""
    assert run(pack, target, "install", "--fable", "no").returncode == 0
    (target / MANIFEST).rename(target / LEGACY_MANIFEST)
    (target / ".claude-agents.lock").write_text("")
    return target


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
    assert after["fable"]["enabled"] is False  # saved choice survived, not re-detected


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
