# Plan: project-store persistence (worktrees, creation commit, detection)

## Goal

Make `.supervisor/` survive: (a) a worktree's store is its branch's memory and lands with the
branch; (b) "make this a project", decided by the user or by `supervisor`, creates and commits
the store; (c) `supervisor`, `planner` and `researcher` see the existing detection rule.
Non-goals: changing the D13 marker set; any other repo. Expected change: about 120 diff lines
(added plus removed, counting rewrapped prose) in 10 pack/doc files plus `VERSION`; no new tests.

## Approach

D13 already detects projects (`pack/skills/project-memory/SKILL.md:70-75`); the deciders never
see it and nothing commits or lands the store. Fix with commit rules, landing steps and pointers.
Rejected: a memory sync step after landing (git merges committed files); preloading
project-memory anywhere new (910 words of context); a commit per default-branch store write (a
`VERSION` bump per entry).

## Decisions

- D1 (user, a): a linked worktree's `.supervisor/` is its branch's memory, landed by git.
  Off the default branch, whoever writes store files (a lead, `curator`, `clerk`, `writer`)
  ends its run with a pathspec commit of them, `chore(memory): <what>`, per `git-safety`
  Commits, no `VERSION` change. Fixes the observed loss: a planning-only session in a user-made
  worktree now leaves its plan committed on the branch.
- D2: every commit in a project checkout, on any branch, also stages that checkout's pending
  `.supervisor/` changes, except while resolving a conflict (`conflict-resolution.md:16`).
  Gives "the store is committed" (`project-memory/SKILL.md:8`) an owner on the default branch.
- D3: landing stages the default checkout's pending store changes into the squash commit. If
  `git merge --squash` refuses because of them, commit them first (D5 form), then back to step 2.
  A merge the user asks for of any branch, including one the user made, follows steps 2-5.
- D4: store conflicts: `history.md` and a plan `## Log` keep both sides' lines; other files
  combine per step 3; one entry changed differently on both sides keeps the default-branch text
  and the report names the branch text with `follow-up: curator`. Never drop an entry file.
- D5 (user, b): only `curator` creates the store: README, `git add`, `git commit -- .supervisor`
  (other staged work stays staged), `chore(memory): create project store`, per `git-safety`
  Commits. On the default branch of an X.y repo it raises y in the same commit
  (repo-workflow :43-52, CLAUDE.md: every default-branch commit raises y). Skip the commit and
  report why without git, when `.supervisor/` is gitignored, or with an operation in progress.
  Idempotent: an existing store is reported, not recreated. The lazy first-write path
  (SKILL.md:29-31, :76) instead reports `follow-up: curator make this a project`.
- D6 (user, b and c): `supervisor` applies the rule itself: in a project, before the first
  store-writing stage of a session, it dispatches `curator` `make this a project` (no check
  needed, D5 is idempotent). Root: project root in a project, current directory in a one-off.
- D7 (c): marker set unchanged. Inside git the root is the nearest `.supervisor/` within the
  work tree, else the toplevel, so `.git` counts; outside git `.supervisor/`, `.claude/`,
  `CLAUDE.md`, `AGENTS.md` count; `$HOME` and above never count; the innermost repo wins.
- D8: `planner` and `researcher` get a one-line pointer to `project-memory` (Projects and
  one-offs) beside their path rules; `executor` and the leads get D1 via `lead-loop`.

## Outline

- `pack/skills/project-memory/SKILL.md`: :29-31, :76 lazy path per D5; a "Committing the store"
  paragraph (D1 off-default commit, D5) after Layout; D7 worktree clause at :73-75. Cap 1300.
- `.../references/curator-procedures.md:71-74`: D5 procedure and idempotence.
- `pack/agents/curator.md:27-29, :44`: "create and commit" (25-word headroom).
- `pack/agents/supervisor.md`: bullet after :91 (D6, D7 in one sentence); pay for it with the
  redundancy cuts at :53-55, :57-58, :95-97, :98-100, :114-117 (body <= 1000; keep :104).
- `pack/agents/planner.md:17-18`, `researcher.md:15-16`: D8 pointer.
- `pack/skills/lead-loop/SKILL.md` near the report step: D1 one line.
- `pack/skills/repo-workflow/SKILL.md`: "Store changes" paragraph (D2) after :56-69; landing
  :75 (step 1 includes the store), :73-74 and :78-84 (D3).
- `pack/skills/git-safety/references/conflict-resolution.md`: D4 after :20.
- `docs/architecture.md:80`: one sentence on D1 and D5. No inventory row changes (no name,
  scope, model or tool changes).

## Slices

### S1: deciders see the rule; creation commits (b, c)
- Units: U1 project-memory SKILL.md (D5 part) + curator-procedures.md + curator.md;
  U2 supervisor.md; U3 planner.md + researcher.md.
- Tests: `test_agent_body_word_cap: supervisor.md -> <= 1000`; `test_skill_*: project-memory
  -> <= 1300 words, lines <= 100 chars`. Scenario in a scratch repo: D5 with an unrelated staged
  file -> one commit holding only the store (+ `VERSION` when X.y), unrelated file still staged;
  rerun -> "store exists", no commit.
- Checkpoint: `uv run --no-project --with pytest python -m pytest -q`.

### S2: the store lands with the branch (a)
- Units: U1 repo-workflow; U2 conflict-resolution.md; U3 project-memory D1 paragraph and D7
  clause + lead-loop + architecture.md.
- Scenarios (scratch repo, edited steps): `user worktree: plan written, no code commit, merge
  asked -> plan on main`; `disjoint: branch adds an entry, main has an uncommitted plan ->
  squash holds both`; `overlap: main has untracked plans/x.md, branch adds it -> squash refuses,
  store commit, rebase conflict per D4, squash holds the resolution`; `history.md appended on
  both sides -> both lines kept`.
- Checkpoint: same pytest command; scenario results in the executor report.

## Verification

Suite passes; `git diff --stat` shows only the Outline files plus `VERSION` raised by one in the
landing commit (CLAUDE.md); `curator` records D1-D6 as decision entries.

## Risks

- D2 widens commits: a commit can carry another stage's half-written store file; reports list
  the store paths they committed.
- A lead in a worktree reads the branch's store, which lacks the default checkout's uncommitted
  entries until the next landing.

## Scope Notes

Out: implementing; claude-rc-hive; the marker set. Binding user decisions (a), (b), (c) are not
reopened; D13 is `.supervisor/memory/decisions/2026-10-21-one-off-directories-persist-nothing-and.md`.

## Assumptions

- `git commit -- <paths>` keeps other staged paths staged; `git merge --squash` refuses on an
  untracked path the branch adds (both checked by critic in a scratch repo).

## Open Questions

None.

## Log

## Todo

- [x] S1 U1-U3, checkpoint, creation scenario
- [x] S2 U1-U3, checkpoint, landing scenarios
- [ ] Land with `VERSION` raised; `curator` records D1-D6
