---
domain: process
summary: curator and clerk never commit; git-ops is the only Mode 2 committer, dispatched after memory writes, bumps VERSION and carries the attribution
affects: [pack/agents/curator.md, pack/agents/clerk.md, pack/agents/git-ops.md, pack/agents/supervisor.md, pack/skills/project-memory/, pack/skills/git-safety/, pack/skills/repo-workflow/SKILL.md, deploy]
verified: 2026-10-23
source: user 2026-10-23 ("should curator and clerk be doing commits in the first place? That's git-ops job"; approved the proposal: "yes, that sounds good")
supersedes: [.supervisor/archive/memory/decisions/2026-10-23-only-git-ops-commits-memory-writes.md, .supervisor/archive/memory/decisions/2026-10-22-store-lives-in-the-branch-curator-commits.md]
---
Reach: product behaviour, written into `pack/` by executor (done in commit 4576a93, v4.11); this entry keeps the decision and why for repo work.

Decided (owner sjoosten):
- `curator` and `clerk` never commit. They write and stage files under `.supervisor/` and report what changed.
- `git-ops` is the only Mode 2 agent that commits. `supervisor` dispatches it after a memory write, once per wave in a program.
- Mode 1 leads (executor, researcher, planner, writer) keep committing their own work as landing agents.
- `git-ops` bumps `VERSION` from the shell when it lands a change in an X.y repo, per `repo-workflow` ("the agent that lands the change bumps it").
- `deploy` sets `attribution.commit` to `Co-Authored-By: Supervisor for Claude` in the sandbox `settings.json`, not under `--global`.

Why: the attribution rule lived only in `git-safety`, which curator and clerk do not preload and cannot load (no Skill tool). Claude Code's default model-name trailer won, and they refused the supervisor's correction as an agent message without user authority. One committer per mode keeps the commit rules in one place; a focused Haiku prompt (git-ops) follows them reliably, a crowded one does not.

Supersedes the old entry only as far as curator committing; the store still lives in the branch (see `2026-10-23-store-lives-in-the-branch.md`).
