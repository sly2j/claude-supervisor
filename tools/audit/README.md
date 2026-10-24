# Harness audit

Opt-in re-measurement of harness efficiency from local Claude Code transcripts. It is never run by default and is not part of pytest or deploy. Standard library only, Python 3.9+.

## Run

```
mkdir -p tools/audit/out
python3 -I tools/audit/audit.py > tools/audit/out/run.md
```

`tools/audit/out/` is gitignored; never commit its contents.

`-I` is isolated mode: Python ignores the environment and the current directory's modules. The script reads untrusted transcript data, so nothing from the surrounding directory may be imported.

## Flags

- `--root DIR`: transcript root to scan; repeatable. Default: `~/.config/claude-supervisor/projects` and `~/.claude/projects`. In the latter, only sessions that dispatched a pack agent count.
- `--since YYYY-MM-DD`: ignore sessions before this date.

## Metrics

Output is markdown tables on stdout:

- Critic round-1 PASS rate, by lead
- Round-1 empty and NIT-only-or-empty findings-table rates, by lead
- Scope-critic dispatches per critic round, and logged skips
- Lead-tree tokens per run: lead, workers, reviewers
- Files read by two or more workers of one run
- Quick-tier ESCALATE rate
- Main-thread final context: median and max
- Corpus counts

## Privacy

Output carries only aggregates and 8-character session prefixes. Transcript text is never printed. The script exits 2 rather than print a line matching `[/-](Users|home)[/-]` or a transcript working directory.
