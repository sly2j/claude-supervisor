---
domain: code
summary: Update clones the recorded remote and hands off to the clone's own deploy, which replays the install's recorded options
affects: [deploy, docs/deploy.md]
verified: 2026-10-21
source: .supervisor/archive/working/plans/plan-install-lifecycle.md#approach
supersedes:
---
`deploy update` (one install, or `--all`) does not reinstall from the old tool copy. It clones the recorded remote and branch into a temp dir and runs `<clone>/deploy update --from <clone> --prefix <prefix> <selection> --yes`, so the newest code replays each install's recorded options. Why: the old copy would replay flags newer code may have removed (the removed `--fable` install flag was the concrete case), and the newest code knows the newest manifest and launcher format. Under `--all`, `--from` processes only entries whose remote and branch match the clone's, so each clone deploys only to its own group. Update needs git and network or ssh access, and it only sees what is pushed to the followed branch; a clone of an older branch without `update --from` fails in argparse, so push before relying on update.

Replay passes `--no-default-agent` when the manifest says the pack does not manage the `agent` key (else the reinstall retakes it) and never `--overwrite-local`. Git runs with no env tweaks, so ssh passphrase prompts work.

Consequences: installs made before the registry existed must run `./deploy install` once; after an update, the manifest's `source_dir` names the deleted temp clone, so `status` needs `--source` to compare versions.

Reach: product; stated in deploy:1333.
