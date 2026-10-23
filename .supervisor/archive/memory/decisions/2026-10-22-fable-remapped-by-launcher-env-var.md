---
domain: code
summary: Fable is remapped to Opus by a launcher env var; agent files keep model: fable
affects: [deploy, docs/deploy.md]
verified: 2026-10-22
source: .supervisor/archive/working/plans/plan-install-lifecycle.md; user 2026-10-22
supersedes: .supervisor/archive/memory/decisions/2026-10-22-launcher-design-rationale.md
---
The launcher exports `ANTHROPIC_DEFAULT_FABLE_MODEL` as a full model ID, updated by hand per Opus release; deployed files are not rewritten.
Why: Fable is billed separately on some plans. Rejected: `CLAUDE_CODE_SUBAGENT_MODEL` (overrides every subagent, Haiku and Sonnet too) and an install-time rewrite with an install `--fable` flag and manifest key. Unchecked: that a `model: fable` dispatch really reports Opus.
superseded by: .supervisor/memory/decisions/2026-10-23-fable-is-default-opus-is-opt-in.md
