---
domain: writing
summary: Mode 1 is called "the full loop" everywhere, and the project is described as an orchestration layer, never a harness; lead-loop is only a skill name
affects: [README.md, docs/architecture.md, docs/context-engineering.md, pack/agents/supervisor.md, CLAUDE.md]
verified: 2026-10-29
source: user 2026-10-26
supersedes: .supervisor/archive/memory/decisions/2026-10-25-project-is-described-as-a-multi-agent-orc.md
---
Descriptions say "a multi-agent orchestration layer for Claude Code". "Pack" stays for the deployable unit under `pack/`. Mode 1 is "the full loop" in prose and in `supervisor.md`; `lead-loop` names only the skill.
Why: "harness" names the runtime around the model; Claude Code is that harness and this project runs on top without replacing its loop, tools or permissions. "Pack" undersells the orchestration. "Full harness" reused the confusing word.
Rejected: "harness" as the project or mode description; "agent pack" or "workflow pack" as the project description; "lead loop" as the mode name.
A tagline change is not a rebrand: see `.supervisor/memory/decisions/2026-10-24-the-product-is-named-supervisor-for-clau.md`.
