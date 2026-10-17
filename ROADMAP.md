# Roadmap

## Context

- This repo is the source of a Claude Code agent pack. `pack/` deploys via `deploy`
  (stdlib-only, Python 3.9, which macOS ships as `/usr/bin/python3`).
- Work goes through the supervisor harness: `researcher`/`planner`/`executor`/`writer` leads with
  worker fan-out and `critic`/`scope-critic` loops; quick tier `quick-edit`/`git-ops`/`scout`.
- Before touching the pack, read `CLAUDE.md`, `docs/architecture.md`, and the `agent-authoring`
  skill (`pack/skills/agent-authoring/SKILL.md`).
- Per change set on `main`: edit, bump `VERSION` once (`1.x` -> `1.x+1`), run
  `python3 -m pytest -q`, run `./deploy install` if `pack/` changed, commit with the trailer
  exactly `Co-Authored-By: Claude`, push.
- Plans live in `docs/plan-<topic>.md`; finished plans move to `docs/archive/` with `git mv`.
  Long tasks may use work packages (`## Work Packages` in the plan; see README).
- Owner's style rule is simplicity: add rules to agent files only for observed failures, no
  anticipated-failure clauses, keep word counts and line lengths down. Body word caps per tier
  are linted in `tests/test_pack_lint.py`; do not raise a cap without the owner's approval.
- Items are ordered; each states its dependencies under "Decisions already made". Pick one item
  per change set; remove it from this file in the same commit when it lands.

## Items

### 0. Plumbing for major releases and branches

- **Goal:** let a major feature branch land as `X.0`, and make every install follow the branch
  it was installed from instead of always `main`.
- **Background:**
  - `tests/test_version.py` already accepts `1.17` -> `2.0`: `FORMAT` (L11) allows any major and
    `bump_ok` (L29-31) compares `(int, int)` tuples. Its cases (L39-45) cover only `1.x`.
  - `CLAUDE.md:10-11` state the `1.x` rule and the rebase + squash-merge landing rule. L10 says
    `git-ops` stages `VERSION` and escalates on `main`, but `grep -rn VERSION pack/` is empty:
    `pack/agents/git-ops.md` has no VERSION logic.
  - Install metadata: the registry `<prefix>/state/claude-supervisor/installs.json` records
    `{tag, remote}` per target (`deploy:499-526`; `register_install` at L741 uses `git_remote`,
    L361, `git remote get-url origin`). The manifest `<target>/.claude-supervisor-manifest.json`
    (`deploy:711-723`) records no remote and no branch.
  - `update_cmd` (`deploy:963-1043`) shallow-clones with `--branch main` hard-coded (L1030), then
    replays `<clone>/deploy update --from <clone>`. The launcher (`launcher_text`, `deploy:46-65`)
    intercepts `update|uninstall` and execs the tool copy with `--prefix --tag --target
    --launcher`, so one change in `update_cmd` covers both entry points.
  - Exit codes: `main()` (`deploy:1280-1289`) returns 2 for `DeployError`, 130 on interrupt, else
    the handler's 0 or 1; `docs/deploy.md:147` documents 0, 1, and 2.
  - `--tag` (default `supervisor`, `deploy:38`) sets `~/.config/claude-<tag>` and
    `<prefix>/bin/claude-<tag>`. Nothing pins the source to the main checkout, so
    `./deploy install --tag supervisor-dev` from a worktree already yields a separate install; the
    missing piece is the recorded branch.
- **Scope:**
  - In: major-bump acceptance (test cases for `1.x` -> `2.0`, `CLAUDE.md` wording, and whichever
    `git-ops` rule exists or the planner adds); record the git branch in the registry next to the
    remote; `update` (both `./deploy update` and `claude-<tag> update`) clones the recorded
    branch; the gone-branch case reports and exits non-zero with a documented code; a
    `CLAUDE.md` policy line on frequent rebase; `docs/deploy.md` and `README.md` on
    branch-following and dev-tag installs; tests for each.
  - Out: item 1's review findings; any change to the squash-merge landing rule; registry format
    changes beyond adding a key.
