---
domain: process
summary: The product is named "Supervisor for Claude" in prose and printed strings; identifiers keep the old names; a rename is a major release
affects: [deploy, README.md, docs/, pack/, VERSION]
verified: 2026-10-29
source: user 2026-10-23 ("pursue a rebrand ... to \"Supervisor for Claude\" instead of \"Claude Supervisor\" - including the entry added to git commits"); landed in 905f3b7 (v5.0)
supersedes: .supervisor/archive/memory/decisions/2026-10-23-product-name-is-supervisor-for-claude.md
---
Prose and printed strings say "Supervisor for Claude", never "Claude Supervisor", and the git trailer is `Co-Authored-By: Supervisor for Claude`. Identifiers stay: the `claude-supervisor` command, `~/.config/claude-supervisor`, the repo slug, agent and skill names. A branding change counts as a major release (`X.0`) even when the edit is small.
Why: the old name read as an Anthropic product; the new one is unambiguously not.
Rejected: renaming identifiers, which would break installs.
`deploy` keeps `LEGACY_ATTRIBUTION_COMMITS` so an installed old trailer is replaced on update; do not drop it while an install may still carry one.
