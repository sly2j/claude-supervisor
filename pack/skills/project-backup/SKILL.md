---
name: project-backup
description: Create a timestamped, integrity-checked zip backup of the current project directory and prune older backups with tiered retention (recent, weekly, monthly, half-yearly). Use when the user asks to back up, snapshot, or archive the project or vault before risky changes, or asks to run "the backup". Not for git commits, remote sync, or restoring from a backup.
context: fork
---

# Project backup

Create `<ProjectName>-YYMMDD-HHMMSS.zip` of the current working directory, verify it with
`zip -T`, and prune older managed backups using the bundled retention policy.

## Run

From the project root:

```bash
"${CLAUDE_SKILL_DIR}/scripts/backup.sh"
```

The default backup directory is `../backups` (a sibling of the project). To override it, set
`PROJECT_BACKUP_DIR` (absolute or relative):

```bash
PROJECT_BACKUP_DIR=/path/to/backups "${CLAUDE_SKILL_DIR}/scripts/backup.sh"
```

Only create backups and prune backups this script created. Never point the backup directory inside
the project. Do not inspect project content beyond what archiving requires.

## What the script does

- Refuses (`FATAL`) if the backup directory resolves to the project root or anywhere inside it.
- Warns, but continues, when less than 1 GB is free.
- Excludes local caches and churn: `.claude/worktrees/`, `.DS_Store`, Obsidian workspace state,
  `.trash/`, and smart-connections indexes.
- Removes the archive and exits `FATAL` if `zip` or `zip -T` fails.
- Retention (only files matching exactly `<ProjectName>-YYMMDD-HHMMSS.zip`):
  - keep the 7 most recent;
  - then the newest per ISO week for the 4 completed weeks before the current week;
  - then the newest per month in the current calendar year;
  - then the newest per half-year (Jan-Jun, Jul-Dec) in prior years;
  - always keep at least 3 managed backups.
- Files with unparseable names are skipped, never deleted, and counted as `Skipped`.
- Prints a `=== BACKUP REPORT ===` block.

The script needs bash 3.2+, `zip`, and BSD or GNU `date` (macOS or Linux).

## Report

Confirm the script exited 0 with `Integrity: PASSED` and relay the `BACKUP REPORT` block
(archive path, size, retained/deleted/skipped counts, warnings). On a non-zero exit, relay the
`FATAL` line and do not retry with a different backup directory unless the user asks.
