---
domain: process
summary: The product term for a private Claude Code config dir with its own launcher is "profile", never "sandbox"
affects: [README.md, docs/deploy.md, deploy, tests/]
verified: 2026-10-24
source: user 2026-10-24 ("yes, use profile throughout all documents will improve things."; "memory should be up-to-date so it should be fixed. Either rewrite or supercede")
supersedes:
---
Reach: product wording, written into README, docs and `deploy` strings by executor in the same change set; live memory entries were reworded to match.

A profile is a private config dir `~/.config/claude-<tag>` with its own launcher; several coexist via `--tag`. `--global` installs into `~/.claude` instead.
Why: "sandbox" implies security isolation, which the install does not give, and needed a disclaimer; "profile" matches the browser-profile mental model. Rejected: keeping "sandbox" with the disclaimer.
Identifiers (flags, tags, file names) are unchanged. Archived entries and file names keep the old word as history.
