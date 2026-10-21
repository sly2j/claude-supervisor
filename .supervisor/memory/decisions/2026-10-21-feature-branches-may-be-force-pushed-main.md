---
domain: process
summary: Feature branches may be force-pushed (--force-with-lease) to origin; main never is
affects: [CLAUDE.md, docs/deploy.md]
verified: 2026-10-21
source: user 2026-10-21
supersedes:
---
The user said: "you can force push if desired. Only protected branch is main." Feature branches
of this repo (e.g. `memory-stage4`) are pushed to origin (eicweb) and must be rebased on `main`
often (CLAUDE.md), so their history is rewritten and a plain push is rejected. Force-pushing a
feature branch, as `git push --force-with-lease`, is therefore authorized without asking again.
`main` is the only protected branch and is never force-pushed. The rule covers this repo's git
practice only, so it lives here and not in `pack/` (the `git-safety` skill stays generic).
Related: `.supervisor/memory/decisions/2026-10-21-memory-work-was-developed-on-a-feature.md`
(the feature-branch and worktree flow, no `VERSION` edits on branches).