- **Decisions already made:**
  - The squash-merge commit of a major feature branch sets `X.0`; the minor-bump rule otherwise
    stays, and feature branches still never touch `VERSION`. `tests/test_version.py`, the
    `CLAUDE.md` VERSION rule, and `git-ops`' VERSION check must accept it.
  - Installs record their git branch alongside the remote. `deploy update` and launcher `update`
    pull the recorded branch, not always `main`.
  - If the recorded branch no longer exists on the remote, update reports "nothing to update;
    branch <x> is gone, this install is stale" and recommends `claude-<tag> uninstall`, rather
    than failing with a clone error. It exits non-zero in a documented way.
  - Policy in `CLAUDE.md`: feature branches rebase on `main` frequently. The existing rebase +
    squash-merge landing rule stays.
  - A dev worktree deploys under its own tag (e.g. `--tag supervisor-dev`), and its update follows
    its recorded branch.
  - Lands before item 1, so the review covers it.
- **Left to planner:** the exit code for the gone-branch case (1, 2, or a new documented code);
  whether `git-ops` gets the VERSION rule `CLAUDE.md:10` attributes to it or L10 is corrected;
  the reading of a registry entry with no branch key (`main` is the compatible choice).
- **Done when:** `tests/test_version.py` has a passing case for `1.17` -> `2.0`; `./deploy
  install` from a branch checkout records that branch; `update` on that install clones it;
  `update` on an install whose branch is gone prints the stale message and exits with the
  documented code (covered by a test against a local bare remote); `claude-supervisor-dev update`
  from a worktree install follows its branch; `CLAUDE.md`, `docs/deploy.md`, `README.md`, and
  the `VERSION` line in this file's Context are updated; `python3 -m pytest -q` passes.
- **Pointers:** `tests/test_version.py`; `CLAUDE.md:10-11`; `pack/agents/git-ops.md`; `deploy`
  (ranges in Background); `docs/deploy.md` (Update L66, exit codes L147); `README.md`
  (Maintaining An Install L161); `tests/test_deploy.py`
  (`test_update_from_remote_replays_options`, `test_update_all`, `test_launcher_update_yes`,
  `test_stale_entry_skipped_by_update_and_pruned_by_uninstall`, `test_tag_with_target_dir`).

### 1. Full code review and new-user usability review

- **Goal:** fix what a full code and usability review of `deploy`, `tests/`, and `pack/` finds,
  and start `REVIEW.md` so critic reuses the checklist in every later review.
- **Background:**
  - Hosted on eicweb GitLab (`origin`) with a GitHub mirror at
    `github.com/sly2j/claude-supervisor`, which the docs' clone URL uses. Anthropic's managed
    GitHub Code Review reads `REVIEW.md`; the local `/code-review` does not.
  - No `REVIEW.md` exists and nothing references one. `pack/agents/critic.md` loads project rules
    only for prose (`docs/writing-rules.md` via `writing-rules-persistence`, L42-44) and the
    `agent-authoring` skill for agent definitions (L45). It states no precedence between the
    brief's contract and other rules; the only precedence stack in the pack is
    `pack/skills/writing-rules-persistence/SKILL.md:24-32`. Its body is 543 words against the
    Review-tier cap of 600 (`tests/test_pack_lint.py:21`).
  - `CLAUDE.md` has no review-only rules today; pack review guidance lives in
    `pack/skills/agent-authoring/SKILL.md` ("Reviewing Definitions (for critic)") and
    `docs/architecture.md:50-55`.
  - The journey spans `README.md` Quick Start through Troubleshooting and `docs/deploy.md` Steps
    through Migrate. `doctor` prints PASS/WARN/FAIL rows and exits 1 only on a FAIL.
  - Tests: `tests/test_deploy.py` (92, `deploy` as a subprocess against temp dirs),
    `tests/test_pack_lint.py` (120), `tests/test_version.py` (7).
- **Scope:**
  - In: code review of `deploy`, `tests/`, and `pack/` for correctness, resilience, and edge
    cases. Usability review for non-expert users across the whole journey: cloning, install
    choices (sandbox vs `--global`, PATH, token), first launch, update, migrate, uninstall; whether
    error messages and `doctor` output say what went wrong and what to do next; whether `README.md`
    and `docs/deploy.md` match the tool's actual behavior. Fixes for the findings; `REVIEW.md`;
    the `critic` change (see Decisions).
  - Out: new `deploy` features; raising a word cap; rewrites beyond the findings; item 0's work.
