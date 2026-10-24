---
domain: process
summary: the product is named "Supervisor for Claude" in prose and printed strings; identifiers keep the old names; a rename is a major release
affects: [deploy, README.md, docs/, pack/, VERSION]
verified: 2026-10-23
source: user 2026-10-23 ("pursue a rebrand ... to \"Supervisor for Claude\" instead of \"Claude Supervisor\" - including the entry added to git commits"); landed in 905f3b7 (v5.0)
supersedes:
---
Reach: repo work; the name itself lives in `pack/`, `deploy` and the docs. This entry keeps the rule for future edits.

Decided (owner sjoosten): prose and printed strings say "Supervisor for Claude", never "Claude Supervisor", and the git trailer is `Co-Authored-By: Supervisor for Claude`. Identifiers stay unchanged: the `claude-supervisor` command, `~/.config/claude-supervisor`, the repo slug, agent and skill names. A branding change counts as a major release (`X.0`) even when the edit is small.
Why: the old name read as an Anthropic product; the new one is unambiguously not. Renaming identifiers would break installs and was out of scope. `deploy` keeps `LEGACY_ATTRIBUTION_COMMITS` so an installed old trailer is replaced on update; do not drop it without checking that no install still carries one.
Related: `.supervisor/memory/decisions/2026-10-23-only-git-ops-commits-memory-writes.md` (already carries the new trailer).
