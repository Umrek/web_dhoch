# Deployment

The supported target is a single Linux host running Docker Compose behind a TLS-terminating reverse proxy (nginx example in `deploy/nginx/oderske-chasy.conf.example`). Any platform that runs the container image with PostgreSQL works the same way.

## Prerequisites

1. A merged `uv.lock`, created by the **Update uv.lock** workflow. The image build fails without it on purpose.
2. A domain name with a TLS certificate on the proxy.
3. An SMTP account for outgoing e-mail.

## Configuration

Copy `.env.example` to `.env` on the server (permissions `600`, never committed) and set at least:

| Variable | Notes |
|---|---|
| `SECRET_KEY` | At least 50 random characters: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `ALLOWED_HOSTS` | Exact host names, comma-separated; no wildcard |
| `CSRF_TRUSTED_ORIGINS`, `SITE_URL` | `https://` origin(s) and the canonical URL |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Database credentials; Compose builds `DATABASE_URL` from them |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` | SMTP |
| `DEFAULT_FROM_EMAIL`, `ADMIN_CONTACT_EMAIL`, `PRIVACY_CONTACT_EMAIL`, `SECURITY_CONTACT_EMAIL`, `CONTACT_RECIPIENT_EMAIL` | Contact addresses shown on the site and used for mail |
| `ADMIN_URL` | A non-obvious admin path, ending with `/` |
| `PROXY_COUNT` | Number of trusted proxies in front of the app (usually `1`). Used for login lockout and contact rate limiting |
| `HSTS_SECONDS` | Start with `3600`; raise to `31536000` once HTTPS is confirmed stable |

The production settings refuse to start if any critical value is missing or unsafe. Read the error message: it names the setting.

## First deployment

```sh
docker compose build
docker compose up -d          # runs the one-shot "migrate" service, then "web"
docker compose run --rm web python manage.py createsuperuser
```

The `migrate` service runs `migrate`, `createcachetable` and `sync_roles`. The app container itself never migrates, so several replicas cannot race each other.

After logging in to `/<ADMIN_URL>`:

1. Fill in **Nastavení webu** (operator details, contact).
2. Review every legal page, then switch off "vyžaduje právní kontrolu".
3. Invite members.

## Releases

```sh
git pull
docker compose build
docker compose up -d          # migrate runs again before web is replaced
```

Back up the database before releases that contain migrations (see operations.md).

## Reverse proxy

The proxy must:

- terminate TLS and redirect HTTP to HTTPS;
- set `X-Forwarded-Proto` and `X-Forwarded-For`. The app trusts exactly `PROXY_COUNT` hops;
- forward to `127.0.0.1:8000`;
- limit the request body to about 20 MB, to match the upload limits.

The app serves its own static files (WhiteNoise), so no media alias is needed. Do not expose `/data` through the proxy.

## Container hardening already applied

- The container runs as non-root user `10001`.
- The root filesystem is read-only, apart from `/tmp` (tmpfs).
- All capabilities are dropped and `no-new-privileges` is set.
- The app port is bound to localhost only.
- A health check calls `/health/live/`. Readiness, including a database check, is at `/health/ready/`.
