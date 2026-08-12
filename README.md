# NORSU — Patient Record System

A web-based clinic management system for the NORSU Medical Dental Clinic.  
It streamlines patient registration, consultation queues, medical records, inventory, and certificate issuance.

---

## Features

- **Dashboard** – Overview of daily consultations, queue status, and clinic activity
- **Patient Management** – Register and update student/patient profiles (ID, college, age, sex, blood type, allergies, medical history, immunizations)
- **Consultation Queue** – Triage and track patient consultations from submission to completion
- **Medical Profiles** – Record and view allergies, blood type, medical history, and immunizations
- **Reports** – Generate clinic visit reports and summaries
- **Inventory Management** – Track clinic supplies and medicines
- **Staff Management** – Manage clinic staff accounts and roles
- **Account & Settings** – User profile, system preferences
- **Notifications & Feedback** – Alerts and user feedback collection
- **Admin Panel** – Full system administration via Django Admin

---

## Typical Clinic Workflow

### 1. Front Desk
- Front desk registers or retrieves patient record
- Creates a new **consultation** in the system
- Patient enters the **queue**

### 2. Triage & Queueing
- Patient's vital signs are recorded (temperature, blood pressure, etc.)
- Reason for visit is noted (sports clearance, medical exam, etc.)
- Patient is placed in the consultation queue

### 3. Doctor Consultation
- Records vital signs and initial screening
- Notes reason for visit (sports clearance, medical exam, etc.)
- Doctor conducts physical examination and reviews medical history
- Determines fitness and documents findings
- Marks consultation as **Completed**

### 4. Certificate Issuance
- After doctor approval, the medical certificate is generated via the system
- Certificate is printed, signed/stamped, and released to the patient
- This step is typically handled by the front desk or the attending doctor

---

## Tech Stack

- **Backend:** Django (Python)
- **Frontend:** HTML, CSS, JavaScript (Bootstrap or similar)
- **Database:** MySQL 8 (production) / SQLite (development)
- **Cache & Sessions:** Redis 7
- **Web Server:** Nginx (reverse proxy), Gunicorn (WSGI)
- **Containerization:** Docker & Docker Compose

---

## Installation (Local Development)

```bash
# Clone the repository
git clone https://github.com/usrss/clinic_patient_recorder.git
cd clinic-patient-recorder

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create a superuser (for admin access)
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

---

## Deployment with Docker (Recommended for Production)

The project ships with a complete Docker Compose setup that runs four services:

| Service | Role |
|---------|------|
| `db` | MySQL 8 database |
| `redis` | Redis 7 cache & session store |
| `web` | Django + Gunicorn (application server) |
| `nginx` | Reverse proxy, static/media file server |

### Prerequisites

- A Linux server (Ubuntu/Debian recommended) with:
  - [Docker Engine](https://docs.docker.com/engine/install/) (24+) and [Docker Compose plugin](https://docs.docker.com/compose/install/)
  - Git
  - A domain name or static IP (if accessing over the network)

### 1. Clone the Repository

```bash
git clone https://github.com/usrss/clinic_patient_recorder.git
cd clinic-patient-recorder
```

### 2. Create the Environment File

```bash
cp .env.example .env   # if you have one, or create from scratch:
```

Create `.env` with the following contents (adjust values for your server):

```bash
# Django
SECRET_KEY='django-insecure-<generate-a-long-random-key-here>'
DEBUG=False
ALLOWED_HOSTS=192.168.1.100,your-domain.com

# Database
DB_ENGINE=mysql
DB_NAME=clinic_db
DB_USER=cpr_user
DB_PASSWORD=<strong-db-password>
DB_HOST=db
DB_PORT=3306
DB_ROOT_PASSWORD=<strong-root-password>

# Redis (defaults work with the included docker-compose.yml)
REDIS_URL=redis://redis:6379/1

# Email (optional — needed for password reset)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<app-password>

