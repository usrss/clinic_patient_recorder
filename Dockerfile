# ── Stage: Build & Run (single stage) ──────────────────────────────────────
# Python 3.14 slim base — everything needed for this Django app.
FROM python:3.14-slim AS app

# ── System dependencies ───────────────────────────────────────────────────
# mysqlclient requires build-time packages: default-libmysqlclient-dev (which
# pulls headers + libs), gcc (C compiler), and pkg-config for discovery.
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────
# Copy requirements first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Project code ──────────────────────────────────────────────────────────
COPY . .

# ── Static files ──────────────────────────────────────────────────────────
# Whitenoise serves them at runtime; collect them once at build time.
RUN python manage.py collectstatic --noinput --clear

# ── Runtime ───────────────────────────────────────────────────────────────
# Gunicorn listens on 0.0.0.0:8000 (inside the container). The host port
# mapping is defined in docker-compose.yml.
CMD ["gunicorn", "main.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
