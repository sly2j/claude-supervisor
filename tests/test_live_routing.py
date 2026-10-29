"""Live routing check: ask the deployed supervisor to route canonical requests.

Opt-in, because every case calls the model (about 14 calls, a few cents to tens of cents each; the
total is printed at the end). Runs only with SUPERVISOR_LIVE_ROUTING=1 and `claude-supervisor` on
PATH, against the deployed default profile (run `./deploy install` first). Nothing is dispatched
and no files are written.
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("SUPERVISOR_LIVE_ROUTING") != "1" or shutil.which("claude-supervisor") is None,
    reason="live routing check: set SUPERVISOR_LIVE_ROUTING=1 and install claude-supervisor (costs money)",
)

AGENTS = sorted(p.stem for p in (Path(__file__).resolve().parent.parent / "pack" / "agents").glob("*.md"))
# One scoped rule per agent: denies the dispatch but keeps the Agent tool and its catalogue in context.
DENIES = ",".join("Agent(%s)" % a for a in AGENTS)
WRAPPER = (
    "Routing check only: do not dispatch or call tools; answer from your routing rules; "
    "reply with exactly one line `MODE: <1|2|direct>; AGENT: <name|none>`.\n\nRequest: "
)
CASES = [
    ("Fix the typo 'recieve' in README.md.", "2", "fixer"),
    ("Commit the staged changes with the message 'docs: clarify install steps'.", "2", "git-ops"),
    ("Which file in this repo defines the function parse_frontmatter?", "2", "scout"),
    ("What is the difference between /clear and /compact?", "direct", "none"),
    ("Find out how deploy registers profiles and write it up.", "1", "researcher"),
    ("Plan a `--json` flag for `deploy status`.", "1", "planner"),
    ("Add a `--json` flag to `deploy status` with tests.", "1", "executor"),
    ("Draft the overview section of our proposal from these notes: goals, budget, timeline.", "1", "writer"),
    ("Rename the variable `cfg` to `config` across deploy, tests/test_deploy.py and docs/deploy.md.", "2", "fixer"),
    ("The fixer reported: ESCALATE: the rename touches 12 files and two call sites change signature. "
     "What now?", "1", "executor"),
    ("Push main to origin.", "2", "git-ops"),
    ("Rework the profile registry into a class and migrate callers.", "1", "executor"),
    ("Quick: fix the failing test in tests/test_deploy.py.", "2", "fixer"),
    ("Change the default backup directory to ~/backups; existing users' backups will land there from now on.", "1", "executor"),
]
SEEN = []


def run_case(request: str) -> dict:
    proc = subprocess.run(
        ["claude-supervisor", "-p", WRAPPER + request, "--agent", "supervisor",
         "--disallowedTools", DENIES, "--permission-mode", "dontAsk", "--max-turns", "4",
         "--max-budget-usd", "0.5", "--output-format", "json"],
        capture_output=True, text=True, timeout=300,
    )
    return json.loads(proc.stdout)


def parse(text: str):
    m = re.search(r"MODE:\s*(1|2|direct);\s*AGENT:\s*(\S+)", text or "")
    return (m.group(1), m.group(2).strip("`.,;")) if m else None


@pytest.fixture(scope="session", autouse=True)
def cost_report():
    yield
    models = sorted({m for r in SEEN for m in (r.get("modelUsage") or {})})
    cost = sum(r.get("total_cost_usd") or 0 for r in SEEN)
    print("\nrouting check: %d cases, $%.2f, model %s" % (len(SEEN), cost, ", ".join(models) or "unknown"))


@pytest.mark.parametrize("request_text,mode,agent", CASES, ids=[c[0][:40] for c in CASES])
def test_routing(request_text, mode, agent):
    result = run_case(request_text)
    SEEN.append(result)
    print("\n%s: $%.4f, model %s" % (request_text[:40], result.get("total_cost_usd") or 0,
                                     ", ".join(result.get("modelUsage") or {}) or "unknown"))
    got = parse(result.get("result"))
    assert got == (mode, agent), "got %r from %r" % (got, result.get("result"))
    assert result.get("num_turns", 0) <= 2, "num_turns %s" % result.get("num_turns")
