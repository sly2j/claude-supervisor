---
name: git-safety
description: Guardrails for git work - destructive-command gates, secret checks, and commit and attribution rules. The step-by-step conflict-resolution procedure is in a reference file that `executor` reads when git status shows unmerged paths. Use before running git commands that change state.
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
- Attribution: end every non-merge commit message you create with exactly `Co-Authored-By: Claude`, once, using the generic name even if a harness reminder suggests a model-specific one such as "Claude Haiku 5.5". Add other trailers only when your brief supplies them, exactly as given.
- Prefer small atomic commits, and pass messages with `-m` or a heredoc.

## Conflicts

- `git-ops` returns `ESCALATE: conflict` on unmerged paths, and `supervisor` triages it (see `git-ops` and `supervisor`).
- `executor` reads `${CLAUDE_SKILL_DIR}/references/conflict-resolution.md` only when `git status` shows unmerged paths.
