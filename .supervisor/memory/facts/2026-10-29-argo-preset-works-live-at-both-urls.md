---
domain: code
summary: The Argo preset works live at the Argo URL and the argo-proxy URL with the three tier ids; CLAUDE_CODE_SKIP_ANTHROPIC_AUTH is not needed
affects: [deploy, docs/deploy.md]
verified: 2026-10-29
source: user 2026-10-29
supersedes:
---
The owner ran the Argo preset inside ANL and reported all checks passed.
- Both the preset URL and an argo-proxy `--base-url` serve `claude-opus-5-5`, `claude-sonnet-5-5` and `claude-haiku-5-5` through Claude Code.
- `CLAUDE_CODE_SKIP_ANTHROPIC_AUTH` is not needed, though argo-proxy's documentation calls it required, so the preset's `env` does not set it.
Reported by the owner without a transcript; the preset's code and tier defaults need no change.
