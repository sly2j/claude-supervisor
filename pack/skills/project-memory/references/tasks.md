# Task cards

A task card is one mid-term item in `.supervisor/tasks/`. Copy
`${CLAUDE_SKILL_DIR}/templates/task.md`. Cards are not entries and do not count toward the
five-entry cap.

- Path: `.supervisor/tasks/YYYY-MM-DD-<slug>.md`, date and slug as for entries. The card name is
  the file stem; `depends:` cites card names, never paths.
- `summary:` is the grep target and the one-line listing; `status:` is `open`, `active` or
  `blocked`.
- A `blocked` card gives its reason in `Notes:` and may have no owner; it is never pickable.
- `since:` is the date of the last status change, empty on an open card.
- `owner:` is the branch the work lands from, as briefed; free text when the user says otherwise.
- `plan:` is the plan path, set at claim only when the route has a `planner` stage.
- Body at most 200 words, no minor versions. `decisions:` cites by path only entries that
  still bind.
- Pickable: `status: open` and no `depends:` name still present in `tasks/`.
- List and claim in the default-branch checkout, before a worktree is cut, so the branch carries
  the claimed card.
- Reach: a tracked store shares cards with other clones once pushed (a linked worktree holds its
  branch's cards); a local store, this checkout only; an externalized store, every linked checkout
  live.
- A quick-tier card is not claimed: done in the current checkout, finished with
  `close-out task <card>`.
- A claim is compare-and-set: `fixer` replaces the text `status: open`; if it is not found,
  list again.
- A finished card is archived whole; what its plan left over arrives as `deferred:` cards.

| Transition | Who | Change |
|---|---|---|
| create | `curator` (`task`, close-out `deferred:`, roadmap migration) | new card, `open` or `blocked` |
| claim | `fixer` replacing `status: open`, then `git-ops` `chore(memory): claim <card>`; none for the quick tier | `status: active`, `owner`, `since`, `plan` when the route has a planner stage |
| other status edits | `fixer`, on the user's word | block: `blocked`, reason in `Notes:`; unblock: `active` (`open` with no owner); release: `open`, `owner` and `plan` emptied; `since` per the rule above |
| finish | `curator` close-out | `met: YYYY-MM-DD`, `git mv` to `archive/tasks/`, `history.md` line |
| drop | `curator` `drop task` | `dropped: YYYY-MM-DD`, `git mv`; report live cards that depend on it |

Archived cards are never edited or repointed.
