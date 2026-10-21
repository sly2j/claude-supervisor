---
domain: code
summary: A per-prefix installs.json registry maps each target to tag, remote and branch; the manifest keeps every other option
affects: [deploy, docs/deploy.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-install-lifecycle.md#approach
supersedes:
---
Every non-dry-run install records itself in the registry `<prefix>/state/claude-supervisor/installs.json`, one per prefix. Each target maps to three fields: `tag`, `remote` and `branch`.

Why the registry stays this small: launcher, base URL, settings state, prefix and pack version are already in each target's manifest (which also records `tag`, `launcher`, `prefix`, `base_url`; no schema bump, old manifests just lack the keys), and a second copy of them would drift. Rejected or deliberately left out: extra registry fields, a repair or import command, honouring `$XDG_STATE_HOME` (not asked for, and the tests would need isolation; `--prefix` already moves the state dir), and a `status --all` (superseded by `list`, which reads the registry).

Reach: product; stated in deploy:598, 603.
