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

### 2. Create `backup.sh`

Create a file named `backup.sh` in the project root (same folder as
`manage.py`, `Dockerfile`, `docker-compose.yml`):

```bash
#!/bin/bash
set -e

export $(grep -v '^#' .env | xargs)

BACKUP_DIR="./backups"
USB_DIR="/mnt/backup_usb/cpr_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SQL_FILE="clinic_db_backup_${TIMESTAMP}.sql"
MEDIA_FILE="media_backup_${TIMESTAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

# ── Database dump ──
docker compose exec -T db mysqldump -u root -p"${DB_ROOT_PASSWORD}" clinic_db > "${BACKUP_DIR}/${SQL_FILE}"

# ── Media files dump ──
docker run --rm -v cpr-media-data:/data -v "$(pwd)/${BACKUP_DIR}:/backup" alpine tar czf "/backup/${MEDIA_FILE}" -C /data .

chmod 600 "${BACKUP_DIR}/${SQL_FILE}" "${BACKUP_DIR}/${MEDIA_FILE}"

# ── Copy to USB, if it's mounted ──
if mountpoint -q /mnt/backup_usb; then
    mkdir -p "$USB_DIR"
    cp "${BACKUP_DIR}/${SQL_FILE}" "${BACKUP_DIR}/${MEDIA_FILE}" "$USB_DIR/"
    echo "Backup copied to USB: $USB_DIR"
else
    echo "⚠ WARNING: USB backup drive not mounted at /mnt/backup_usb — backup saved locally only!"
fi

# Keep 14 days of local backups (USB copies are kept separately — rotate manually)
find "$BACKUP_DIR" -type f \( -name "*.sql" -o -name "*.tar.gz" \) -mtime +14 -delete
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

Confirm files were created:
```bash
ls -la backups/
```

You should see a `clinic_db_backup_<timestamp>.sql` and a
`media_backup_<timestamp>.tar.gz`.

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

A backup drive that never leaves the same room as the server does not
protect against the scenarios that matter most (fire, theft of the
whole setup, building damage).

---

## Restoring from a backup

### Restore the database

```bash
source .env
docker compose exec -T db mysql -u root -p"${DB_ROOT_PASSWORD}" clinic_db < backups/clinic_db_backup_<timestamp>.sql
```

⚠️ This overwrites the current database contents with the backup. Only
run this when you're certain you want to replace live data (e.g.
disaster recovery, not routine use).

### Restore media files

```bash
docker run --rm -v cpr-media-data:/data -v $(pwd)/backups:/backup alpine \
  tar xzf /backup/media_backup_<timestamp>.tar.gz -C /data
```

### Always test a restore before you need it for real

Don't assume a backup file is good just because it was created without
errors. Periodically test a restore into a **throwaway/test database**
(not production) to confirm the backup is actually usable. A backup
that has never been test-restored is unverified.

---

## Outstanding items / to-do

- [ ] Acquire USB backup drive(s) — **blocking** for safe production use
- [ ] Confirm server OS (this guide assumes Linux — commands like
      `mountpoint`, `crontab`, and `/mnt/...` paths are Linux-specific)
- [ ] Decide on official retention period based on clinic/institutional
      policy (current script default: 14 days locally — likely too
      short for real patient records; confirm actual requirement)
- [ ] Perform and document a first full test restore before go-live
- [ ] Establish who is responsible for the weekly USB rotation