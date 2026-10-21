---
domain: process
summary: Folders hold fixed properties, labels changing ones; no status field; static store README
affects: [pack/skills/project-memory/, pack/skills/project-memory/templates/store-readme.md]
verified: 2026-10-21
source: docs/archive/plan-memory-v2.md#approach
supersedes: 
---
An entry's kind and a working-set area never change, so they are folders and nothing else;
`domain:` stays a label. A status change is a move into `archive/`, which mirrors the live tree, so
there is no `status:` field: an archived file says why in one added line, `superseded by:`, `met:`
or `dropped:`. Supersede, never edit: the replacement carries `supersedes:`, the old file gains its
line and is moved in the same step. A static `README.md` is copied from the skill template when
`.supervisor/` is created, so collaborators can read the layout without the pack; agents never
edit it. Accepted by the user 2026-10-18 (the no-status choice as recommended, vetoable at review,
OQ9).
