#!/usr/bin/env bash
set -euo pipefail
# Compatible with bash 3.2+ (stock macOS). No associative arrays.
# Date parsing works with BSD date (macOS) and GNU date (Linux).
SORT_TMP=""
SORT_TMP2=""
cleanup() {
  if [ -n "$SORT_TMP" ]; then rm -f "$SORT_TMP"; fi
  if [ -n "$SORT_TMP2" ]; then rm -f "$SORT_TMP2"; fi
}
trap cleanup EXIT

# fmt_date YYYY-MM-DD OUTFMT - format a calendar date with BSD or GNU date
fmt_date() {
  date -j -f '%Y-%m-%d' "$1" "+$2" 2>/dev/null || date -d "$1" "+$2" 2>/dev/null
}

# Configuration
PROJECT_ROOT="$(pwd -P)"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"
BACKUP_DIR="${PROJECT_BACKUP_DIR:-$(cd "$PROJECT_ROOT/.." && pwd -P)/backups}"
TIMESTAMP="$(date '+%y%m%d-%H%M%S')"
ARCHIVE="$BACKUP_DIR/${PROJECT_NAME}-${TIMESTAMP}.zip"
WARNINGS=""

warn() { WARNINGS="${WARNINGS}${WARNINGS:+; }$1"; printf 'WARNING: %s\n' "$1"; }

# Safety check: backup dir must not be inside project
mkdir -p "$BACKUP_DIR"
RESOLVED_BACKUP="$(cd "$BACKUP_DIR" && pwd -P)"
# Compare on path component boundaries
if [ "$RESOLVED_BACKUP" = "$PROJECT_ROOT" ] \
   || case "$RESOLVED_BACKUP" in "$PROJECT_ROOT"/*) true;; *) false;; esac; then
  printf 'FATAL: Backup directory %s is inside project %s. Aborting.\n' \
    "$RESOLVED_BACKUP" "$PROJECT_ROOT"
  exit 1
fi

# Disk space check
AVAIL_KB=$(df -k "$BACKUP_DIR" | awk 'NR==2 {print $4}')
if [ "$AVAIL_KB" -lt 1048576 ] 2>/dev/null; then
  warn "Low disk space: $(( AVAIL_KB / 1024 )) MB available"
fi

# Create backup
cd "$PROJECT_ROOT"
if ! zip -r -y -q "$ARCHIVE" . \
     -x ".smart-env/*" \
        ".smtcmp_json_db/*" \
        ".smtcmp_vector_db.tar.gz" \
        ".trash/*" \
        ".claude/worktrees/*" \
        ".obsidian/workspace.json" \
        "*/.DS_Store" \
        ".DS_Store"; then
  rm -f "$ARCHIVE"
  printf 'FATAL: zip failed. Partial archive removed.\n'
  exit 1
fi

# Verify integrity
if ! zip -T "$ARCHIVE" >/dev/null 2>&1; then
  rm -f "$ARCHIVE"
  printf 'FATAL: zip -T verification failed. Corrupt archive removed.\n'
  exit 1
fi

ARCHIVE_SIZE="$(du -h "$ARCHIVE" | cut -f1)"

# Retention policy
# Tiers (applied in order):
#   Recent - 7 most recent backups by timestamp -> keep ALL
#   Weekly - 4 completed ISO weeks before current week -> newest per (year, week)
#   Monthly - same calendar year, older than weekly -> newest per (year, month)
#   Bi-yearly - prior calendar years -> newest per (year, half: H1=Jan-Jun, H2=Jul-Dec)
# Safety floor: always retain at least 3 managed backups.
#
# Uses parallel indexed arrays instead of associative arrays for bash 3.2
# compatibility. Each "map" is a pair: KEYS=() and VALS=(). A lookup
# function scans KEYS linearly to find/update the matching entry.

NOW_ISO_YEAR=$(date '+%G')
NOW_ISO_WEEK=$(date '+%V')
NOW_CAL_YEAR=$(date '+%Y')

