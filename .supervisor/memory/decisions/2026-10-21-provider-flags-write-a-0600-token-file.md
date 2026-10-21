---
domain: code
summary: Provider flags write a 0600 token file in a 0700 sandbox dir; the secret never reaches the manifest, settings or output
affects: [deploy, docs/deploy.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-sandboxed-install.md#scope-notes
supersedes:
---
For a proxy or gateway, sandbox `install` accepts `--base-url URL` and one of `--token-file PATH` or `--token VALUE` (mutually exclusive in argparse; `--global` rejects all three). The token goes to `<dir>/token` (mode 0600, via a temp file that starts 0600) and the launcher exports exactly `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` (the latter read from that file at run time). A new sandbox dir is created 0700 unconditionally, because it also holds login state and history.

The secret never appears in the manifest, `settings.json`, install output or `status` output; the manifest records only the base URL, and token state is simply whether `<dir>/token` exists. A later plain `install` keeps both (the launcher is regenerated from the manifest URL and the token file); `--base-url ''` clears the URL and deleting `<dir>/token` drops the token line at the next install, which was the least-code way to express "keep unless told otherwise". `--token VALUE` stays available but leaves the value in shell history, so the docs prefer `--token-file`. Neither URL nor token is validated.

Reach: product; stated in deploy:898.
