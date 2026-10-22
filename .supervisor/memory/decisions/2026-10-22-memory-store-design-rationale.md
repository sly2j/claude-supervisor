---
domain: process
summary: Memory store design rationale: no INDEX, no status field, no time expiry, lessons only after approval, per-draft writer state
affects: [pack/skills/project-memory/, pack/agents/curator.md, pack/agents/writer.md]
verified: 2026-10-22
source: .supervisor/archive/working/plans/plan-memory-v2.md, .supervisor/archive/working/plans/plan-memory-stage4.md, user 2026-10-18 and 2026-10-21
supersedes: [.supervisor/archive/memory/decisions/2026-10-21-store-layout-is-memory-per-kind-working-2.md, .supervisor/archive/memory/decisions/2026-10-21-folders-hold-fixed-properties-labels.md, .supervisor/archive/memory/decisions/2026-10-21-one-file-per-entry-kinds-decision-fact.md, .supervisor/archive/memory/decisions/2026-10-21-memory-holds-decisions-then-facts.md, .supervisor/archive/memory/decisions/2026-10-21-history-md-holds-one-line-per-landed.md, .supervisor/archive/memory/decisions/2026-10-21-three-horizons-goals-roadmap-supervisor.md, .supervisor/archive/memory/decisions/2026-10-21-research-and-plans-live-in-supervisor.md, .supervisor/archive/memory/decisions/2026-10-21-expiry-flags-an-entry-when-its-affects.md, .supervisor/archive/memory/decisions/2026-10-21-writing-rules-are-conventions-per-draft.md, .supervisor/archive/memory/decisions/2026-10-21-writer-state-is-one-file-per-draft-keyed.md]
---
Behaviour is in `pack/skills/project-memory/`; this keeps the why and the rejected options.

- Folders hold fixed properties (an entry's kind, a working-set area), labels hold changing ones
  (`domain:`). No `status:` field: a status change is a move into the mirroring `archive/`, and the
  file says why in one added line (`superseded by:`, `met:`, `dropped:`). The no-status choice was
  accepted by the user 2026-10-18, vetoable at review. The store README is static, copied once, so
  collaborators read the layout without the pack.
- No generated `memory/INDEX.md`: kind folders plus `grep -r '^summary:'` list the store, always
  current and never a merge conflict. One file per entry replaced the single `docs/decisions.md`.
- No time-based expiry: an entry is flagged only when an `affects:` path changes or goes missing
  since `verified:`. Revisit for `fact` entries only if staleness is observed.
- Lessons exist only after user approval, because over-general or wrong entries compound
  (arXiv 2505.16067). The curator proposes them in its report.
- `history.md` is one line per landed roadmap item, never per commit or dispatch; the roadmap holds
  only what is next, so it has no archive. Program logs live in each plan's `## Log`, not a
  separate logbook.
- The roadmap stays at `.supervisor/roadmap.md`; a root `ROADMAP.md` human page and a split
  (short root roadmap plus item list) were rejected (user 2026-10-21: not useful for external
  users).
- Research and plans moved into `working/` with their `research-`/`plan-` prefixes, so a migrated
  file keeps its name and a moved `source:` resolves by name. Rejected: unprefixed `plans/<topic>.md`
  (breaks lookup by name); a migration command in `deploy` (it never touches projects, and
  distillation needs judgment); new programs only; detection in `planner` or `supervisor` (no
  word-cap headroom, the curator's sweep already proposes `curator migrate docs/`).
- Writing rules are `convention` entries with `domain: writing`; the skill `writing-rules-persistence`
  was folded into `project-memory` since one skill describes one store. Per-draft state is
  `working/writing/<key>.md` (`<key>` is the draft path with `/` as `--`). Rejected:
  `<draft>.state.md` beside the draft (pollutes user directories) and a project-wide Pending
  Verification file (a second location for writing state). A pattern seen once stays a note about
  its draft until the user promotes it.