# Build the 4 completed weekly buckets (ISO year-week pairs)
WEEKLY_BUCKETS=()
TMP_Y=$NOW_ISO_YEAR
TMP_W=$((10#$NOW_ISO_WEEK))
for i in 1 2 3 4; do
  TMP_W=$((TMP_W - 1))
  if [ "$TMP_W" -le 0 ]; then
    TMP_Y=$((TMP_Y - 1))
    LAST_WEEK=$(fmt_date "${TMP_Y}-12-28" '%V')
    TMP_W=$((10#$LAST_WEEK))
  fi
  WEEKLY_BUCKETS+=("$(printf '%04d-W%02d' "$TMP_Y" "$TMP_W")")
done

# Escape project name for use in grep -E pattern
ESCAPED_NAME=$(printf '%s' "$PROJECT_NAME" | sed 's/[^a-zA-Z0-9_-]/\\&/g')
PATTERN="^${ESCAPED_NAME}-[0-9]{6}-[0-9]{6}\\.zip\$"

SKIPPED=0
KEEP_FILES=()
DELETE_FILES=()
ALL_PARSED_FILES=()

# Parallel-array maps: KEYS[i] -> VALS[i] = "stamp|filename"
BUCKET_KEYS=()
BUCKET_VALS=()

# map_upsert KEY STAMP FILENAME - insert or update if STAMP is newer
map_upsert() {
  local key="$1" stamp="$2" filename="$3"
  local idx=0
  for k in "${BUCKET_KEYS[@]+"${BUCKET_KEYS[@]}"}"; do
    if [ "$k" = "$key" ]; then
      local existing="${BUCKET_VALS[$idx]%%|*}"
      if [ "$stamp" '>' "$existing" ] 2>/dev/null \
         || [ "$stamp" = "$existing" ]; then
        # Newer or same timestamp - update (same timestamp keeps both via KEEP)
        if [ "$stamp" '>' "$existing" ] 2>/dev/null; then
          BUCKET_VALS[$idx]="$stamp|$filename"
        fi
      fi
      return
    fi
    idx=$((idx + 1))
  done
  # Key not found - insert
  BUCKET_KEYS+=("$key")
  BUCKET_VALS+=("$stamp|$filename")
}

# Build recent-7 set: newest 7 backups by filename (timestamps sort correctly)
RECENT_SET=()
cd "$RESOLVED_BACKUP"
SORT_TMP2=$(mktemp)
for rf in "${PROJECT_NAME}"-*.zip; do
  [ -f "$rf" ] || continue
  if printf '%s\n' "$rf" | grep -qE "$PATTERN"; then printf '%s\n' "$rf"; fi
done | sort -r | head -7 > "$SORT_TMP2"
while IFS= read -r line; do
  [ -n "$line" ] && RECENT_SET+=("$line")
done < "$SORT_TMP2"
rm -f "$SORT_TMP2"
SORT_TMP2=""

# Iterate backup files safely. The quoted prefix keeps spaces in PROJECT_NAME
# literal; the unquoted * glob-expands. test -f handles no-match gracefully.
for f in "${PROJECT_NAME}"-*.zip; do
  [ -f "$f" ] || continue

  # Check exact pattern match
  if ! printf '%s' "$f" | grep -qE "$PATTERN"; then
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  # Parse YYMMDD-HHmmss from filename
  STAMP="${f#"${PROJECT_NAME}"-}"
  STAMP="${STAMP%.zip}"
  YYMMDD="${STAMP%-*}"

  # Validate date parses
  FILE_DATE="20${YYMMDD:0:2}-${YYMMDD:2:2}-${YYMMDD:4:2}"
  if ! FILE_ISO=$(fmt_date "$FILE_DATE" '%G-W%V'); then
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  FILE_ISO_YEAR="${FILE_ISO%%-*}"
  FILE_ISO_WEEK="${FILE_ISO#*-W}"
  FILE_CAL_YEAR=$(fmt_date "$FILE_DATE" '%Y')
  FILE_MONTH=$(fmt_date "$FILE_DATE" '%m')
  FILE_MONTH_NUM=$((10#$FILE_MONTH))

  ALL_PARSED_FILES+=("$f")

  # Tier assignment (first match wins)
  IS_RECENT=false
  for R in "${RECENT_SET[@]+"${RECENT_SET[@]}"}"; do
    if [ "$f" = "$R" ]; then IS_RECENT=true; break; fi
  done
  if $IS_RECENT; then
    # Recent tier: keep most recent 7 unconditionally
    KEEP_FILES+=("$f")

  elif printf '%s\n' "${WEEKLY_BUCKETS[@]}" | grep -qxF "$FILE_ISO"; then
    # Weekly tier: newest per (year, week)
    map_upsert "$FILE_ISO" "$STAMP" "$f"

  elif [ "$FILE_CAL_YEAR" = "$NOW_CAL_YEAR" ]; then
    # Monthly tier: newest per (year, month)
    map_upsert "${FILE_CAL_YEAR}-${FILE_MONTH}" "$STAMP" "$f"

  else
    # Bi-yearly tier: newest per (year, half)
    if [ "$FILE_MONTH_NUM" -le 6 ]; then HALF="H1"; else HALF="H2"; fi
    map_upsert "${FILE_CAL_YEAR}-${HALF}" "$STAMP" "$f"
  fi
done

# Collect keepers from bucket winners
for VAL in "${BUCKET_VALS[@]+"${BUCKET_VALS[@]}"}"; do
  [ -n "$VAL" ] && KEEP_FILES+=("${VAL#*|}")
done

# Build DELETE set: parsed files not in KEEP set
for F in "${ALL_PARSED_FILES[@]+"${ALL_PARSED_FILES[@]}"}"; do
  IS_KEPT=false
  for K in "${KEEP_FILES[@]+"${KEEP_FILES[@]}"}"; do
    if [ "$F" = "$K" ]; then IS_KEPT=true; break; fi
  done
  if ! $IS_KEPT; then
    DELETE_FILES+=("$F")
  fi
done

# Safety floor: retain at least 3 managed backups (skipped files don't count)
WOULD_REMAIN=$(( ${#ALL_PARSED_FILES[@]} - ${#DELETE_FILES[@]} ))
if [ "$WOULD_REMAIN" -lt 3 ] && [ "${#DELETE_FILES[@]}" -gt 0 ]; then
  # Sort DELETE_FILES by filename descending (newer timestamps sort first)
  # and rescue newest until at least 3 remain. Use temp file for bash 3.2 compat
  # (pipe-into-while runs in a subshell, losing array modifications).
  SORT_TMP=$(mktemp)
  printf '%s\n' ${DELETE_FILES[@]+"${DELETE_FILES[@]}"} | sort -r > "$SORT_TMP"
  SORTED_DEL=()
  while IFS= read -r line; do
    SORTED_DEL+=("$line")
  done < "$SORT_TMP"
  NEW_DELETE=()
  RESCUED=0
  NEED=$((3 - WOULD_REMAIN))
  for D in "${SORTED_DEL[@]}"; do
    if [ "$RESCUED" -lt "$NEED" ]; then
      KEEP_FILES+=("$D")
      RESCUED=$((RESCUED + 1))
    else
      NEW_DELETE+=("$D")
    fi
  done
  DELETE_FILES=("${NEW_DELETE[@]+"${NEW_DELETE[@]}"}")
fi

# Execute deletions
DELETED=0
for D in "${DELETE_FILES[@]+"${DELETE_FILES[@]}"}"; do
  [ -n "$D" ] && rm -f "$D" && DELETED=$((DELETED + 1))
done
KEPT=${#KEEP_FILES[@]}

# Structured report
printf '\n=== BACKUP REPORT ===\n'
printf 'Archive: %s\n' "$ARCHIVE"
printf 'Size: %s\n' "$ARCHIVE_SIZE"
printf 'Integrity: PASSED\n'
printf 'Disk space: %s MB available\n' "$(( AVAIL_KB / 1024 ))"
printf 'Retained: %d\n' "$KEPT"
printf 'Deleted: %d\n' "$DELETED"
printf 'Skipped: %d\n' "$SKIPPED"
printf 'Warnings: %s\n' "${WARNINGS:-none}"
printf '========================\n'
