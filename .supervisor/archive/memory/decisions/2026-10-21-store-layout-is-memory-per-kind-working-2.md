---
domain: process
summary: Store layout is memory/ per kind, working/ per area, archive/ mirroring both
affects: [pack/skills/project-memory/, docs/architecture.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-memory-v2.md#scope-notes
supersedes: .supervisor/archive/memory/decisions/2026-10-21-store-layout-is-memory-per-kind-working.md
---
D2, as amended at landing. `.supervisor/` is the one root: `memory/` (long-term, one file per
entry, one folder per kind), `working/` (short-term state, one folder per area: `writing/`,
`research/` and `plans/`, complete since Stage 4) and `archive/` (spent files, never read by
default, mirrors both `memory/` and `working/`, no files at its top level). A static `README.md`,
plus `roadmap.md` and `history.md`, sit at the root. Amended from the roadmap's original wording, which
had no per-kind folders and no mirror rule. Layout principle: see the decision on folders, labels
and the archive mirror.
superseded by: .supervisor/memory/decisions/2026-10-22-memory-store-design-rationale.md
