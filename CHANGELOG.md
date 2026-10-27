# Changelog

Major versions only; minor versions are in `git log`.

- **v8** (2026-10-27): installs can target an API provider: presets (OpenRouter, NRP, ALCF) and a generic `--base-url`, per-tier model picks with `--model-<tier>` flags, and a managed `apiKeyHelper` for expiring tokens. See [API Providers](docs/deploy.md#api-providers).
- **v7** (2026-10-24): optional Codex CLI backend for the critic, with the Claude critic as automatic fallback; switch with `deploy critic` or `/supervisor-config critic`. See [Codex As Critic](docs/deploy.md#codex-as-critic).
- **v6** (2026-10-24): major architectural change to improve token efficiency, by letting leads work directly on smaller tasks and by optimizing the review cycle.
- **v5** (2026-10-23): rebrand to Supervisor for Claude.
- **v4** (2026-10-22): project-aware git workflow: agents follow a repo's own versioning scheme, and larger changes are developed on their own branch in a worktree.
- **v3** (2026-10-21): token efficiency: the planner no longer writes code in plans, which was redundant with the executor's work; plans are split into vertical slices (work packages) that execute in parallel waves.
- **v2** (2026-10-21): persistent per-project memory.
- **v1** (2026-10-15): first version of Supervisor for Claude: a supervisor that routes each request to the full harness or to fast specialists, with a standard-library deploy script.
