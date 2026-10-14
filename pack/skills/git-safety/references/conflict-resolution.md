# Resolving Conflicts

Use this only when `git status` shows unmerged paths. Do not start merges, rebases, or cherry-picks yourself.

1. Run `git status` to list the conflicted files and the operation in progress.
2. Read each file's `<<<<<<<` / `=======` / `>>>>>>>` regions, and the intent of both sides, using `git log` on each side when that helps.
3. Combine changes that do not overlap. Where both sides change the same thing, pick the side that matches the intended outcome and note what you discarded.
4. If the intent is ambiguous or needs domain knowledge, stop and present both sides with a recommendation. If the conflict is deeper than the triage in your brief (overlapping logic edits, many files, or unclear intent on either side), stop and report Outcome `blocked` with a summary starting `ESCALATE: conflict deeper than triaged`, plus what you found, rather than resolving it.
5. Remove all markers. Validate structured files (JSON, YAML, TOML) and run the relevant tests.
6. Stage only the resolved files. Never edit files that are not in conflict, or anything under `.git/`.
7. Continue with `git merge --continue`, `git rebase --continue`, or `git cherry-pick --continue`. Apply the attribution rule to any commit this creates.
8. Run `git status` to confirm the final state. If the user asks to abort, use the matching `--abort`.

Report each conflicted file and how it was resolved (kept, combined, or discarded). Never silently drop changes, and warn immediately if a conflict involves credentials.
