---
domain: process
summary: Only curator creates the store and commits it (pathspec, VERSION raised on an X.y default branch); idempotent
affects: [pack/skills/project-memory/SKILL.md, pack/skills/project-memory/references/curator-procedures.md, pack/agents/curator.md]
verified: 2026-10-22
source: user 2026-10-22, .supervisor/archive/working/plans/plan-store-persistence.md#decisions
supersedes: 
---
D5 (user, option b). Only `curator` creates the store: README, `git add .supervisor`, then `git commit -m 'chore(memory): create project store' -- .supervisor`, so other staged work stays staged. On the default branch of a repo using the `repo-workflow` X.y scheme it raises y in `VERSION` in the same commit. It skips the commit and reports why without git, when `.supervisor/` is gitignored, or during a merge, rebase or cherry-pick. An existing store is reported (`store exists`), not recreated. Any other agent whose first write finds no store writes nothing and reports `follow-up: curator make this a project`.

Reach: product; stated in `project-memory` SKILL.md, `curator-procedures.md` (Make this a project) and `curator.md`.
superseded by: .supervisor/memory/decisions/2026-10-22-store-lives-in-the-branch-curator-commits.md
