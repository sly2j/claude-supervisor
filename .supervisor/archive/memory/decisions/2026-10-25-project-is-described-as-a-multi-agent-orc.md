---
domain: process
summary: The project is described as "a multi-agent orchestration layer for Claude Code", never as a "harness" or merely an "agent pack"
affects: [README.md, CLAUDE.md, docs/]
verified: 2026-10-25
source: user 2026-10-25
supersedes:
---
Descriptions of the project say "a multi-agent orchestration layer for Claude Code". "Pack" stays for the deployable unit under `pack/` that `deploy` installs, and "Mode 1: full harness" stays as the internal workflow-depth term in `pack/agents/supervisor.md`.
Why: "harness" names the runtime around the model; Claude Code is the harness and this project runs on top of it, replacing none of its loop, tools or permissions, so the word conflates two layers. "Pack" undersells the orchestration: supervisor routing by mode, leads fanning out to workers, critic and scope-critic loops, plan and program contracts, committed project memory with a curator.
Rejected: "harness" (layer confusion); "agent pack" or "workflow pack" as the project description (undersell).
A tagline change is not a rebrand: the product name is unchanged (see `.supervisor/memory/decisions/2026-10-24-the-product-is-named-supervisor-for-clau.md`) and the major-release rule there does not apply.
superseded by: .supervisor/memory/decisions/2026-10-26-mode-1-is-the-full-loop.md
