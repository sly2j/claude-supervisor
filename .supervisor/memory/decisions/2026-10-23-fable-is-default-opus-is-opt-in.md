---
domain: code
summary: Launcher runs Fable by default; Opus is the explicit opt-out (--fable-is-opus or env var)
affects: [deploy, docs/deploy.md]
verified: 2026-10-27
source: user 2026-10-23; commit 9426bfa
supersedes: .supervisor/archive/memory/decisions/2026-10-22-fable-remapped-by-launcher-env-var.md
---
Fable is the default tier; choosing Opus is the user's explicit act, either `--fable-is-opus` per session or their own `ANTHROPIC_DEFAULT_FABLE_MODEL` in the environment, which the launcher never overrides unasked. The old `--fable` flag is retired; agent files keep `model: fable`.
Why: the user wanted Fable as the default and the earlier Opus-by-default launcher was "not quite what I wanted". The earlier rejections stand: `CLAUDE_CODE_SUBAGENT_MODEL` (overrides every subagent) and an install-time rewrite.
