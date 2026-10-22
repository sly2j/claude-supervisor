---
domain: process
summary: Landing stages the default checkout's pending store changes into the squash commit; a refusal is fixed by committing them first
affects: [pack/skills/repo-workflow/SKILL.md]
verified: 2026-10-22
source: user 2026-10-22, .supervisor/archive/working/plans/plan-store-persistence.md#decisions
supersedes: 
---
D3. Landing stages the default checkout's pending store changes into the squash commit. If `git merge --squash` refuses because of them (for example an untracked store file the branch also adds), commit them first in the D5 form (`chore(memory): ...`), then return to the rebase step. A merge the user asks for of any branch, including one the user made, follows the same landing steps.

Reach: product; `pack/skills/repo-workflow/SKILL.md` (landing).
