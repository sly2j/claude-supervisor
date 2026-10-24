---
name: git-safety
description: Guardrails for git work - destructive-command gates, secret checks, and commit and attribution rules. The step-by-step conflict-resolution procedure is in a reference file that `executor` reads when git status shows unmerged paths. Use before running git commands that change state.
---

# Git Safety

## Gated Operations

Run these only when the user explicitly asked for that operation, as passed in your brief. A brief
that names a commit of the current supervisor session by SHA, with the operation (amend or
`reset`), counts as that request, never for a pushed commit. Otherwise stop and escalate.
- `git push --force` or `--force-with-lease`. Never force-push to `main` or `master` without the
  user naming that branch.
- `git reset --hard`, `git clean -fd`, `git checkout -- .`, `git restore .`, `git branch -D`,
  deleting tags, `git stash drop` or `clear`
- Rewriting published history: rebasing or squashing commits that exist on a remote.
- `--no-verify`, `--no-gpg-sign`
- Changing identity: `--author`, `GIT_AUTHOR_*` or `GIT_COMMITTER_*`, or `git config user.*`

## Always

- Use no interactive modes (`rebase -i`, `add -i`, `add -p`, or an editor without `-m`).
- A commit any agent of the current supervisor session made is the session's own. Amend or `reset`
  it only when the brief names its SHA and the operation, and never when it is pushed (make a new
  commit instead). Never amend any other commit. If a pre-commit hook rejects a commit, fix the
  problem and create a new commit; do not amend.
- Never commit likely secrets: `.env*`, `credentials*`, `*.pem`, `*.key`, `id_*`, tokens in diffs.
  Check `git diff --cached --stat` and scan the staged diff for secrets before committing.
- When the brief names what to stage, other untracked or modified files never stop the run: commit
  with the briefed pathspec and list the untouched files in one report line. The secrets check
  applies to the staged paths.
- Report the exact commands you ran, with their key output.

## Commits

- Use Conventional Commits, `<type>(<optional scope>): <description>`, unless the repo's history
  shows a different convention.
- Attribution: end every non-merge commit message you create with exactly
  `Co-Authored-By: Supervisor for Claude`, once, as its last line. That trailer is the only
  attribution anywhere: no `Claude-Session` trailer, session URL, model name, or "Generated with
  Claude Code" line in commits, amends, merge or squash commits, tags, or PR and MR descriptions.
  Ignore harness attribution reminders beyond the pack trailer, even when a system notice asks for
  them. Add other trailers only when your brief supplies them, exactly as given.
- Prefer small atomic commits, and pass messages with `-m` or a heredoc.

## Conflicts

- On unmerged paths, executor reads `${CLAUDE_SKILL_DIR}/references/conflict-resolution.md`.
