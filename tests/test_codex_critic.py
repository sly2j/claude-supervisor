"""Tests for the codex-critic script (pack/skills/supervisor-config/scripts/codex-critic).

Real Codex is never called: a stub `codex` on a private PATH records argv and stdin.
Stub protocol (files under tmp/stub): login_rc (rc of `login status`, prints
"Logged in using ChatGPT" when 0), out.txt (copied to the -o path on `exec`), rc (exit code of
`exec`), sleep (optional seconds to sleep before answering `exec`). Recorded: codex.argv (one
line per argument, `exec` calls only), codex.stdin (stdin of the last `exec` call).
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_SRC = ROOT / "pack" / "skills" / "supervisor-config" / "scripts" / "codex-critic"
ENV_WHITELIST = ("TMPDIR", "LANG", "LC_ALL")

STUB = """#!/bin/sh
D='%(stub)s'
if [ "$1" = login ]; then
  rc=$(cat "$D/login_rc" 2>/dev/null || echo 0)
  [ "$rc" = 0 ] && echo 'Logged in using ChatGPT' >&2
  exit "$rc"
fi
printf '%%s\\n' "$@" > "$D/codex.argv"
cat > "$D/codex.stdin"
out=
prev=
for a in "$@"; do
  [ "$prev" = -o ] && out=$a
  prev=$a
