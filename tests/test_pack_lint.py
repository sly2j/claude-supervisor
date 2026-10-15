"""Lint the real pack/ directory: frontmatter, names, models, tool rules, skill refs."""

import importlib.machinery
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PACK = ROOT / "pack"
AGENTS = sorted((PACK / "agents").glob("*.md")) if (PACK / "agents").is_dir() else []
SKILL_DIRS = sorted(p for p in (PACK / "skills").iterdir() if p.is_dir()) if (PACK / "skills").is_dir() else []

pytestmark = pytest.mark.skipif(not PACK.is_dir(), reason="pack/ does not exist yet")

MODELS = {"fable", "opus", "sonnet", "haiku", "inherit"}
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
NO_AGENT_TOOL = {"critic", "scope-critic", "quick-edit", "git-ops", "scout"}
BANNED = ("opencode", "argo/", "~/.config/opencode")


def _load_deploy():
    loader = importlib.machinery.SourceFileLoader("deploy_script", str(ROOT / "scripts" / "deploy"))
    spec = importlib.util.spec_from_loader("deploy_script", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


deploy = _load_deploy()


def frontmatter(path: Path) -> dict:
    fm = deploy.parse_frontmatter(path.read_text(encoding="utf-8"))
    assert fm is not None, "%s: missing --- frontmatter" % path
    return fm


def tool_names(value) -> list:
    """Tool names without the (...) argument part, e.g. Agent(a, b) -> Agent."""
    text = ", ".join(value) if isinstance(value, list) else str(value or "")
    text = re.sub(r"\([^)]*\)", "", text)
    return [t.strip() for t in text.split(",") if t.strip()]


def tier_table() -> dict:
    """Map agent name -> (model, effort) from the Tiers table in agent-authoring/SKILL.md."""
    text = (PACK / "skills" / "agent-authoring" / "SKILL.md").read_text(encoding="utf-8")
    section = text.split("## Tiers", 1)[1].split("\n## ", 1)[0]
    rows = [l for l in section.splitlines() if l.startswith("|")][2:]  # skip header and separator
    tiers = {}
    for row in rows:
        _tier, agents, model_effort, _tools = [c.strip() for c in row.strip("|").split("|")]
        model, effort = [x.strip() for x in model_effort.split("/")]
        for name in agents.split(","):
            tiers[name.strip()] = (model, effort)
    return tiers


def test_pack_has_content():
    assert AGENTS, "no agents in pack/agents"
    assert SKILL_DIRS, "no skills in pack/skills"


@pytest.mark.parametrize("path", AGENTS, ids=lambda p: p.stem)
def test_agent_frontmatter(path):
    fm = frontmatter(path)
    assert fm.get("name") == path.stem
    assert str(fm.get("description") or "").strip(), "description empty"
    model = str(fm.get("model") or "")
    assert model in MODELS or model.startswith("claude-"), "bad model %r" % model
    if "effort" in fm:
        assert fm["effort"] in EFFORTS, "bad effort %r" % fm["effort"]


@pytest.mark.parametrize("path", AGENTS, ids=lambda p: p.stem)
def test_agent_matches_tier_table(path):
    tiers = tier_table()
    assert path.stem in tiers, "%s missing from the Tiers table in agent-authoring/SKILL.md" % path.stem
    fm = frontmatter(path)
    assert (fm.get("model"), fm.get("effort")) == tiers[path.stem], \
        "%s: frontmatter %s / %s != Tiers table %s / %s" % (
            (path.stem, fm.get("model"), fm.get("effort")) + tiers[path.stem])


@pytest.mark.parametrize("path", AGENTS, ids=lambda p: p.stem)
def test_leaf_agents_cannot_spawn(path):
    name = path.stem
    if not (name.endswith("-worker") or name in NO_AGENT_TOOL):
        pytest.skip("not a leaf agent")
    fm = frontmatter(path)
    tools = tool_names(fm.get("tools"))
    disallowed = tool_names(fm.get("disallowedTools"))
    assert "Agent" not in tools, "%s must not have Agent in tools" % name
    assert "Agent" in disallowed or tools, \
        "%s must list Agent in disallowedTools or use a tools allowlist" % name


@pytest.mark.parametrize("path", AGENTS, ids=lambda p: p.stem)
def test_agent_skill_refs_exist(path):
    fm = frontmatter(path)
    known = {p.name for p in SKILL_DIRS}
    missing = [s for s in deploy.as_list(fm.get("skills")) if s not in known]
    assert not missing, "unknown skills: %s" % missing


@pytest.mark.parametrize("skill", SKILL_DIRS, ids=lambda p: p.name)
def test_skill(skill):
    skill_md = skill / "SKILL.md"
    assert skill_md.is_file(), "missing SKILL.md"
    fm = frontmatter(skill_md)
    assert fm.get("name") == skill.name
    assert str(fm.get("description") or "").strip()
    n = len(skill_md.read_text(encoding="utf-8").splitlines())
    assert n <= 300, "SKILL.md has %d lines (agent-authoring: keep each skill under about 300)" % n


def test_no_opencode_leftovers():
    hits = []
    for p in PACK.rglob("*"):
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        hits += ["%s: %s" % (p.relative_to(ROOT), b) for b in BANNED if b in text]
    assert not hits, "\n".join(hits)


@pytest.mark.parametrize("path", AGENTS, ids=lambda p: p.stem)
def test_fable_rewrite_covers_pack(path):
    key = "agents/" + path.name
    assert deploy.deployed_bytes(key, path, True) == path.read_bytes()
    source_fm = frontmatter(path)
    text = deploy.deployed_bytes(key, path, False).decode("utf-8")
    assert "model: fable" not in text
    fm = deploy.parse_frontmatter(text)
    expected = "opus" if source_fm.get("model") == "fable" else source_fm.get("model")
    assert fm.get("model") == expected
    assert fm.get("effort") == source_fm.get("effort")