# Security (set to 1/True when using HTTPS)
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
# SECURE_PROXY_SSL_HEADER=1        # enable if behind an HTTPS proxy
# CSRF_TRUSTED_ORIGINS=https://your-domain.com
```

> **Generate a secret key:** Run `python -c "import secrets; print(secrets.token_urlsafe(50))"` or use an [online generator](https://djecrety.ir/).

### 3. Build and Start the Services

```bash
docker compose build
docker compose up -d
```

This starts all four containers in the background:
- Nginx listens on **port 80** and proxies requests to the Django app
- MySQL and Redis start with health checks — the web service waits for both to be healthy

Check that all services are running:

```bash
docker compose ps
```

### 4. Run Database Migrations

```bash
docker compose exec web python manage.py migrate
```

### 5. Create a Superuser (Admin)

```bash
docker compose exec web python manage.py createsuperuser
```

### 6. Access the Application

Open a browser and go to:

```
http://<server-ip>/
http://<server-ip>/admin/   (admin panel)
```

---

## Managing the Application

| Action | Command |
|--------|---------|
| Start all services | `docker compose up -d` |
| Stop all services | `docker compose down` |
| View logs (all) | `docker compose logs -f` |
| View logs (web only) | `docker compose logs -f web` |
| Restart web only | `docker compose restart web` |
| Rebuild after code changes | `docker compose build web` then `docker compose up -d` |
| Run a management command | `docker compose exec web python manage.py <command>` |
| Open a shell in the web container | `docker compose exec web bash` |
| Access MySQL directly | `docker compose exec db mysql -u root -p"${DB_ROOT_PASSWORD}" clinic_db` |

### Apply Code Updates

```bash
git pull
docker compose build web
docker compose up -d          # only changed containers restart
docker compose exec web python manage.py migrate   # if there are new migrations
```

---

## Backups

A backup script and detailed instructions are included in the repository:

- **Script:** [`backup.sh`](backup.sh) — dumps the MySQL database and media files into human-readable `clinic_db_backup_MM-DD-YYYY.sql` + `media_backup_MM-DD-YYYY.tar.gz` pairs, with tiered retention (30 days daily, 8 weeks weekly, 12 months monthly) and USB copies
- **Documentation:** [`BACKUP.md`](BACKUP.md) — full backup/restore guide and USB rotation instructions

Run a backup manually:

```bash
./backup.sh
```

To automate daily backups, add a cron job:

```bash
crontab -e
# Add:
0 2 * * * cd /path/to/clinic-patient-recorder && ./backup.sh >> ./backups/backup.log 2>&1
```

### Restore from a backup

Backups live in `backups/daily/` (last 30 days), `backups/weekly/` (8 weeks) and
`backups/monthly/` (12 months). Pick the snapshot you want, then run the following
from the project directory (replacing `MM-DD-YYYY` with the backup's date):

Restore the **database**:

```bash
source .env
docker compose exec -T db mysql -u root -p"${DB_ROOT_PASSWORD}" clinic_db < backups/daily/clinic_db_backup_MM-DD-YYYY.sql
```

Restore **media files** (profile pictures, certificates):

```bash
docker run --rm -v cpr-media-data:/data -v $(pwd)/backups:/backup alpine \
  tar xzf /backup/daily/media_backup_MM-DD-YYYY.tar.gz -C /data
```

⚠️ **Restoring overwrites the current database** — anything saved since that backup
will be lost. Snapshot the current state first so you can undo the restore:

```bash
docker compose exec -T db mysqldump -u root -p"${DB_ROOT_PASSWORD}" clinic_db > backups/daily/PRERESTORE_$(date +%m-%d-%Y_%H%M).sql
```

Then restart the app so nothing serves stale data:

```bash
docker compose restart web
```

> 💡 **Always test a restore into a throwaway database before you need it for real**
> — a backup that has never been test-restored is unverified (details in `BACKUP.md`).

> ⚠️ **Before putting real patient data into production**, ensure off-server backups are in place (see `BACKUP.md` for details).

---

## Production Security Checklist

Before deploying with real patient data, verify the following:

- [ ] **`.env` is properly configured** — `DEBUG=False`, `SECRET_KEY` is strong and unique
- [ ] **HTTPS enabled** — add TLS to Nginx (e.g., Let's Encrypt / Certbot) and set:
  ```
  SECURE_SSL_REDIRECT=True
  SESSION_COOKIE_SECURE=True
  CSRF_COOKIE_SECURE=True
  ```
- [ ] **Backups configured and tested** — a restore was verified on a non-production environment
- [ ] **Off-server backup** — USB drive or other off-site backup in place (see `BACKUP.md`)
- [ ] **Firewall** — only ports 80 (HTTP) and 443 (HTTPS) are open; close port 22 if not needed
- [ ] **Regular updates** — keep Docker images and system packages up to date

---

## Troubleshooting

### "Invalid HTTP_HOST" error
Set `ALLOWED_HOSTS` in `.env` to include your server's IP address or domain name.

### Static files not loading (404)
Run collectstatic manually:
```bash
docker compose exec web python manage.py collectstatic --noinput --clear
```

### MySQL connection refused
Make sure the `DB_HOST` in `.env` is set to `db` (the Docker service name, not `localhost`).

### Nginx returns 502 Bad Gateway
The web container may still be starting. Wait a few seconds and reload:
```bash
docker compose restart nginx
```
If it persists, check the web logs:
```bash
docker compose logs web
```

---

## Architecture Overview

```
Internet / LAN
     │
     ▼
┌──────────┐   port 80    ┌──────────┐   upstream   ┌──────────┐
│  Nginx   │──────────────│ Gunicorn │──────────────│  Django  │
│ (static) │              │ (3 wkr)  │              │   App    │
└──────────┘              └──────────┘              └────┬─────┘
     │                           │                       │
     │ serves                    │ caches                │ reads/writes
     ▼                           ▼                       ▼
┌──────────┐              ┌──────────┐            ┌──────────┐
│  static  │              │  Redis 7 │            │  MySQL 8 │
│  /media  │              │ (cache & │            │ (primary │
│ (files)  │              │ sessions)│            │   DB)    │
└──────────┘              └──────────┘            └──────────┘
```

---

## License

This project is developed for the NORSU Medical Dental Clinic. All rights reserved.
