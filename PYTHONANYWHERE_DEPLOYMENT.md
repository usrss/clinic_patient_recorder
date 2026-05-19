# PythonAnywhere Free Tier — Deployment Guide

> Step-by-step instructions for deploying the NORSU Patient Record System
> on PythonAnywhere's free plan.

---

## Prerequisites

- A [PythonAnywhere](https://www.pythonanywhere.com/) account (free tier)
- Your project pushed to a GitHub repository (or uploaded manually)

---

## Step 1 — Upload Your Code to PythonAnywhere

Log in to PythonAnywhere and open a **Bash console** (Dashboard → Consoles → Bash).

Clone your repo:

```bash
git clone https://github.com/your-username/clinic-patient-recorder.git
cd clinic-patient-recorder
```

> If you don't want to use Git, you can use the **Files tab** to upload files manually instead.

---

## Step 2 — Upload the `.env` File

Still in the Bash console, create the `.env` file:

```bash
nano .env
```

Paste the contents below, then save (`Ctrl+O`, `Enter`, `Ctrl+X`).

**Required variables:**

```ini
SECRET_KEY=your-generated-secret-key
DEBUG=False
ALLOWED_HOSTS=yourusername.pythonanywhere.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
```

> **Note on database**: The default is SQLite (set in `settings.py`), so you don't need `DB_ENGINE` in `.env`. If you want MySQL, add `DB_ENGINE=mysql` along with `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` — and install `mysqlclient` in requirements.

> **Note on SECRET_KEY**: Generate one at https://djecrety.ir/ or use `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

---

## Step 3 — Create a Virtual Environment & Install Dependencies

In the Bash console:

```bash
mkvirtualenv --python=/usr/bin/python3.12 clinic-env
pip install -r requirements.txt
```

> If `mkvirtualenv` isn't found, run `pip install virtualenvwrapper` first, or use:
> ```bash
> python3.12 -m venv clinic-env
> source clinic-env/bin/activate
> pip install -r requirements.txt
> ```

---

## Step 4 — Run Migrations & Collect Static Files

Still in the Bash console (with the virtualenv activated):

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

The `collectstatic` command copies all static files (CSS, JS, images) from each app's `static/` folder into the `staticfiles/` directory. Django discovers these automatically — no extra configuration needed.

---

## Step 5 — Configure a Web App

1. Go to the **Web** tab in PythonAnywhere
2. Click **"Add a new web app"**
3. Choose **"Manual Configuration"**
4. Select **Python 3.12**
5. When asked, enter the path to your virtualenv:

   ```
   /home/your-username/.virtualenvs/clinic-env
   ```

   (Replace `your-username` with your actual PythonAnywhere username)

---

## Step 6 — Edit the WSGI File

On the Web tab, click the link for **"WSGI configuration file"** (it'll be something like `/var/www/your-username_pythonanywhere_com_wsgi.py`).

Delete everything and replace with this:

```python
import os
import sys

# ── Point to your project directory ──
path = '/home/your-username/clinic-patient-recorder'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'main.settings'
os.environ['PYTHONUNBUFFERED'] = '1'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Replace `your-username` with your actual PythonAnywhere username.

---

## Step 7 — Configure Media File URL (Only for User Uploads)

On the **Web** tab, scroll to the **"Static files"** section and add **one entry** — for media (user-uploaded) files:

| URL      | Directory                                               |
|----------|----------------------------------------------------------|
| `/media/` | `/home/your-username/clinic-patient-recorder/media`      |

**Why only media?** Your project already has **Whitenoise** configured, which serves static files (CSS/JS) directly through Django. This means you don't need a separate static file mapping in PythonAnywhere — Whitenoise handles it automatically.

> If you prefer PythonAnywhere to serve static files instead (slightly faster via Nginx), you can add a second entry:
> | URL | Directory |
> |---|---|
> | `/static/` | `/home/your-username/clinic-patient-recorder/staticfiles` |
>
> In that case, Whitenoise becomes optional. Either approach works — having both is fine too, just redundant.

---

## Step 8 — Reload the Web App

Click the green **Reload** button on the Web tab.

---

## Step 9 — Verify It Works

Visit `https://your-username.pythonanywhere.com` in your browser. You should see the NORSU Medical Dental Clinic home page.

Test these:

- ✅ Login — `/accounts/login/`
- ✅ Admin panel — `/admin/` (use the superuser you created)
- ✅ Dashboard — Login and verify dashboard loads
- ✅ Static files — CSS should be styled, icons visible
- ✅ Media files — Upload a profile picture in Settings, verify it displays

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| **500 Internal Server Error** | Check the **"Error log"** link on the Web tab — it'll show the traceback |
| `ModuleNotFoundError: No module named 'whitenoise'` | Run `pip install -r requirements.txt` again — you forgot to install deps |
| **Static files not loading (no CSS)** | Run `python manage.py collectstatic --noinput` and reload the web app |
| **Images/profile pictures broken** | Check the Media files URL mapping in Step 7 — the path must be absolute and correct |
| `Invalid HTTP_HOST header` | Your `.env` file's `ALLOWED_HOSTS` doesn't match the domain. It should be `your-username.pythonanywhere.com` |
| `SECRET_KEY` error on startup | The `.env` file is missing or doesn't have `SECRET_KEY=...` |
| **Email sending fails** | Free tier has limited outbound access. Option A: Set up a Gmail App Password (recommended). Option B: Change to `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` in `.env` (emails print to logs instead) |

---

## What About Your Local Setup?

Your local development setup remains completely unchanged. Your local `.env` still uses MySQL (or whatever you have):

```ini
DB_ENGINE=mysql
DB_NAME=clinic_db
DB_USER=root
DB_PASSWORD=localpass
DB_HOST=localhost
DB_PORT=3306
DEBUG=True
SECRET_KEY=your-local-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

The two environments are fully independent — different `.env` files, different databases. The code switches automatically based on the `.env` on each machine.
