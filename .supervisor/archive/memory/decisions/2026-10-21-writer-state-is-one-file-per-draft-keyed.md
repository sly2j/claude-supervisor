---
domain: writing
summary: Writer state is one file per draft, keyed by draft path, Pending Verification per draft
affects: [pack/skills/project-memory/references/writing.md, pack/skills/project-memory/templates/draft-state.md]
verified: 2026-10-21
source: docs/archive/plan-memory-v2.md#approach
supersedes: 
---
Per-draft state lives in `.supervisor/working/writing/<key>.md`, `<key>` the draft path relative to
the project root with `/` replaced by `--`; it holds that draft's Session Decisions and Pending
Verification. Drafts stay user files and nothing is written beside them. Pending Verification is
per draft: a pattern seen once is a note about that draft until the user promotes it to a
convention. Rejected: `<draft>.state.md` beside the draft (pollutes user directories), a
project-wide Pending Verification file (a second location for writing state).
superseded by: .supervisor/memory/decisions/2026-10-22-memory-store-design-rationale.md
