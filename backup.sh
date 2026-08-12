#!/bin/bash
set -e

# ── Load environment (DB_ROOT_PASSWORD is used for the mysqldump) ────────────
export $(grep -v '^#' .env | xargs)

# ── Locations ────────────────────────────────────────────────────────────────
BACKUP_DIR="./backups"
USB_DIR="/mnt/backup_usb/cpr_backups"

# Human-readable date — one backup pair per day, e.g. clinic_db_backup_08-12-2026.sql
DATE=$(date +%m-%d-%Y)
SQL_FILE="clinic_db_backup_${DATE}.sql"
MEDIA_FILE="media_backup_${DATE}.tar.gz"

# ── Retention tiers ──────────────────────────────────────────────────────────
# Recent backups (daily) give fine-grained restore points; as they age they are
# thinned out into weekly, then monthly snapshots for longer-term history.
DAILY_DIR="$BACKUP_DIR/daily"
WEEKLY_DIR="$BACKUP_DIR/weekly"
MONTHLY_DIR="$BACKUP_DIR/monthly"

RETENTION_DAILY_DAYS=30       # keep every daily backup for 30 days
RETENTION_WEEKLY_DAYS=56      # keep one backup per week for 8 weeks
RETENTION_MONTHLY_DAYS=360    # keep one backup per month for 12 months

mkdir -p "$DAILY_DIR" "$WEEKLY_DIR" "$MONTHLY_DIR"

# ── Database dump ────────────────────────────────────────────────────────────
docker compose exec -T db mysqldump -u root -p"${DB_ROOT_PASSWORD}" clinic_db > "${DAILY_DIR}/${SQL_FILE}"

# ── Media files dump ─────────────────────────────────────────────────────────
docker run --rm -v cpr-media-data:/data -v "$(pwd)/${DAILY_DIR}:/backup" alpine tar czf "/backup/${MEDIA_FILE}" -C /data .

chmod 600 "${DAILY_DIR}/${SQL_FILE}" "${DAILY_DIR}/${MEDIA_FILE}"

# ── Copy to USB, if it's mounted (off-site copy — rotate manually) ───────────
if mountpoint -q /mnt/backup_usb; then
    USB_MOUNTED=1
    mkdir -p "$USB_DIR"
    cp "${DAILY_DIR}/${SQL_FILE}" "${DAILY_DIR}/${MEDIA_FILE}" "$USB_DIR/"
    echo "Backup copied to USB: $USB_DIR"
else
    USB_MOUNTED=0
    echo "⚠ WARNING: USB backup drive not mounted at /mnt/backup_usb — backup saved locally only!"
fi

# ── Helpers ──────────────────────────────────────────────────────────────────

# Extract the YYYY-MM-DD sort key from a backup filename (either the
# clinic_db_backup_*.sql or media_backup_*.tar.gz naming). Prints nothing and
# returns 1 for names that don't match the expected MM-DD-YYYY pattern.
backup_sortkey() {
    local base=${1##*/} rest datestr
    case "$base" in
        clinic_db_backup_*.sql) rest=${base#clinic_db_backup_}; datestr=${rest%.sql} ;;
        media_backup_*.tar.gz)  rest=${base#media_backup_};     datestr=${rest%.tar.gz} ;;
        *) return 1 ;;
    esac
    case "$datestr" in
        [0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9]) ;;
        *) return 1 ;;
    esac
    printf '%s-%s-%s\n' "${datestr:6:4}" "${datestr:0:2}" "${datestr:3:2}"
}

# ── Tier promotion ───────────────────────────────────────────────────────────
# Promote the newest daily backup of each ISO week → weekly/, and the newest of
# each calendar month → monthly/. Each SQL file's matching media file travels
# with it. Idempotent — safe to run any number of times.
promote_tiers() {
    local tmp sortkey weekkey monthkey datestr seen_week="" seen_month=""
    tmp=$(mktemp)

    # Build a list of daily backups, newest first (YYYY-MM-DD sorts chronologically)
    for f in "$DAILY_DIR"/clinic_db_backup_*.sql; do
        [ -f "$f" ] || continue
        sortkey=$(backup_sortkey "$f") || { echo "Skipping unrecognized backup name: $f"; continue; }
        weekkey=$(date -d "$sortkey" +%G-W%V 2>/dev/null) || continue
        monthkey="${sortkey:0:7}"
        printf '%s %s %s %s\n' "$sortkey" "$weekkey" "$monthkey" "$f" >> "$tmp"
    done

    sort -r -k1,1 -o "$tmp" "$tmp"

    while read -r sortkey weekkey monthkey f; do
        [ -f "$f" ] || continue
        datestr="${sortkey:5:2}-${sortkey:8:2}-${sortkey:0:4}"

        if [[ " $seen_week " != *" $weekkey "* ]]; then
            seen_week="$seen_week $weekkey "
            cp "$f" "$WEEKLY_DIR/"
            [ -f "$DAILY_DIR/media_backup_${datestr}.tar.gz" ] && cp "$DAILY_DIR/media_backup_${datestr}.tar.gz" "$WEEKLY_DIR/"
        fi
        if [[ " $seen_month " != *" $monthkey "* ]]; then
            seen_month="$seen_month $monthkey "
            cp "$f" "$MONTHLY_DIR/"
            [ -f "$DAILY_DIR/media_backup_${datestr}.tar.gz" ] && cp "$DAILY_DIR/media_backup_${datestr}.tar.gz" "$MONTHLY_DIR/"
        fi
    done < "$tmp"

    rm -f "$tmp"
}
promote_tiers

# ── Retention (prune) ────────────────────────────────────────────────────────
# Delete backup files whose backup-date (parsed from the filename) is older
# than N days. Runs after promotion so weekly/monthly copies already exist.
prune_older_than_days() {
    local dir="$1" days="$2"
    local now cutoff sortkey epoch
    now=$(date +%s)
    cutoff=$(( now - days * 86400 ))
    for f in "$dir"/clinic_db_backup_*.sql "$dir"/media_backup_*.tar.gz; do
        [ -f "$f" ] || continue
        sortkey=$(backup_sortkey "$f") || { echo "Skipping unrecognized backup name: $f"; continue; }
        epoch=$(date -d "$sortkey" +%s 2>/dev/null) || continue
        if [ "$epoch" -lt "$cutoff" ]; then
            echo "Pruning (older than ${days} days): $f"
            rm -f "$f"
        fi
    done
}

prune_older_than_days "$DAILY_DIR"   "$RETENTION_DAILY_DAYS"
prune_older_than_days "$WEEKLY_DIR"  "$RETENTION_WEEKLY_DAYS"
prune_older_than_days "$MONTHLY_DIR" "$RETENTION_MONTHLY_DAYS"

# ── Monthly archives → USB (long-term legal retention; rotate manually) ──────
if [ "$USB_MOUNTED" = "1" ]; then
    for f in "$MONTHLY_DIR"/clinic_db_backup_*.sql; do
        [ -f "$f" ] || continue
        cp -n "$f" "$USB_DIR/" || true
        sortkey=$(backup_sortkey "$f") || continue
        datestr="${sortkey:5:2}-${sortkey:8:2}-${sortkey:0:4}"
        [ -f "$MONTHLY_DIR/media_backup_${datestr}.tar.gz" ] && cp -n "$MONTHLY_DIR/media_backup_${datestr}.tar.gz" "$USB_DIR/" || true
    done
fi

echo "Backup complete: ${DAILY_DIR}/${SQL_FILE}"
