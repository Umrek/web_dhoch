# Architecture

## Shape

A **modular monolith**: one Django project (`src/config`) and one app per domain under `src/apps`. Each app follows the same conventions:

| Module | Responsibility |
|---|---|
| `models.py` | Data and database-level invariants (constraints, not only form validation) |
| `selectors.py` | Read queries. Other apps read through these, never through another app's models directly |
| `services.py` | Multi-step writes in `transaction.atomic`, with audit logging; raise domain exceptions |
| `views.py` | HTTP only: authentication, permissions, forms, rendering |
| `admin.py` | Back office, restricted by model permissions |

Signals are not used for business workflows. The only receiver logs django-axes lockouts.

## Domains

| App | Purpose | Main models |
|---|---|---|
| `common` | Logging, request IDs, security headers, private storage, file helpers, form helpers, health checks, demo data | – |
| `accounts` | E-mail login, invitations, roles (`roles.py`), password flows | `User` (UUID pk, case-insensitive unique e-mail) |
| `content` | Editable pages (plain text, escaped), site settings singleton, internal announcements | `Page`, `SiteSettings`, `Announcement` |
| `musicians` | Member profiles, opt-in public roster, portal dashboard | `MusicianProfile` |
| `events` | Concerts, rehearsals and other events; public listing; `.ics` export | `Event` |
| `attendance` | Each member's own answer per event; organizer overview | `AttendanceResponse` (unique per event and user) |
| `sheet_music` | Versioned PDF parts per section; authorized download | `Piece`, `SheetMusicPart` |
| `gallery` | Albums and processed photos served through views | `Album`, `GalleryImage` |
| `contact` | Contact form with anti-spam, rate limit, retention | `ContactMessage` |

Documented cross-app read dependencies:

- `content.views` reads `events`, `gallery` and `musicians` selectors.
- `musicians.views` reads `events` and `content` selectors.
- `attendance` reads `events` and `musicians`.

## Roles and permissions

Roles are Django groups with explicit permission lists in `apps/accounts/roles.py`. `sync_roles` makes them match; it is idempotent and is part of every release.

| Role | Can do |
|---|---|
| **Muzikant** | Use the portal (`accounts.access_portal`), own profile and own attendance only |
| **Redaktor obsahu** | Pages, announcements, gallery; view events |
| **Organizátor akcí** | Events, sheet music, announcements; view attendance |
| **Administrátor** | All permissions of the project apps |

`is_staff` (admin site access) is derived from roles by `refresh_staff_flag`, so a plain musician never reaches the admin site.

## Object-level authorization

- Profile and attendance views take the user from the session; no other user's id is ever accepted from the request.
- Sheet music: only current parts of non-archived pieces can be downloaded, by portal members.
- Gallery: only published images in published albums are served.
- Events: only events with `is_public=True` appear on the public site and in `.ics` exports. The internal notes are never included in public output.

## Settings

| Module | Use |
|---|---|
| `config.settings.base` | Shared settings. No secret, `DEBUG` or database is defined here |
| `config.settings.local` | Development: `.env` loader, SQLite, console e-mail. Default for `manage.py` |
| `config.settings.test` | Tests: in-memory SQLite, temporary file roots |
| `config.settings.production` | Validates all critical values at start-up and refuses to boot on an unsafe configuration. Default for `wsgi.py`/`asgi.py` |

## Dependencies

All direct dependencies are pinned in `pyproject.toml`. The full tree, with hashes, goes into `uv.lock`, which is generated only in CI.

| Package | Why |
|---|---|
| Django 5.2 (LTS) | Framework; LTS for a long support window |
| django-axes | Login brute-force protection (per account and per IP) |
| django-csp | Content-Security-Policy header (no inline scripts) |
| whitenoise | Serves hashed and compressed static files from Gunicorn without a separate CDN |
| psycopg[binary] | PostgreSQL driver |
| gunicorn | WSGI server in the container |
| Pillow | Decoding, validating and re-encoding uploaded photos (strips metadata) |

Development: pytest, pytest-django, pytest-cov, pytest-playwright, ruff, mypy, django-stubs, djlint, bandit, pip-audit, pre-commit.

URL parsing for `DATABASE_URL` is done in `config/settings/env.py`, so no extra dependency is needed for it.
