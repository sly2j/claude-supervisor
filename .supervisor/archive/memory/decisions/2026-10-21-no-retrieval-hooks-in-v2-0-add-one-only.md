---
domain: process
summary: No retrieval hooks in v2.0; add one only after an observed retrieval failure
affects: [pack/agents/supervisor.md]
verified: 2026-10-24
source: docs/archive/plan-memory-v2.md#open-questions
supersedes: 
superseded by: .supervisor/memory/decisions/2026-10-24-no-sessionstart-or-subagentstart-hook.md
---
D10 (OQ2, default accepted 2026-10-18). No SessionStart or SubagentStart hook in v2.0. Stage 5
(conditional) adds one only when a relevant entry was observed missed in Stages 1-4.