done
[ -f "$D/sleep" ] && sleep "$(cat "$D/sleep")"
[ -n "$out" ] && [ -f "$D/out.txt" ] && cp "$D/out.txt" "$out"
exit "$(cat "$D/rc" 2>/dev/null || echo 0)"
"""


@pytest.fixture
def cfg(tmp_path: Path) -> Path:
    c = tmp_path / "cfg"
    script = c / "skills" / "supervisor-config" / "scripts" / "codex-critic"
    script.parent.mkdir(parents=True)
    shutil.copy2(str(SCRIPT_SRC), str(script))
    (c / "agents").mkdir()
    (c / "agents" / "critic.md").write_text("---\nname: critic\n---\nYou are the critic.\n")
    for sk in ("plan-writing", "agent-authoring", "science-writing-style", "presentation-style"):
        (c / "skills" / sk).mkdir()
        (c / "skills" / sk / "SKILL.md").write_text("---\nname: %s\n---\nRules.\n" % sk)
    ref = c / "skills" / "project-memory" / "references"
    ref.mkdir(parents=True)
    (ref / "writing.md").write_text("WRITING-MD-TEXT\n")
    return c


@pytest.fixture
def codex_stub(tmp_path: Path) -> Path:
    """Install the stub as tmp/bin/codex; returns tmp/stub."""
    bin_dir, stub = tmp_path / "bin", tmp_path / "stub"
    bin_dir.mkdir()
    stub.mkdir()
    (stub / "login_rc").write_text("0")
    (stub / "rc").write_text("0")
    exe = bin_dir / "codex"
    exe.write_text(STUB % {"stub": stub})
    exe.chmod(0o755)
    return stub


def script_of(cfg: Path) -> Path:
    return cfg / "skills" / "supervisor-config" / "scripts" / "codex-critic"


def run(cfg: Path, *args: str, cwd=None, timeout=60) -> subprocess.CompletedProcess:
    """Run the installed script with a whitelisted env; the real codex is not on PATH."""
    env = {k: os.environ[k] for k in ENV_WHITELIST if k in os.environ}
    env["PATH"] = "%s:/bin:/usr/bin" % (cfg.parent / "bin")
    env["HOME"] = str(cfg.parent)
    return subprocess.run([sys.executable, str(script_of(cfg))] + list(args), capture_output=True,
                          text=True, env=env, timeout=timeout, stdin=subprocess.DEVNULL,
                          cwd=str(cwd or cfg.parent))


def rule(cfg: Path) -> str:
    return "Bash(%s review *)" % script_of(cfg)


def test_enable_writes_mode_only(cfg, codex_stub):
    before = json.dumps({"model": "x", "permissions": {"deny": ["a"], "allow": [rule(cfg)]}})
    (cfg / "settings.json").write_text(before)
    r = run(cfg, "enable", "--yes")
    assert r.returncode == 0, r.stderr
    assert "Codex as critic (Supervisor for Claude):" in r.stdout
    assert "sent to OpenAI." in r.stdout
    assert "permissions.allow" not in r.stdout
    assert str(cfg / "supervisor-config.json") in r.stdout
    assert json.loads((cfg / "supervisor-config.json").read_text()) == {
        "critic": {"backend": "codex", "model": "gpt-6.1-sol", "effort": "high"}}
    assert (cfg / "settings.json").read_text() == before
    assert not (cfg / "settings.json.bak").exists()


def test_enable_model_arg(cfg, codex_stub):
    assert run(cfg, "enable", "gpt-6-astra", "--yes").returncode == 0
    critic = json.loads((cfg / "supervisor-config.json").read_text())["critic"]
    assert critic["model"] == "gpt-6-astra" and critic["effort"] == "high"


def test_enable_keeps_domains(cfg, codex_stub):
    domains = {"prose": "claude", "plan": {"model": "gpt-6-astra", "effort": "xhigh"}}
    (cfg / "supervisor-config.json").write_text(json.dumps({"other": 1, "critic": {"domains": domains}}))
    assert run(cfg, "enable", "--yes").returncode == 0
    assert run(cfg, "enable", "--yes").returncode == 0
    data = json.loads((cfg / "supervisor-config.json").read_text())
    assert data["critic"]["domains"] == domains and data["other"] == 1


def test_enable_requires_yes_off_tty(cfg, codex_stub):
    r = run(cfg, "enable")
    assert r.returncode == 2
    assert "--yes" in r.stderr
    assert not (cfg / "supervisor-config.json").exists()
    assert not (cfg / "settings.json").exists()


def test_enable_refuses_missing_binary(cfg, tmp_path):
    (tmp_path / "bin").mkdir()
    r = run(cfg, "enable", "--yes")
    assert r.returncode == 1
    assert "codex" in r.stderr
    assert not (cfg / "supervisor-config.json").exists()
    assert not (cfg / "settings.json").exists()


def test_enable_refuses_logged_out(cfg, codex_stub):
    (codex_stub / "login_rc").write_text("1")
    r = run(cfg, "enable", "--yes")
    assert r.returncode == 1
    assert "login" in r.stderr
    assert not (cfg / "supervisor-config.json").exists()
    assert not (cfg / "settings.json").exists()


def test_disable_removes_mode_only(cfg, codex_stub):
    before = json.dumps({"model": "x", "permissions": {"allow": ["Bash(ls)", rule(cfg)]}})
    (cfg / "settings.json").write_text(before)
    assert run(cfg, "enable", "--yes").returncode == 0
    r = run(cfg, "disable", "--yes")
    assert r.returncode == 0, r.stderr
    assert not (cfg / "supervisor-config.json").exists()
    assert (cfg / "settings.json").read_text() == before


def test_disable_idempotent(cfg, codex_stub):
    r = run(cfg, "disable")
    assert r.returncode == 0
    assert not (cfg / "settings.json").exists()
    assert run(cfg, "disable", "--yes").returncode == 0


def test_status_off(cfg, codex_stub):
    r = run(cfg, "status")
    assert r.returncode == 0
    assert "backend: claude" in r.stdout
    assert "auth: logged in" in r.stdout
    assert "rule: %s" % rule(cfg) in r.stdout
    assert "rule present: no" in r.stdout
    assert not (cfg / "settings.json").exists()


def test_status_on(cfg, codex_stub):
    (cfg / "settings.json").write_text(json.dumps({"permissions": {"allow": [rule(cfg)]}}))
    (cfg / "supervisor-config.json").write_text(json.dumps(
        {"critic": {"backend": "codex", "model": "m1", "effort": "high", "domains": {"prose": "claude"}}}))
    assert run(cfg, "enable", "m2", "--yes").returncode == 0
    r = run(cfg, "status")
    for line in ("backend: codex", "model: m2", "effort: high", 'domains: {"prose": "claude"}',
                 "auth: logged in", "rule present: yes",
                 "mode file: %s" % (cfg / "supervisor-config.json")):
        assert line in r.stdout


def test_status_without_binary(cfg, tmp_path):
    (tmp_path / "bin").mkdir()
    r = run(cfg, "status")
    assert "codex: not found" in r.stdout and "auth: n/a" in r.stdout


VALID = """VERDICT: REVISE
ROUND: 1

