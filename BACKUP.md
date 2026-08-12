# Database & Media Backup — Clinic Patient Recorder (CPR)

This document explains how backups work for this project, how to run them,
and how to restore from one if needed.

---

## What gets backed up

| Item | Contains | Backup method |
|---|---|---|
| MySQL database (`clinic_db`) | All patient records, consultations, prescriptions, user accounts, audit logs — everything in the DB | `mysqldump` |
| Media files (`cpr-media-data` volume) | Uploaded profile pictures, certificate files, etc. | `tar` archive of the Docker volume |

Both are considered **PHI (Protected Health Information)** and must be
handled with the same care as the live system — never committed to Git,
never left in an unsecured location, and access-restricted to authorized
staff only.

---

## Current backup status

⚠️ **As of now, off-server backups are NOT yet configured.** A USB drive
for offline backups has not been acquired yet. Until that's in place,
backups only exist locally on the server itself and are **not protected
against server-level failure** (disk death, fire, theft, ransomware).

**This must be resolved before real patient data goes into production.**

---

## Backup files & tiered retention

Each run of `backup.sh` creates **one pair of files per day**, named with a
human-readable date so you can tell at a glance which snapshot is which:

```
backups/
├── daily/    clinic_db_backup_08-12-2026.sql   +  media_backup_08-12-2026.tar.gz
│             clinic_db_backup_08-11-2026.sql   +  media_backup_08-11-2026.tar.gz
│             ...
├── weekly/   clinic_db_backup_08-05-2026.sql   +  media_backup_08-05-2026.tar.gz   ← one per week
│             clinic_db_backup_07-29-2026.sql   +  media_backup_07-29-2026.tar.gz
│             ...
└── monthly/  clinic_db_backup_07-01-2026.sql   +  media_backup_07-01-2026.tar.gz   ← one per month
              clinic_db_backup_06-01-2026.sql   +  media_backup_06-01-2026.tar.gz
              ...
```

As backups age, the newest one of each **ISO week** is copied up into
`weekly/`, and the newest of each **calendar month** into `monthly/`.
Each tier is then pruned automatically by its own retention window:

| Tier | Location | Retention | Purpose |
|---|---|---|---|
| Daily | `backups/daily/` | **30 days** | Fine-grained restore points for recent incidents |
| Weekly | `backups/weekly/` | **8 weeks** (~2 months) | Longer look-back for slow-discovered problems |
| Monthly | `backups/monthly/` | **12 months** | Historical checkpoints across the school year |
| USB archive | `/mnt/backup_usb/cpr_backups` | **Kept indefinitely** (manual rotation) | Off-site + long-term legal retention (DOH: 7–10 yrs) |

> Note: if `backup.sh` runs more than once in the same day, the second run
> overwrites the same-day file (same `MM-DD-YYYY` name) — the daily backup
> always represents the end state of that day.

---

## Setup (once a USB backup drive is available)

### 1. Prepare the USB drive

- Use a dedicated USB drive (32GB+ recommended) — label it clearly as
  clinic backup media, not a general-purpose drive.
- Plug it into the server and identify it:
  ```bash
  lsblk
  ```
- Mount it at a consistent path, e.g. `/mnt/backup_usb`. To make this
  persist across reboots, add an entry to `/etc/fstab` rather than
  mounting manually each time.

### 2. `backup.sh (Already created)`

The script lives in the project root (same folder as `manage.py`,
`Dockerfile`, `docker-compose.yml`). Current version:

```bash
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
```

Make it executable:
```bash
chmod +x backup.sh
```

### 3. Lock down the backups folder

```bash
mkdir -p backups
chmod 700 backups
```

### 4. Test it manually

```bash
./backup.sh
```

Confirm the files were created and the tiers are working:

```bash
ls -la backups/daily/
ls -la backups/weekly/
ls -la backups/monthly/
```

You should see a `clinic_db_backup_MM-DD-YYYY.sql` and a
`media_backup_MM-DD-YYYY.tar.gz` in `backups/daily/`.

