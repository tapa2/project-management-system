# syntax=docker/dockerfile:1.6
# =============================================================================
# Multi-stage Dockerfile для Django + Gunicorn
# =============================================================================

# --- Stage 1: builder --------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Системні залежності для psycopg2-binary, pillow тощо
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libjpeg-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Збираємо колеса в окремий шар, який кешується
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt


# --- Stage 2: runtime --------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PORT=8000

# Runtime-залежності (без compiler-у)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        libjpeg62-turbo \
        zlib1g \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd --system django \
    && useradd --system --gid django --home /app --shell /bin/bash django

WORKDIR /app

# Ставимо пакети з готових wheels
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Копіюємо код
COPY . .

# Скрипт ентрипоінту
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Каталоги для статики та media + права для non-root
RUN mkdir -p /app/staticfiles /app/media \
    && chown -R django:django /app

USER django

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