| ID | Severity | Location | Finding | Evidence | Minimal fix |
|----|----------|----------|---------|----------|-------------|
| C1 | BLOCKING | a.py:1 | bad `x | y` use | quote | fix it |
| C2 | NIT | a.py:2 | style | quote | rename |

VALIDATION: none available
NOTES: covered a.py
"""
PASS_EMPTY = """VERDICT: PASS
ROUND: 1

| ID | Severity | Location | Finding | Evidence | Minimal fix |
|----|----------|----------|---------|----------|-------------|

VALIDATION: none available
NOTES: nothing found
"""


@pytest.fixture
def work(tmp_path: Path) -> Path:
    w = tmp_path / "work"
    w.mkdir()
    (w / "brief.md").write_text("BRIEF-TEXT\n")
    return w


def enable_codex(cfg: Path, **extra) -> None:
    critic = {"backend": "codex", "model": "gpt-6.1-sol", "effort": "high"}
    critic.update(extra)
    (cfg / "supervisor-config.json").write_text(json.dumps({"critic": critic}))


def review(cfg, work, *extra, domain="code", round_no="1", timeout=60):
    return run(cfg, "review", "--domain", domain, "--round", round_no,
               "--brief", str(work / "brief.md"), *extra, cwd=work, timeout=timeout)


def argv_of(stub: Path) -> list:
    return (stub / "codex.argv").read_text().splitlines()


def assert_fallback(r, *words):
    assert r.returncode == 0 and r.stdout.strip() == "NO_CODEX", (r.stdout, r.stderr)
    assert "codex-critic:" in r.stderr
    for w in words:
        assert w in r.stderr


def test_review_no_mode_file(cfg, codex_stub, work):
    assert_fallback(review(cfg, work))
    assert not (codex_stub / "codex.argv").exists()


def test_review_malformed_mode_file(cfg, codex_stub, work):
    (cfg / "supervisor-config.json").write_text('{"critic": {"backend": "codex"')
    assert_fallback(review(cfg, work))
    assert not (codex_stub / "codex.argv").exists()


def test_review_backend_claude(cfg, codex_stub, work):
    (cfg / "supervisor-config.json").write_text(json.dumps({"critic": {"backend": "claude"}}))
    assert_fallback(review(cfg, work))
    assert not (codex_stub / "codex.argv").exists()


def test_review_domain_pinned(cfg, codex_stub, work):
    enable_codex(cfg, domains={"prose": "claude"})
    assert_fallback(review(cfg, work, domain="prose"), "prose")
    assert not (codex_stub / "codex.argv").exists()


def test_review_missing_binary(cfg, tmp_path, work):
    (tmp_path / "bin").mkdir()
    enable_codex(cfg)
    assert_fallback(review(cfg, work), "codex binary")


def test_review_missing_critic_md(cfg, codex_stub, work):
    enable_codex(cfg)
    (cfg / "agents" / "critic.md").unlink()
    assert_fallback(review(cfg, work), "critic.md")
    assert not (codex_stub / "codex.argv").exists()


def test_review_never_checks_login(cfg, codex_stub, work):
    enable_codex(cfg)
    (codex_stub / "login_rc").write_text("1")
    (codex_stub / "out.txt").write_text(VALID)
    r = review(cfg, work)
    assert r.returncode == 0 and r.stdout.startswith("VERDICT: REVISE")


def test_review_nonzero_rc(cfg, codex_stub, work):
    enable_codex(cfg)
    (codex_stub / "rc").write_text("3")
    (codex_stub / "out.txt").write_text(VALID)
    r = review(cfg, work)
    assert_fallback(r, "exited 3")
    assert list(work.iterdir()) == [work / "brief.md"]


def test_review_empty_output(cfg, codex_stub, work):
    enable_codex(cfg)
    (codex_stub / "out.txt").write_text("  \n")
    assert_fallback(review(cfg, work), "no output")
    (codex_stub / "out.txt").unlink()
    assert_fallback(review(cfg, work), "no output")
    assert list(work.iterdir()) == [work / "brief.md"]


@pytest.mark.parametrize("text,why", [
    ("just prose\n", "line 1"),
    ("VERDICT: PASS\nnope\n", "line 2"),
    (VALID.replace("ROUND: 1", "ROUND: 2"), "ROUND"),
    (VALID.replace("| ID | Severity", "| Id | Sev"), "header"),
    (VALID.replace("NOTES:", "NOTE:"), "NOTES"),
    (VALID + "NOTES: twice\n", "NOTES"),
    (VALID.replace("| fix it |", "| fix | it | extra |"), "cells"),
    (VALID.replace("| NIT |", "| MINOR |"), "severity"),
])
def test_review_malformed_block(cfg, codex_stub, work, text, why):
    enable_codex(cfg)
    (codex_stub / "out.txt").write_text(text)
    r = review(cfg, work)
    assert_fallback(r, "validation")
    assert why in r.stderr
    assert list(work.iterdir()) == [work / "brief.md"]


def test_review_verdict_disagrees_with_rows(cfg, codex_stub, work):
    enable_codex(cfg)
    (codex_stub / "out.txt").write_text(VALID.replace("VERDICT: REVISE", "VERDICT: PASS"))
    assert_fallback(review(cfg, work), "disagrees")
    (codex_stub / "out.txt").write_text(VALID.replace("BLOCKING", "SHOULD"))
    assert_fallback(review(cfg, work), "disagrees")


def test_review_timeout(cfg, codex_stub, work):
    enable_codex(cfg)
    (codex_stub / "sleep").write_text("30")
    (codex_stub / "out.txt").write_text(VALID)
    r = review(cfg, work, "--timeout", "1", timeout=20)
    assert_fallback(r, "timed out")
    assert list(work.iterdir()) == [work / "brief.md"]


def test_review_valid_block(cfg, codex_stub, work, tmp_path):
    enable_codex(cfg)
    (codex_stub / "out.txt").write_text(VALID)
    r = review(cfg, work, "pack/a.py")
    assert r.returncode == 0, r.stderr
    assert r.stdout == VALID.strip() + "\nbackend: codex gpt-6.1-sol high\n"
    argv = argv_of(codex_stub)
    assert argv[0] == "exec"
    for flag in ("-s", "read-only", "--ephemeral", "--ignore-user-config", "--skip-git-repo-check",
                 "--color", "never", "-m", "gpt-6.1-sol", "model_reasoning_effort=high",
                 'project_doc_fallback_filenames=["CLAUDE.md"]', "-"):
        assert flag in argv
    assert argv[argv.index("-C") + 1] == str(work.resolve())
    assert argv[-1] == "-" and argv[-3] == "-o"
    assert argv.count("-c") == 2
    assert not os.path.exists(argv[-2])
    assert "- pack/a.py" in (codex_stub / "codex.stdin").read_text()


def test_review_zero_finding_pass(cfg, codex_stub, work):
    enable_codex(cfg)
    (codex_stub / "out.txt").write_text(PASS_EMPTY)
    r = review(cfg, work)
    assert r.stdout.startswith("VERDICT: PASS") and r.stdout.endswith("high\n")


def test_review_fenced_block_unwrapped(cfg, codex_stub, work):
    enable_codex(cfg)
    (codex_stub / "out.txt").write_text("```markdown\n" + VALID + "```\n")
    r = review(cfg, work)
    assert r.returncode == 0, r.stderr
    assert r.stdout == VALID.strip() + "\nbackend: codex gpt-6.1-sol high\n"


def test_review_prompt_contents(cfg, codex_stub, work):
    enable_codex(cfg)
    (codex_stub / "out.txt").write_text(VALID)
    (work / "REVIEW.md").write_text("REVIEW-RULES\n")
    (work / "d.diff").write_text("+DIFF-LINE\n")
    review(cfg, work, "--diff", str(work / "d.diff"), domain="plan", round_no="1")
    p = (codex_stub / "codex.stdin").read_text()
    assert "Domain: plan" in p and "Round: 1" in p and "running under Codex" in p
    assert "name: critic" not in p and "name: plan-writing" not in p
    order = [p.index(x) for x in ("running under Codex", "You are the critic.", "REVIEW-RULES",
                                  "Rules.", "## Diff", "+DIFF-LINE", "## Brief", "BRIEF-TEXT")]
    assert order == sorted(order)
    assert "science-writing-style" not in p


def test_review_prompt_pytest_and_absent_review_md(cfg, codex_stub, work):
    enable_codex(cfg)
    (codex_stub / "out.txt").write_text(VALID)
    review(cfg, work)
    p = (codex_stub / "codex.stdin").read_text()
    assert "PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider" in p
    assert "tests were not independently run" in p
    assert "## REVIEW.md" not in p and "project rule files that do not exist" in p
    (work / "REVIEW.md").write_text("REVIEW-RULES\n")
    review(cfg, work)
    p = (codex_stub / "codex.stdin").read_text()
    assert "## REVIEW.md" in p and "project rule files that do not exist" not in p


def test_review_missing_domain_skill_skipped(cfg, codex_stub, work):
    enable_codex(cfg)
    (codex_stub / "out.txt").write_text(VALID)
    shutil.rmtree(str(cfg / "skills" / "plan-writing"))
    r = review(cfg, work, domain="plan")
    assert r.stdout.startswith("VERDICT:")


def test_review_prose_includes_writing_md(cfg, codex_stub, work):
    enable_codex(cfg)
    (codex_stub / "out.txt").write_text(VALID)
    review(cfg, work, domain="prose")
    p = (codex_stub / "codex.stdin").read_text()
    assert "science-writing-style" in p and "presentation-style" in p
    assert "WRITING-MD-TEXT" not in p
    (work / ".supervisor").mkdir()
    review(cfg, work, domain="prose")
    assert "WRITING-MD-TEXT" in (codex_stub / "codex.stdin").read_text()


def test_review_domain_override(cfg, codex_stub, work):
    enable_codex(cfg, domains={"plan": {"model": "gpt-6-astra", "effort": "xhigh"}})
    (codex_stub / "out.txt").write_text(VALID)
    r = review(cfg, work, domain="plan")
    argv = argv_of(codex_stub)
    assert argv[argv.index("-m") + 1] == "gpt-6-astra"
    assert "model_reasoning_effort=xhigh" in argv
    assert r.stdout.endswith("backend: codex gpt-6-astra xhigh\n")
    review(cfg, work, domain="code")
    assert argv_of(codex_stub)[argv_of(codex_stub).index("-m") + 1] == "gpt-6.1-sol"


def test_review_cwd_flag(cfg, codex_stub, work, tmp_path):
    enable_codex(cfg)
    (codex_stub / "out.txt").write_text(VALID)
    other = tmp_path / "other"
    other.mkdir()
    review(cfg, work, "--cwd", str(other))
    argv = argv_of(codex_stub)
    assert argv[argv.index("-C") + 1] == str(other)


def test_probe_claude_without_mode_file(cfg, codex_stub):
    r = run(cfg, "review", "--probe")
    assert r.returncode == 0 and r.stdout == "claude\n" and "backend is claude" in r.stderr
    assert not (codex_stub / "codex.argv").exists()


def test_probe_codex_engine(cfg, codex_stub):
    enable_codex(cfg, domains={"plan": {"model": "gpt-6-astra", "effort": "xhigh"}})
    assert run(cfg, "review", "--probe").stdout == "codex gpt-6.1-sol high\n"
    assert run(cfg, "review", "--probe", "--domain", "plan").stdout == "codex gpt-6-astra xhigh\n"


def test_probe_claude_when_codex_missing_or_logged_out(cfg, codex_stub, tmp_path):
    enable_codex(cfg)
    (codex_stub / "login_rc").write_text("1")
    r = run(cfg, "review", "--probe")
    assert r.stdout == "claude\n" and "not logged in" in r.stderr
    (tmp_path / "bin" / "codex").unlink()
    r = run(cfg, "review", "--probe")
    assert r.stdout == "claude\n" and "not on PATH" in r.stderr


def test_review_without_probe_needs_round_and_brief(cfg, codex_stub):
    r = run(cfg, "review", "--domain", "code")
    assert r.returncode == 2 and "--round, --brief" in r.stderr
