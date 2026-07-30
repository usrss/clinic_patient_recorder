# ── Stage: Build & Run (single stage) ──────────────────────────────────────
# Python 3.14 slim base — everything needed for this Django app.
FROM python:3.14-slim AS app

# ── System dependencies ───────────────────────────────────────────────────
# mysqlclient requires build-time packages: default-libmysqlclient-dev (which
# pulls headers + libs), gcc (C compiler), and pkg-config for discovery.
#
# LibreOffice-writer is needed for DOCX→PDF conversion in certificate export.
# The --no-install-recommends flag skips recommended packages that are needed
# for headless mode (X11 libs, fonts, etc.), so we list them explicitly.
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    gcc \
    pkg-config \
    libreoffice-writer \
    libreoffice-common \
    fonts-dejavu \
    fonts-liberation \
    fontconfig \
    libgl1 \
    libdbus-1-3 \
    libxinerama1 \
    libxcb-shm0 \
    libxcb1 \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Generate locale — LibreOffice headless needs a locale to function properly.
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# ── Working directory ─────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ──────────────────────────────────────────────────
# Copy requirements first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Project code ─────────────────────────────────────────────────────────
COPY . .

# ── Static files ─────────────────────────────────────────────────────────
# Whitenoise serves them at runtime; collect them once at build time.
RUN python manage.py collectstatic --noinput --clear

# ── Runtime ───────────────────────────────────────────────────────────────
# Gunicorn listens on 0.0.0.0:8000 (inside the container). The host port
# mapping is defined in docker-compose.yml.
CMD ["gunicorn", "main.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
