# claude-agents

A supervisor-based agent pack for [Claude Code](https://code.claude.com/docs). One Fable supervisor routes every request either to the full harness (leads that fan out to parallel workers, with a critic and a scope-critic loop) or to fast Haiku specialists for small tasks.

It succeeds the OpenCode agent pack (`opencode-agents`). The design rationale is in [docs/research-claude-code-port.md](docs/research-claude-code-port.md), and the details are in [docs/architecture.md](docs/architecture.md).

## Install

Requires Claude Code 2.1.293 or newer and `python3` 3.9 or newer, on macOS or Linux.

```bash
git clone <this-repo> ~/Work/claude-agents
~/Work/claude-agents/scripts/deploy doctor
~/Work/claude-agents/scripts/deploy install
```

You can also ask Claude Code: *"deploy the agents in ~/Work/claude-agents"*. It follows [docs/deploy.md](docs/deploy.md). To update, run `git pull` and then `scripts/deploy install` again. `status`, `uninstall`, and `doctor` are also available.

Optional but recommended: Anthropic's document skills for docx, pdf, pptx, and xlsx. In Claude Code, run `/plugin marketplace add anthropics/skills` and install `document-skills`.

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

## Repository Layout

```
pack/agents/        agent definitions (deployed to ~/.claude/agents)
pack/skills/        skills (deployed to ~/.claude/skills)
scripts/deploy      installer: install | status | uninstall | doctor
tests/              deploy behavior tests + pack lint
docs/               research, plan, architecture, deploy runbook
```

Run `python3 -m pytest -q` before deploying changes to the pack.
