---
domain: code
summary: Launcher remaps Fable to Opus via ANTHROPIC_DEFAULT_FABLE_MODEL; installed agents keep model: fable and --fable opts out
affects: [deploy, docs/deploy.md, README.md, pack/agents/planner.md, pack/agents/writer.md]
verified: 2026-10-22
source: .supervisor/archive/working/plans/plan-install-lifecycle.md#approach
supersedes: .supervisor/archive/memory/decisions/2026-10-21-launcher-remaps-fable-to-opus-installed.md
---
Deployed agent files say `model: fable` byte for byte as in `pack/`; there is no install-time rewrite. Each `claude-<tag>` launcher exports `ANTHROPIC_DEFAULT_FABLE_MODEL` set to the `OPUS_MODEL` constant in `deploy` (currently `claude-opus-5-5`), so the three Fable agents (`supervisor`, `planner`, `scope-critic`) and the prose `model: fable` dispatch overrides (`planner` to `critic`, `writer` to `writer-worker`) run on Opus. A `--fable` in any position before a `--` (first argument only until 3.2; owner, 2026-10-22) strips the flag and unsets the variable for that session, which runs them on Fable. Why: Fable is billed separately on some plans, so Opus is the default and Fable is a per-session choice.

Details that bind later changes. The value is a full model ID, not the `opus` alias (the variable requires a full name), and is updated by hand with each Opus release, then `install` is re-run to regenerate launchers. The pack source and the `agent-authoring` tier table keep saying `fable`. The dispatch overrides follow the remap with no pack edit, because the variable controls what the `fable` alias resolves to. The owner's by-hand check that such a dispatch really reports Opus under the default launcher was still open in the source plan, so treat that point as assumed, not verified.

Rejected: `CLAUDE_CODE_SUBAGENT_MODEL` (it overrides every subagent, Haiku and Sonnet ones included, instead of remapping only `fable`); an install-time rewrite of agent files to `opus` plus an install `--fable` flag and manifest key (the earlier design, replaced by the launch-time switch).

Reach: product; stated in docs/deploy.md:129 and deploy:48.
superseded by: .supervisor/memory/decisions/2026-10-22-launcher-design-rationale.md
