---
domain: code
summary: Installs are stand-alone of the deploy source dir; version and update info come from the install's own record
affects: [deploy, docs/deploy.md]
verified: 2026-10-21
source: user 2026-10-21
supersedes:
---
User, verbatim: "and we should assume by default to be independent of the deploy directory as it may have changed for multiple reasons, or been deleted. Like any other program it has to be stand-alone."

Applies to `deploy` installs: the claude-<tag> launcher, the installed tool copy under <prefix>/state, `deploy update`, `--version` and the downgrade guard. An installed instance must not depend on the source checkout it was deployed from, which may have moved, changed or been deleted. Version and update information come from what the install itself recorded (manifest / installs.json), not from reading the source tree. Consequence: any code path that requires the source checkout at run time of an installed instance is a defect, except where the user names a source explicitly (e.g. `update` pointed at a checkout). Reading the recorded source checkout is allowed only as an optional extra that applies when the checkout still exists and whose absence changes no result: `status` reads the manifest alone and adds a comparison against the recorded source checkout only when it exists (otherwise "source not available", never MISMATCH). `--version` of the tool copy reads a VERSION file recorded at install, and `update` clones the recorded remote.
