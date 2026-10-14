# Plan: claude-agents v1

Source research: `docs/research-claude-code-port.md`.

## Decisions (confirmed with user 2026-10-14)

- Mode 1 (full harness): supervisor -> lead -> N parallel workers -> critic -> scope-critic -> lead decides, loop.
- Mode 2 (quick): supervisor -> one Haiku specialist. The supervisor chooses the mode unless the user names one.
- Models: supervisor, planner, and scope-critic on Fable 5.1. researcher, executor, and writer leads on Opus 5.5.
  critic on Opus 5.5 (planner overrides it to Fable). researcher-worker and executor-worker on Sonnet 5.5.
  writer-worker on Opus 5.5. Quick specialists on Haiku 5.5 at xhigh effort.
- Writing is core: a `writer` lead with one drafter by default, sharing critic and scope-critic.
- Install into `~/.claude` (or `$CLAUDE_CONFIG_DIR`) with a manifest, and set `"agent": "supervisor"` in settings.json.

## Layout

```
pack/agents/*.md            13 agents
pack/skills/<name>/         11 skills
scripts/deploy              stdlib Python >=3.9: install | status | uninstall | doctor
tests/                      pytest: deploy behavior + pack lint
docs/                       research, plan, architecture, deploy runbook
CLAUDE.md                   repo conventions + "how to deploy" for Claude
README.md
```

## Agents

| Agent | Tier | Model / effort | Tools | Dispatches |
|---|---|---|---|---|
| supervisor | main | fable / high | read-only + Agent(allowlist) | leads, critic, scope-critic, quick tier |
| researcher | lead | opus / high | all | researcher-worker, critic, scope-critic |
| planner | lead | fable / xhigh | all | researcher-worker, critic(model: fable), scope-critic |
| executor | lead | opus / high | all | executor-worker, critic, scope-critic |
| writer | lead | opus / high | all | writer-worker, researcher-worker (extraction), critic, scope-critic |
| researcher-worker | worker | sonnet / high | no Agent | - |
| executor-worker | worker | sonnet / high | no Agent | - |
| writer-worker | worker | opus / high | no Agent | - |
| critic | review | opus / xhigh | read-only + Bash | - |
| scope-critic | review | fable / high | read-only | - |
| quick-edit | quick | haiku / xhigh | edit, no Agent | - |
| git-ops | quick | haiku / xhigh | Bash + read, no Agent | - |
| scout | quick | haiku / xhigh | read-only + Bash + web | - |

## The loop (skill `lead-loop`, preloaded into all leads)

1. Contract: requirements, acceptance criteria, in-scope / out-of-scope lists.
2. Fan-out: split into N independent units (1-6) and dispatch the workers in one message.
3. Integrate the worker reports into the artifact.
4. critic: findings tagged BLOCKING / SHOULD / NIT with evidence; verdict PASS / REVISE.
5. scope-critic: given the contract, artifact, and critic findings, rule KEEP / DOWNGRADE / DROP on
   each finding and list CUT items (existing bloat in the artifact).
6. Lead decides and records why. Fix kept BLOCKING findings and apply CUTs. Repeat up to 3 rounds.
   A stalemate (same finding twice) escalates.
7. Bounded report to the supervisor, including a decision log.

## Todo

- [x] Research old repo and Claude Code capabilities
- [x] Confirm models, critic, writer, activation with user
- [x] Write agents (13)
- [x] Write new skills: lead-loop, git-safety, python-env, agent-authoring, meeting-summary
- [x] Port skills: document-extraction, email-extraction, project-backup, science-writing-style,
      presentation-style, writing-rules-persistence
- [x] scripts/deploy with manifest reconcile, settings merge, lock, backups, doctor
- [x] tests: deploy behavior + pack lint (frontmatter, names, models, tool rules, skill refs)
- [x] docs: README, CLAUDE.md, docs/architecture.md, docs/deploy.md
- [x] Review pass (critic + scope-critic style) and test run
- [x] Dry-run deploy against a temp CLAUDE_CONFIG_DIR

## Out of scope

Argo/provider config, model profile switching, plugin packaging, agent teams, CI.
