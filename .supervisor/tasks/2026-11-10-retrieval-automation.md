---
summary: Inject active entry summaries at session or subagent start
status: blocked
owner: 
since: 
plan: 
depends: []
decisions:
  - .supervisor/memory/decisions/2026-10-24-no-sessionstart-or-subagentstart-hook.md
---
Goal: Relevant memory arrives without an explicit lookup step.
Scope: A SessionStart or SubagentStart hook injecting active entry summaries, shipped in supervisor.md frontmatter.
Done when: It fixes an observed failure, a relevant entry missed at contract time.
Notes: Blocked: start only after an observed missed-entry failure.
