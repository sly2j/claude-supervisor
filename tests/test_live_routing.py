"""Live routing check: ask the deployed supervisor to route canonical requests.

Opt-in, because every case calls the model (28 calls, a few cents to tens of cents each, at most $0.50 each; the
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
    "reply with exactly one line `MODE: <1|2|direct>; AGENT: <name|none>; MODEL: <fable|opus|sonnet|haiku|default>` (the `model:` alias you would pass on the dispatch, `default` when you would pass none).\n\nRequest: "
)
CASES = [
    ("Fix the typo 'recieve' in README.md.", "2", "fixer", "default"),
    ("Commit the staged changes with the message 'docs: clarify install steps'.", "2", "git-ops", "default"),
    ("Which file in this repo defines the function parse_frontmatter?", "2", "scout", "default"),
    ("What is the difference between /clear and /compact?", "direct", "none", "default"),
    ("Find out how deploy registers profiles and write it up.", "1", "researcher", "default"),
    ("Plan a `--json` flag for `deploy status`.", "1", "planner", "default"),
    ("Add a `--json` flag to `deploy status` with tests.", "1", "executor", "default"),
    ("Draft the overview section of our proposal from these notes: goals, budget, timeline.", "1", "writer", "default"),
    ("Rename the variable `cfg` to `config` across deploy, tests/test_deploy.py and docs/deploy.md.", "2", "fixer", "default"),
    ("The fixer reported: ESCALATE: the rename touches 12 files and two call sites change signature. "
     "What now?", "1", "executor", "default"),
    ("Push main to origin.", "2", "git-ops", "default"),
    ("Move the four profile-registry functions in deploy into a `ProfileRegistry` class with the same method names and update their three callers.", "1", "executor", "default"),
    ("Quick: fix the failing test in tests/test_deploy.py.", "2", "fixer", "default"),
    ("Change the default backup directory to ~/backups; existing users' backups will land there from now on.", "1", "executor", "default"),
    # Tier overrides: planner Opus by default, Fable on trigger; writer and executor Opus only when the rules say so.
    ("Plan how to add retry logic to the backup step of `deploy install`; I'm not sure whether a decorator "
     "or a loop fits better.", "1", "planner", "default"),
    ("Plan the move of all our services to a new auth provider: the gateway, billing, the web app and the CLI "
     "each need changes over the next quarter.", "1", "planner", "fable"),
    ("Work out how the deploy tool's profile registry and the test harness's fixture loader should share state; I see a few approaches "
     "with real trade-offs and want a plan.", "1", "planner", "fable"),
    ("Plan a port of the deploy tool to Windows; nobody here has done Windows packaging before.",
     "1", "planner", "fable"),
    ("Plan a `--quiet` flag for `deploy status`, and be thorough about it.", "1", "planner", "fable"),
    ("I left comments in .supervisor/plans/auth-migration.md (the quarter-long program moving the gateway, "
     "billing, web app and CLI to a new auth provider); work through my annotations and update the plan.",
     "1", "planner", "default"),
    ("Sync the checklist in .supervisor/plans/auth-migration.md (the quarter-long program moving the gateway, "
     "billing, web app and CLI to a new auth provider) with what has landed in git.",
     "1", "planner", "default"),
    ("Write a short email to the team saying the deploy window moves to Thursday.", "1", "writer", "opus"),
    ("Write the methods paragraph for our paper on the detector calibration from these notes.",
     "1", "writer", "default"),
    ("tests/test_deploy.py fails intermittently, only when run in parallel; track down the race and fix it.",
     "1", "executor", "opus"),
    ("Write a new agent definition for a security reviewer in pack/agents.", "1", "executor", "opus"),
    ("Split deploy into a package with cli.py, profiles.py and install.py along its existing sections; I haven't touched that code in years.",
     "1", "executor", "opus"),
    ("Why is `deploy install` slow on macOS? Investigate before we change anything.", "1", "researcher", "default"),
    ("`deploy status` crashes with `KeyError: 'profile'` at deploy:412 when no profile is registered. "
     "Fix it and add a regression test, with review.", "1", "executor", "default"),
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
    m = re.search(r"MODE:\s*(1|2|direct);\s*AGENT:\s*(\S+?)[`.,;]*\s*;\s*MODEL:\s*`?(fable|opus|sonnet|haiku|default)", text or "")
    return (m.group(1), m.group(2).strip("`.,;"), m.group(3)) if m else None


@pytest.fixture(scope="session", autouse=True)
def cost_report():
    yield
    models = sorted({m for r in SEEN for m in (r.get("modelUsage") or {})})
    cost = sum(r.get("total_cost_usd") or 0 for r in SEEN)
    print("\nrouting check: %d cases, $%.2f, model %s" % (len(SEEN), cost, ", ".join(models) or "unknown"))


@pytest.mark.parametrize("request_text,mode,agent,model", CASES, ids=[c[0][:40] for c in CASES])
def test_routing(request_text, mode, agent, model):
    result = run_case(request_text)
    SEEN.append(result)
    print("\n%s: $%.4f, model %s" % (request_text[:40], result.get("total_cost_usd") or 0,
                                     ", ".join(result.get("modelUsage") or {}) or "unknown"))
    got = parse(result.get("result"))
    assert got == (mode, agent, model), "got %r from %r" % (got, result.get("result"))
    assert result.get("num_turns", 0) <= 2, "num_turns %s" % result.get("num_turns")
