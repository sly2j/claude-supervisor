---
name: git-safety
description: Guardrails and procedures for git work - destructive-command gates, secret checks, commit and attribution rules, and the step-by-step procedure for resolving active merge/rebase/cherry-pick conflicts. Use before running git commands that change state, and whenever git status shows unmerged paths.
---

# Git Safety

## Gated Operations

Run these only when the user explicitly asked for that operation, as passed in your brief. Otherwise stop and escalate.
- `git push --force` or `--force-with-lease`. Never force-push to `main` or `master` without the user naming that branch.
- `git reset --hard`, `git clean -fd`, `git checkout -- .`, `git restore .`, `git branch -D`, deleting tags, `git stash drop` or `clear`
- Rewriting published history: rebasing, amending, or squashing commits that exist on a remote.
- `--no-verify`, `--no-gpg-sign`
- Changing identity: `--author`, `GIT_AUTHOR_*` or `GIT_COMMITTER_*`, or `git config user.*`

## Always

- Use no interactive modes (`rebase -i`, `add -i`, `add -p`, or an editor without `-m`).
- Never amend a commit you did not create in this session, or any commit that has been pushed. If a pre-commit hook rejects a commit, fix the problem and create a new commit; do not amend.
- Never commit likely secrets: `.env*`, `credentials*`, `*.pem`, `*.key`, `id_*`, tokens in diffs. Check `git diff --cached --stat` and scan the staged diff for secrets before committing.
- Report the exact commands you ran, with their key output.

## Commits

- Use Conventional Commits, `<type>(<optional scope>): <description>`, unless the repo's history shows a different convention. Follow the history.
- Common types: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`.
- Attribution: append the trailer lines your brief supplies exactly, once, at the end of every non-merge commit message you create. If none are supplied, add none.
- Prefer small atomic commits, and pass messages with `-m` or a heredoc.

## Resolving Conflicts

Use this only when `git status` shows unmerged paths. Do not start merges, rebases, or cherry-picks yourself.

1. Run `git status` to list the conflicted files and the operation in progress.
2. Read each file's `<<<<<<<` / `=======` / `>>>>>>>` regions, and the intent of both sides, using `git log` on each side when that helps.
3. Combine changes that do not overlap. Where both sides change the same thing, pick the side that matches the intended outcome and note what you discarded.
4. If the intent is ambiguous or needs domain knowledge, stop and present both sides with a recommendation.
5. Remove all markers. Validate structured files (JSON, YAML, TOML) and run the relevant tests.
6. Stage only the resolved files. Never edit files that are not in conflict, or anything under `.git/`.
7. Continue with `git merge --continue`, `git rebase --continue`, or `git cherry-pick --continue`. Apply the attribution rule to any commit this creates.
8. Run `git status` to confirm the final state. If the user asks to abort, use the matching `--abort`.

Report each conflicted file and how it was resolved (kept, combined, or discarded). Never silently drop changes, and warn immediately if a conflict involves credentials.
