# Landing From A Worktree

Use this when no checkout has the default branch, or the harness confines the session to the
worktree and refuses commands against the parent checkout. Run everything in the worktree.

1. `git fetch origin`, then `git rebase origin/<default> <branch>` (step 2 of Landing A Work
   Branch) and rerun the checks.
2. `git checkout --detach origin/<default>`, then `git merge --squash <branch>`, then
   `git add .supervisor`.
3. Bump `VERSION` in an `X.y` repo when the change set touches a versioned path (`SKILL.md`, The
   X.y Scheme), and run the checks.
4. Apply the step-4 guard unchanged: commit only once
   `git diff --cached --quiet <branch> -- . ':!VERSION'` (with `':!.supervisor'` as step 4 says)
   confirms the staged tree is the branch. Commit with the `git-safety` trailer.
5. Push only when the brief carries `Confined to worktree: <path>; push to <default> authorized`.
   Without it, stop here and report the squash SHA.
6. `git push origin HEAD:<default>`, fast-forward only, never `--force`. If origin rejects, fetch,
   redo from step 1 once, then stay detached, report the squash SHA and stop. Push other remotes
   after origin in the same step (Sync With Origin).
7. `git checkout <branch>`. Report the squash SHA, that the parent checkout needs
   `git pull --ff-only`, and that the worktree was not removed.
