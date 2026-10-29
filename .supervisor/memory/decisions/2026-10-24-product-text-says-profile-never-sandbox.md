---
domain: process
summary: Product text says "profile", never "sandbox", for a private Claude Code config dir with its own launcher
affects: [README.md, docs/deploy.md, deploy, tests/]
verified: 2026-10-29
source: user 2026-10-24 ("yes, use profile throughout all documents will improve things."; "memory should be up-to-date so it should be fixed. Either rewrite or supercede")
supersedes: .supervisor/archive/memory/decisions/2026-10-24-product-term-is-profile-not-sandbox.md
---
A profile is a private config dir `~/.config/claude-<tag>` with its own launcher; several coexist via `--tag`, and `--global` installs into `~/.claude` instead. Identifiers (flags, tags, file names) are unchanged.
Why: "sandbox" implies security isolation, which the install does not give; "profile" matches the browser-profile mental model.
Rejected: keeping "sandbox" with a disclaimer.
