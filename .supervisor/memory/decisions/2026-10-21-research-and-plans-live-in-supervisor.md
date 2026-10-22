---
domain: process
summary: Research and plans live in .supervisor/working/ and are archived to archive/working/; a legacy docs/ set moves with curator migrate
affects: [pack/agents/researcher.md, pack/agents/planner.md, pack/skills/project-memory/references/curator-procedures.md]
verified: 2026-10-22
source: .supervisor/archive/working/plans/plan-memory-stage4.md#approach
supersedes: [.supervisor/archive/memory/decisions/2026-10-21-in-v2-0-working-holds-only-writing.md, .supervisor/archive/memory/decisions/2026-10-21-research-and-plans-move-out-of-docs-at.md]
---
D3, landed at Stage 4. Research and plans live under `.supervisor/working/research/` and
`working/plans/` (`researcher` and `planner` default paths, same `research-`/`plan-` file names; a
caller-supplied path wins). The curator's close-out archives them to `.supervisor/archive/working/`
under the same file names, so `docs/` holds only human documentation and the layout of D2 is
complete.

A project whose working set is still in `docs/` moves it with `curator migrate docs/`: live files
to `working/`, spent files in `docs/archive/` distilled into entries still in force and then moved
to `archive/working/`. The curator's every-run sweep proposes it (`follow-up: curator migrate
docs/`) while `docs/` still holds `plan-*` or `research-*` files.

Why: one path switch, no new mechanism. Keeping the prefixes means a migrated file keeps its name,
so a moved `source:` resolves by name. Rejected: `plans/<topic>.md` without the prefix (renames
every migrated file and breaks lookup by name); a migration command in `deploy` (deploy never
touches projects and distillation needs judgment); new programs only (D3 decided a one-time
migration); detection in `planner` or `supervisor` (no word-cap headroom, and the curator already
runs the sweep).

Reach: product; stated in `pack/agents/researcher.md:16`, `pack/agents/planner.md:16` and
`pack/skills/project-memory/references/curator-procedures.md` (archive step, sweep, migrate).
