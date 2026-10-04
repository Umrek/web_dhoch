# syntax=docker/dockerfile:1
# Python 3.12 everywhere. Requires a committed uv.lock (see .github/workflows/update-lock.yml);
# the build intentionally fails without it instead of resolving dependencies on its own.

FROM ghcr.io/astral-sh/uv:0.12.23 AS uv

FROM python:3.12-slim-bookworm AS builder
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /app
COPY pyproject.toml uv.lock .python-version README.md ./
RUN uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    GALLERY_ROOT=/data/gallery \
    SHEET_MUSIC_ROOT=/data/sheet_music

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app \
 && mkdir -p /data/gallery /data/sheet_music \
 && chown -R app:app /data

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=root:root src ./src
COPY --chown=root:root docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 0555 /usr/local/bin/entrypoint.sh

# Build-time only placeholders so production settings validate while collecting static files.
# Nothing here is a real secret and none of it is kept in the image environment.
RUN SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" \
    ALLOWED_HOSTS=build.invalid CSRF_TRUSTED_ORIGINS=https://build.invalid \
    SITE_URL=https://build.invalid DATABASE_URL=postgresql://u:p@localhost/build \
    EMAIL_HOST=localhost DEFAULT_FROM_EMAIL=build@build.invalid \
    ADMIN_CONTACT_EMAIL=build@build.invalid PRIVACY_CONTACT_EMAIL=build@build.invalid \
    python src/manage.py collectstatic --noinput --settings=config.settings.production \
 && chmod -R a+rX /app/staticfiles

USER 10001:10001
WORKDIR /app/src
EXPOSE 8000
VOLUME ["/data/gallery", "/data/sheet_music"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,os; urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/health/live/', headers={'Host': os.environ.get('HEALTHCHECK_HOST','localhost')}), timeout=3)"
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "30", "--access-logfile", "-", "--error-logfile", "-"]