- **Decisions already made:**
  - Output: fixes for the findings plus this repo's first `REVIEW.md`, built from the review's
    checklist. Review-only rules move out of `CLAUDE.md` into it.
  - `critic` loads project review rules when present: root `REVIEW.md`, plus a `REVIEW.md` in any
    subdirectory containing changed files (mirroring Anthropic's Code Review convention). When
    none exist, critic reviews as today. Precedence: the brief's contract, then `REVIEW.md`, then
    critic's defaults. `REVIEW.md` never overrides the user's task decisions. This must work
    across projects with different conventions, where the file is sometimes present and
    sometimes not.
  - Depends on item 0.
- **Left to planner:** how critic finds "subdirectories containing changed files" for
  non-code domains (the artifact's directory is the natural reading); whether the critic rule fits
  in the 57 words of cap headroom or earns a shorter checklist elsewhere; how to split the review
  into packages (code review, usability review, critic change) within one item.
- **Done when:** every finding is fixed or recorded as rejected with a reason; `REVIEW.md` exists
  at the root and `CLAUDE.md` holds no review-only rules; critic loads `REVIEW.md` per the
  precedence above and still passes `tests/test_pack_lint.py`; `README.md` and `docs/deploy.md`
  match `deploy`'s behavior for every journey step; `python3 -m pytest -q` passes.
- **Pointers:** `deploy`; `tests/`; `pack/agents/critic.md`; `pack/skills/agent-authoring/SKILL.md`;
  `pack/skills/lead-loop/SKILL.md:49-65` (critic inputs);
  `pack/skills/writing-rules-persistence/SKILL.md:24-32`; `docs/architecture.md:37,50-55,90`;
  `README.md`; `docs/deploy.md`; `CLAUDE.md`.

### 2. Persistence for long programs (v2.0)

- **Goal:** carry decisions and run history across long multi-package programs.
- **Background:** the earlier gate (run the work-package flow on a real multi-package task) was
  met by the install-lifecycle program (`docs/archive/plan-install-lifecycle.md`, P1-P4 at
  L326-365). Gaps observed there:
  - A mid-program user decision (`--prefix`, `## Decisions` item 6, L408-415) was recorded only in
    the plan's ad hoc `## Decisions` section, which is now archived. `pack/agents/planner.md`
    lists no such section, and `pack/agents/supervisor.md:66-69,88` passes decisions only inside
    briefs and re-runs.
  - Glue Todo items (commit + install for P1-P4: L422, L428, L433, L437) were left unticked
    because installs were deferred; nothing records why.
  - No `docs/decisions.md`, logbook, or `## Assumptions` section exists anywhere in `pack/`,
    `docs/`, or `README.md`; `docs/archive/plan-wbs.md:276` excluded them explicitly.
- **Scope:**
  - In, in order of value: per-project `docs/decisions.md` (append-only, one line per decision);
    a run logbook index (one line per top-level dispatch); an `## Assumptions` section in plans.
  - Out: a standalone RAID register; issues separate from Todo (both rejected).
- **Decisions already made:**
  - The owner chooses which candidates to adopt; implement them with the minimum rule text.
  - Development happens on a feature branch in a separate git worktree, deployed under a dev tag
    (item 0's `--tag supervisor-dev` flow) so the stable sandbox is untouched. It may change
    designs that are not ready for general users.
  - Lands as v2.0 via item 0's major-bump plumbing. Depends on items 0 and 1.
- **Left to planner:** which agent writes `docs/decisions.md` and the logbook (`supervisor` via
  `quick-edit`, or the lead that took the decision); where the tier word caps bind, since every
  candidate adds rule text to Main or Lead agents.
- **Done when:** the owner has chosen which candidates to adopt and they are implemented with the
  minimum rule text on the branch; the branch is rebased on `main` and squash-merged with
  `VERSION` set to `2.0`.
- **Pointers:** `docs/archive/plan-install-lifecycle.md` (`## Decisions` L394-415, `## Todo`
  L417+); `README.md` (Larger Work L74-140, work packages L78-91); `docs/architecture.md:43-60`;
  `pack/agents/planner.md:24-32,75-81`; `pack/agents/supervisor.md:66-69,79-92`;
  `pack/agents/executor.md:28-30,61`.
