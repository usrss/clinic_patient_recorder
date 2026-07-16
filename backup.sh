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