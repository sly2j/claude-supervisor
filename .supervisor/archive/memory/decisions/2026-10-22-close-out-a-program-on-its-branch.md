---
domain: process
summary: Close out a major program with curator on its feature branch before the squash merge
affects: [CLAUDE.md, pack/skills/repo-workflow/SKILL.md]
verified: 2026-10-22
source: .supervisor/archive/working/plans/plan-memory-v2.md; owner 2026-10-21
supersedes: .supervisor/archive/memory/decisions/2026-10-22-program-flow-rationale.md
superseded by: pack/skills/repo-workflow/SKILL.md
---
Run `curator close-out` on the branch before the squash merge; the brief states the version in advance (`VERSION` on `main` plus one, or `X.0`).
Why: the merge then lands the store changes in the one `main` commit with its bump. Rejected: closing out after the merge, which costs a commit and bump and leaves `main` describing landed work as planned. `CLAUDE.md` does not state this step.
