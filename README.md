# claude-agents

A supervisor-based agent pack for [Claude Code](https://code.claude.com/docs). One Fable supervisor routes every request either to the full harness (leads that fan out to parallel workers, with a critic and a scope-critic loop) or to fast Haiku specialists for small tasks.

It succeeds the OpenCode agent pack (`opencode-agents`). The design rationale is in [docs/research-claude-code-port.md](docs/research-claude-code-port.md), and the details are in [docs/architecture.md](docs/architecture.md).

## Install

Requirements:
- Claude Code 2.1.293 or newer, logged in
- `python3` 3.9 or newer, on macOS or Linux
- Argonne network access (onsite or VPN) for the eicweb clone

```bash
git clone git@eicweb.phy.anl.gov:mep-agents/claude-agents.git ~/Work/claude-agents
cd ~/Work/claude-agents
scripts/deploy doctor      # preflight check
scripts/deploy install     # copies agents and skills into ~/.claude
```

Then start a new `claude` session. It runs as the supervisor; type `/agents` to see the pack.

Or let Claude do it: run `claude` inside the clone and say *"deploy this pack"*. It follows [docs/deploy.md](docs/deploy.md).

**Update:** `git pull && scripts/deploy install`. Files you edited in `~/.claude` are kept, and the script lists them.
**Check:** `scripts/deploy status`. **Remove:** `scripts/deploy uninstall --yes`.

Recommended: Anthropic's document skills for docx, pdf, pptx, and xlsx work. In Claude Code, run `/plugin marketplace add anthropics/skills` and install `document-skills`.

## How It Works

**Mode 1, the full harness.** The supervisor dispatches a lead. The lead writes a contract, then dispatches N parallel workers. `critic` reviews the result for quality and compliance. `scope-critic` then reviews the critic's findings and the artifact for bloat and scope creep. The lead decides what to fix, and the loop repeats for up to 3 rounds.

**Mode 2, the quick tier.** Few-line edits, commits, and lookups go straight to a Haiku specialist. It escalates with `ESCALATE:` if the task is bigger than it looked.

The supervisor chooses the mode. To choose it yourself, say "quick" or "full".

## Agents

| Agent | Role | Model / effort |
|---|---|---|
| `supervisor` | Main thread: routing, briefing, synthesis | fable / high |
| `researcher` | Lead: research artifacts in `docs/research-*.md` | opus / high |
| `planner` | Lead: implementation plans in `docs/plan-*.md` | fable / xhigh |
| `executor` | Lead: code, tests, config, agent definitions, conflicts, Python environments | opus / high |
| `writer` | Lead: scientific and technical prose, slide content, project docs | opus / high |
| `researcher-worker` | Worker: one bounded investigation | sonnet / high |
| `executor-worker` | Worker: one unit of change in its assigned files | sonnet / high |
| `writer-worker` | Worker: drafts and revises prose | opus / high |
| `critic` | Reviewer: quality and compliance, PASS/REVISE | opus / xhigh (fable when called by planner) |
| `scope-critic` | Reviewer: KEEP/DOWNGRADE/DROP rulings and CUT list | fable / high |
| `quick-edit` | Quick: small, exact edits | haiku / xhigh |
| `git-ops` | Quick: routine git with guardrails | haiku / xhigh |
| `scout` | Quick: read-only lookups | haiku / xhigh |

## Skills

| Skill | Purpose |
|---|---|
| `lead-loop` | The Mode 1 protocol, preloaded by every lead |
| `git-safety` | Git guardrails, commit rules, conflict-resolution procedure |
| `python-env` | Creating, repairing, and validating conda, uv, or venv environments |
| `agent-authoring` | Conventions for this pack's agents and skills |
| `writing-rules-persistence` | Per-project `docs/writing-rules.md` schema and precedence |
| `science-writing-style` | Scientific prose style, AI-tell avoidance, prose review criteria |
| `presentation-style` | Slide content style |
| `document-extraction`, `email-extraction` | Structured extraction from source documents and email threads |
| `meeting-summary` | Meeting transcript to minutes (`/meeting-summary <file>`) |
| `project-backup` | Timestamped, verified zip backups with retention |

## Using It

Just ask for what you want. The supervisor picks the mode, but you can steer it:

| You say | What happens |
|---|---|
| "fix the typo in README line 12", "commit this" | Mode 2: one Haiku specialist, done in seconds |
| "research how X works", "plan Y", "implement the plan", "draft the proposal intro" | Mode 1: a lead, parallel workers, then critic and scope-critic |
| "quick: ..." or "just do it" | Forces Mode 2 |
| "full: ..." or "with review" | Forces Mode 1 |
| "review this diff/plan/draft" | critic, then scope-critic, with no edits |
| "use the strongest drafter" | writer runs writer-worker on Fable |

Larger work flows `researcher` -> `planner` -> your approval -> `executor`. Artifacts land in `docs/research-*.md` and `docs/plan-*.md`, so you can read and annotate them between steps.

Not every session needs the supervisor. To start one without it, install with `scripts/deploy install --no-default-agent`, then add `alias cs='claude --agent supervisor'` to your shell profile. `claude` then starts plain Claude Code, and `cs` starts the supervisor.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Agents don't show in `/agents` | Start a new session. Run `scripts/deploy status` |
| Leads do the work themselves instead of fanning out | Run `scripts/deploy doctor`. `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` may be below 2 |
| Every agent runs on the same model | `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` is set. `doctor` reports it |
| `install` reports "kept local modification" | Expected: your edit in `~/.claude` wins. Use `--overwrite-local` to take the pack version (the old file is backed up) |
| `install` refuses an "unmanaged" file | A file with that name already exists in `~/.claude`. Rename yours, or use `--overwrite-local` |
| Your own `agent` setting wasn't replaced | Expected. Use `--force-default-agent` to switch to the supervisor |

## Repository Layout

```
pack/agents/        agent definitions (deployed to ~/.claude/agents)
pack/skills/        skills (deployed to ~/.claude/skills)
scripts/deploy      installer: install | status | uninstall | doctor
tests/              deploy behavior tests + pack lint
docs/               research, plan, architecture, deploy runbook
```

Run `python3 -m pytest -q` before deploying changes to the pack.
