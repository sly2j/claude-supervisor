---
domain: process
summary: Agent names are actor nouns and must not collide with conventional-commit types
affects: [pack/agents/, docs/architecture.md]
verified: 2026-10-29
source: user 2026-10-25
supersedes:
---
Name a pack agent for the worker (researcher, planner, executor, fixer), never for the work, and never with a word that is a conventional-commit type (`chore`, `fix`, `docs`, `test`).
Why: a commit-type name makes briefs and grep ambiguous against commit messages, and a work name reads oddly in prose such as "dispatch `chore`".
Rejected: `chore` as the Mode 2 agent name.
