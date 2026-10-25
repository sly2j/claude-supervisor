---
name: supervisor-config
description: Switch the lead's critic between Codex and the Claude critic, or show which is active. Use when the user runs `/supervisor-config critic codex [model]`, `/supervisor-config critic claude`, or `/supervisor-config critic status`.
argument-hint: critic codex [model] | critic claude | critic status
disable-model-invocation: true
---

# Supervisor config

Switch the critic backend of this install.

Input: `$ARGUMENTS`.
- `critic codex [model]`: enable.
- `critic claude`: disable.
- `critic status`: status.
- Anything else: show these three forms and stop.

## Enable

Ask with AskUserQuestion (yes or no), showing this text verbatim:

```
Codex as critic (Supervisor for Claude):
- Codex reviews spend your OpenAI/ChatGPT quota.
- Repository content under the current directory, the review brief and the diff are sent to OpenAI.
```

Only on yes, run enable. Disable and status need no consent. Each costs one permission prompt
by design: install pre-allows only `review`, so no agent can enable Codex unasked.

## Run

The command is exactly one of the following, as a single plain command with no `cd`, pipe, `&&`
or heredoc, because a permission check matches the literal command:

```bash
"${CLAUDE_SKILL_DIR}/scripts/codex-critic" enable --yes [model]
"${CLAUDE_SKILL_DIR}/scripts/codex-critic" disable
"${CLAUDE_SKILL_DIR}/scripts/codex-critic" status
```

Run it with Bash. Without Bash (the `supervisor` main thread), dispatch `fixer` with the exact
command line, substituted path included, and relay its output.

## Report
Relay the script's output. Add that the switch takes effect from the next task, without
a reinstall.

## Models
Default `gpt-6.1-sol`; `gpt-6-astra` is also verified. Per-domain overrides go in
`supervisor-config.json` at the install's config directory, under `critic`:

```json
{"critic": {"domains": {"prose": "claude", "plan": {"model": "gpt-6-astra", "effort": "xhigh"}}}}
```

A domain value is `"claude"` (always the Claude critic) or an object with `model` and/or `effort`.