### 5. Automate with cron (daily backup)

```bash
crontab -e
```

Add a line to run daily at 2 AM:
```
0 2 * * * cd /path/to/clinic-patient-recorder && ./backup.sh >> ./backups/backup.log 2>&1
```

Adjust `/path/to/clinic-patient-recorder` to the actual path on the server.

### 6. Check the log periodically

```bash
tail -20 ./backups/backup.log
```

Do this roughly once a week to confirm backups are actually running and
the USB drive isn't silently unplugged/unmounted.

---

## USB drive rotation (manual habit — required)

Since this deployment has no second device and must stay fully
offline/on-premise, **the USB drive itself must physically leave the
building periodically** to provide real protection against a
server-level disaster (fire, theft, flood, etc.).

Recommended routine:

1. Use **two USB drives**, alternating.
2. Each week, swap the drive currently in the server for the other one.
3. Take the drive you just removed **off-site** — home, a locked drawer
   elsewhere in the building, a safe — anywhere physically separate from
   the server.
4. Repeat weekly.

The USB drive holds the **monthly archives** (the long-term legal-retention
copies) plus the daily copies — it is the copy that must survive the server
itself, so treat it accordingly. A backup drive that never leaves the same
room as the server does not protect against the scenarios that matter most.

> Legal note (Philippines): DOH record-retention rules require out-patient
> records kept **7 years** and in-patient records **10 years** from the last
> visit. Because the local tiers auto-prune, the USB (or another archive) is
> what carries the clinic's compliance copies that long.

---

## Restoring from a backup

### Choose your restore point first

- **Recent issue (last 30 days):** pick the file from `backups/daily/`.
- **Older issue:** pick from `backups/weekly/` or `backups/monthly/`.
- The `.sql` and `.tar.gz` with the **same date** belong to the same snapshot.

Example for a restore point of `08-12-2026`:

### Restore the database

```bash
source .env
docker compose exec -T db mysql -u root -p"${DB_ROOT_PASSWORD}" clinic_db < backups/daily/clinic_db_backup_08-12-2026.sql
```

⚠️ This overwrites the current database contents with the backup. Only
run this when you're certain you want to replace live data (e.g.
disaster recovery, not routine use).

### Restore media files

```bash
docker run --rm -v cpr-media-data:/data -v $(pwd)/backups:/backup alpine \
  tar xzf /backup/daily/media_backup_08-12-2026.tar.gz -C /data
```

> **Tip:** before overwriting anything, snapshot the current (possibly bad)
> state so the restore can be undone:
> ```bash
> source .env
> docker compose exec -T db mysqldump -u root -p"${DB_ROOT_PASSWORD}" clinic_db > backups/daily/PRERESTORE_$(date +%m-%d-%Y_%H%M).sql
> ```

### Always test a restore before you need it for real

Don't assume a backup file is good just because it was created without
errors. Periodically test a restore into a **throwaway/test database**
(not production) to confirm the backup is actually usable. A backup
that has never been test-restored is unverified.

---

## Migrating from the old format

Older backups used the `clinic_db_backup_YYYYMMDD_HHMMSS.sql` naming and
lived directly in `backups/`. The new script ignores those files (they are
not pruned, promoted, or copied to USB) — they remain on disk until you
delete them. If you want to keep any for the archive, move them into
`backups/monthly/` (the script will then retain and rotate them normally).
Otherwise remove them once you're confident the new daily/weekly/monthly
scheme has been running for a few days.

---

## Outstanding items / to-do

- [ ] Acquire USB backup drive(s) — **blocking** for safe production use
- [ ] Confirm server OS (this guide assumes Linux — commands like
      `mountpoint`, `crontab`, and `/mnt/...` paths are Linux-specific)
- [ ] Decide on the official retention period (DOH minimum: 7 yrs
      out-patient / 10 yrs in-patient; current USB archive is indefinite,
      local tiers are 30 days / 8 weeks / 12 months)
- [ ] Perform and document a first full test restore before go-live
- [ ] Establish who is responsible for the weekly USB rotation
