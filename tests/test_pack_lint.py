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
NO_AGENT_TOOL = {"critic", "scope-critic", "clerk", "git-ops", "scout", "curator"}
BANNED = ("opencode", "argo/", "~/.config/opencode")
BODY_WORD_CAPS = {
    "Main": 1030, "Lead": 700, "Review": 600, "Worker": 400, "Memory": 400, "Quick": 350,
}
SKILL_WORD_CAP = 1300
TIER_TOOLS = {  # agent -> (field, entries it must list), from the Tools column of the Tiers table
    "supervisor": ("disallowedTools", ["Bash"]),
    "critic": ("disallowedTools", ["Write", "Edit"]),
    "scope-critic": ("disallowedTools", ["Bash"]),
    **{lead: ("skills", ["lead-loop"]) for lead in ("researcher", "planner", "executor", "writer")},
}
LEAD_WORKERS = {
    "executor": ["executor-worker"],
    "researcher": ["researcher-worker"],
    "planner": ["planner-worker"],
    "writer": ["writer-worker"],
}


def _load_deploy():
    loader = importlib.machinery.SourceFileLoader("deploy_script", str(ROOT / "deploy"))
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


def _tier_rows() -> dict:
    """Map agent name -> (tier, model, effort) from the Tiers table in agent-authoring/SKILL.md."""
    text = (PACK / "skills" / "agent-authoring" / "SKILL.md").read_text(encoding="utf-8")
    section = text.split("## Tiers", 1)[1].split("\n## ", 1)[0]
    rows = [l for l in section.splitlines() if l.startswith("|")][2:]  # skip header and separator
    tiers = {}
    for row in rows:
        tier, agents, model_effort, _tools = [c.strip() for c in row.strip("|").split("|")]
        model, effort = [x.strip() for x in model_effort.split("/")]
        effort = None if effort == "default" else effort  # frontmatter omits effort
        for name in agents.split(","):
            tiers[name.strip()] = (tier, model, effort)
    return tiers


def tier_table() -> dict:
    """Map agent name -> (model, effort) from the Tiers table in agent-authoring/SKILL.md."""
    return {name: (model, effort) for name, (_tier, model, effort) in _tier_rows().items()}


def body_words(path: Path) -> int:
    """Word count of the text after the closing --- of the frontmatter."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if lines and lines[0] == "---":
        close = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == "---"), 0)
        text = "\n".join(lines[close + 1:])
    return len(text.split())


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


@pytest.mark.parametrize("name", sorted(TIER_TOOLS))
def test_agent_matches_tier_tools(name):
    field, required = TIER_TOOLS[name]
    have = deploy.as_list(frontmatter(PACK / "agents" / (name + ".md")).get(field))
    missing = [r for r in required if r not in tool_names(have)]
    assert not missing, "%s: %s must list %s" % (name, field, missing)


@pytest.mark.parametrize("path", AGENTS, ids=lambda p: p.stem)
def test_agent_body_word_cap(path):
    tier = _tier_rows().get(path.stem, (None,))[0]
    assert tier in BODY_WORD_CAPS, "%s: tier %r has no body word cap" % (path.stem, tier)
    n = body_words(path)
    assert n <= BODY_WORD_CAPS[tier], "%s: body has %d words, %s tier cap is %d" % (
        path.stem, n, tier, BODY_WORD_CAPS[tier])


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


@pytest.mark.parametrize("lead", sorted(LEAD_WORKERS))
def test_leads_name_worker_subagent_type(lead):
    """Leads must pass subagent_type explicitly, or the Agent tool starts general-purpose."""
    text = (PACK / "agents" / (lead + ".md")).read_text(encoding="utf-8")
    missing = [w for w in LEAD_WORKERS[lead] if 'subagent_type: "%s"' % w not in text]
    assert not missing, "%s must dispatch with subagent_type: %s" % (lead, missing)


@pytest.mark.parametrize("lead", sorted(LEAD_WORKERS))
def test_leads_dispatch_only_own_workers(lead):
    """A lead dispatches only its own worker, critic, and scope-critic."""
    text = (PACK / "agents" / (lead + ".md")).read_text(encoding="utf-8")
    extra = set(re.findall(r'subagent_type: "([^"]+)"', text)) - set(LEAD_WORKERS[lead]) - {"critic", "scope-critic"}
    assert not extra, "%s must not dispatch %s" % (lead, sorted(extra))


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
    assert n <= 300, "SKILL.md has %d lines (agent-authoring: keep each skill under 300)" % n
    words = body_words(skill_md)
    assert words <= SKILL_WORD_CAP, "SKILL.md body has %d words, cap is %d" % (words, SKILL_WORD_CAP)


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


def test_memory_templates():
    """The memory templates carry exactly the documented frontmatter keys."""
    templates = PACK / "skills" / "project-memory" / "templates"
    entry = frontmatter(templates / "entry.md")
    assert set(entry) == {"domain", "summary", "affects", "verified", "source", "supersedes"}
    assert set(frontmatter(templates / "draft-state.md")) == {"file"}
    readme = templates / "store-readme.md"
    assert readme.is_file() and not readme.read_text(encoding="utf-8").startswith("---")


MAX_LINE = 100


@pytest.mark.parametrize("path", sorted(PACK.rglob("*.md")), ids=lambda p: str(p.relative_to(PACK)))
def test_body_line_length(path):
    """Body lines stay within MAX_LINE; only table rows and fenced code lines are exempt."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0] == "---":
        close = next((i for i, l in enumerate(lines[1:], 1) if l == "---"), 0)
        lines = [""] * (close + 1) + lines[close + 1:]  # keep line numbers
    long, fenced = [], False
    for n, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            fenced = not fenced
        elif not fenced and not stripped.startswith("|") and len(line) > MAX_LINE:
            long.append("%s:%d (%d)" % (path.relative_to(ROOT), n, len(line)))
    assert not long, "lines over %d chars:\n%s" % (MAX_LINE, "\n".join(long))


@pytest.mark.parametrize("name", ["curator", "clerk"])
def test_memory_agents_never_commit(name):
    text = (PACK / "agents" / ("%s.md" % name)).read_text(encoding="utf-8")
    assert "git commit" not in text, "%s must not run git commit; git-ops commits" % name
    assert "never commit" in text.lower(), "%s must state it never commits" % name


def test_curator_procedures_have_no_git_commit():
    path = PACK / "skills" / "project-memory" / "references" / "curator-procedures.md"
    assert "git commit" not in path.read_text(encoding="utf-8")


def test_git_ops_loads_git_safety():
    skills = frontmatter(PACK / "agents" / "git-ops.md").get("skills") or []
    assert {"git-safety", "repo-workflow"} <= set(skills)


@pytest.mark.parametrize("rel", ["skills/repo-workflow/SKILL.md", "agents/git-ops.md"])
def test_default_branch_syncs_with_origin(rel):
    """Agents that land on the default branch first rebase onto origin (user decision 2026-10-23)."""
    text = (PACK / rel).read_text(encoding="utf-8")
    assert "git fetch origin" in text and "pull --rebase" in text, rel
    assert "`origin` first" in text, "%s must push to origin before other remotes" % rel


@pytest.mark.parametrize("rel", [
    "skills/git-safety/SKILL.md", "skills/repo-workflow/SKILL.md",
    "agents/git-ops.md", "agents/executor.md", "agents/supervisor.md",
])
def test_attribution_ignores_harness_reminders(rel):
    text = " ".join((PACK / rel).read_text(encoding="utf-8").lower().split())
    assert "harness attribution reminders" in text, rel
    if rel == "skills/git-safety/SKILL.md":
        assert "claude-session" in text
