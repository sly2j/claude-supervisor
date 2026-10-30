---
domain: writing
summary: User docs define a pack string once, in the lifecycle page, never use brief or prompt vocabulary, and state what users need, not everything true
affects: [docs/, README.md]
verified: 2026-10-30
source: user 2026-10-29
supersedes: .supervisor/archive/memory/conventions/2026-10-26-docs-are-for-users-not-prompts.md
---
Define a pack string (such as the `Session state:` line) once, in docs/workflow-lifecycle.md, and refer to it elsewhere; use no brief or prompt vocabulary. Nothing stated may be wrong, but not everything true must be stated: write what a user needs to know, clear and correct, not exhaustive like a prompt.
Why: agent prompts need exhaustive rules; a user document loses its point when every case and mode is spelled out. The owner: "it's important that we really write it in terms of what a user needs to know, rather than be completely comprehensive or fully accurate like a prompt".
Rejected: prompt-style completeness in user docs.
