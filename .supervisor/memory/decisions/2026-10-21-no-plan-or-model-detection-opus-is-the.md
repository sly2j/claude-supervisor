---
domain: process
summary: No plan or model detection: Opus is the default and Fable is an explicit opt-in
affects: [deploy, docs/deploy.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-opus-default.md#scope-notes
supersedes:
---
The owner decided that `deploy` and the launcher never detect whether a user's plan includes Fable, and never ask. Fable agents run on Opus unless the user asks for Fable (today `claude-<tag> --fable`; earlier `install --fable`). Do not reintroduce a plan or model check, a TTY prompt, an `auto` value, or a saved Fable choice.

Why: a first design (Fable-to-Opus fallback at install time) detected the plan from `claude auth status --json` and an undocumented `~/.claude.json` seat-tier field, depending on `subscriptionType` and `seatTier` strings seen on one Team premium account only, and still had to ask or default to Opus when unclear. Dropping detection removed that code, its prompts and its test isolation, at the cost of one explicit opt-in. Rejected as creep when the default flipped: an `--opus` or `--no-fable` flag, and honoring a saved choice on later installs.

Reach: repo work.
