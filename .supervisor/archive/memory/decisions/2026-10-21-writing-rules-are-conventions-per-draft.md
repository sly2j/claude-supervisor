---
domain: writing
summary: Writing rules are conventions; per-draft state lives under working/writing/
affects: [pack/skills/project-memory/, pack/agents/writer.md]
verified: 2026-10-21
source: docs/archive/plan-memory-v2.md#scope-notes
supersedes: 
---
D8, as amended at landing. Standing Rules become `convention` entries with `domain: writing`
(no `kind:` field; the folder is the kind). Per-draft Session Decisions and Pending Verification
live in `.supervisor/working/writing/<key>.md` and move to `archive/working/writing/` with the
draft; `docs/writing-rules.md` goes away (`curator migrate` converts an existing one). The skill
`writing-rules-persistence` was folded into `project-memory` (`references/writing.md`) rather than
reworked: one skill describes one store. Claude Code auto memory keeps personal cross-project
preferences.
superseded by: .supervisor/memory/decisions/2026-10-22-memory-store-design-rationale.md
