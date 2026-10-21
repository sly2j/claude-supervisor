---
domain: code
summary: Pack version is read from the VERSION file beside pack/ and recorded in the manifest; a status MISMATCH still exits 0
affects: [deploy, docs/deploy.md, tests/test_deploy.py]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-versioning.md#approach
supersedes:
---
`deploy` reads the version from the `VERSION` file in the directory that contains the `pack/` being installed (`read_pack_version(source)` uses `source.parent`), not from the checkout `deploy` itself runs from. The install records the result in the manifest as `pack_version` and prints it on install; `status` compares the recorded version with the source's and appends a `MISMATCH` marker when they differ.

Why `source.parent`: the version recorded is then the version of whatever pack was installed, also when `--source` points at another clone, and tests can exercise the missing-file case with a temp pack and no environment hook. Consequences: no `VERSION` beside the pack is not an error (install prints `Version: unknown (no VERSION file in <dir>)` and records `null`); a manifest without `pack_version` reads as `installed=not recorded` until the next install; `status` exits 0 on a `MISMATCH` (an owner decision; a non-zero `status` exit was considered out of scope). Branch checkouts get a derived version rather than the plain file; that is described in `docs/deploy.md`.

Reach: product; stated in deploy:994, 1011 and docs/deploy.md:53.
