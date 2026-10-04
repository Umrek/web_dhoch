# Testing

## Layers

| Layer | Location | Runs with |
|---|---|---|
| Unit and integration (models, services, views, permissions, headers) | `tests/test_*.py` | `uv run pytest` (Django test client, in-memory SQLite) |
| Browser smoke tests (navigation, skip link, mobile menu, login, accessible form errors) | `tests/e2e/` (marked `e2e`) | `uv run pytest -m e2e --no-cov` after `uv run playwright install chromium` |
| Static checks | – | ruff, ruff format, djlint, mypy (django-stubs), bandit |
| Migrations | `test_commands_and_migrations.py`, CI | `makemigrations --check --dry-run` |

E2E tests are excluded by default (`-m "not e2e"` in `pyproject.toml`). Coverage must stay at or above 80 % (`--cov-fail-under=80`).

In CI, the `test` job runs the same suite on PostgreSQL 16 (via `DATABASE_URL`). Locally, tests use in-memory SQLite. See `.github/workflows/ci.yml`.

## Three levels of evidence

1. **Static local visual preview** (`python tools/local_preview.py`, see README). It shows layout, navigation, responsive breakpoints and keyboard and focus behaviour using the production CSS and JS. It is fictional static HTML with no Django, database, forms or permissions. It proves nothing about backend behaviour.
2. **Authoritative Django validation in GitHub Actions** (below). This is the only evidence for tests, migrations, PostgreSQL, permissions, private files, Docker and Playwright.
3. **Production deployment validation** by the operator on the real host: TLS, proxy headers, HSTS rollout, SMTP delivery, backups and restore, and persistent volumes (see deployment.md and operations.md).

## Authoritative validation (GitHub Actions)

Some developer workstations cannot install Python 3.12, Docker or packages, because TLS inspection is in place. On those machines nothing is installed locally. GitHub Actions is the authoritative validation environment. Each check below counts as passed only when it has passed in a real workflow run.

| Workflow / job | What it proves |
|---|---|
| **Update uv.lock** (manual) | `uv lock` on Python 3.12 with normal TLS verification; `uv lock --check`; install from the lock; Django 5.2 imports. Opens a pull request. |
| CI → `lock` | `uv.lock` exists and matches `pyproject.toml`; only PyPI is used as a package source. |
| CI → `quality` | ruff check and ruff format, djlint, mypy, bandit, pip-audit, pre-commit. |
| CI → `test` | On PostgreSQL 16, with the test settings: `check`, `makemigrations --check --dry-run`, `migrate --plan`. Then migrate a clean database, run `createcachetable` and `sync_roles`, and re-check for drift. With the production settings: `check --deploy --fail-level WARNING`, plus a check that settings fail without `SECRET_KEY` or with SQLite. `load_demo_data` runs twice (idempotency). Then the full pytest suite with coverage. |
| CI → `e2e` | Playwright with Chromium, run against pytest-django's real `live_server`. |
| CI → `docker` | Validates `compose.yaml` and builds the image. Checks the image: Python 3.12, UID 10001, no build tools, empty data volumes, collected static manifest. Runs the release migration in the container against PostgreSQL 16, starts gunicorn on a read-only filesystem with all capabilities dropped, and checks `/health/ready/`, the Docker health status and that `docker stop` exits with status 0. |
| **Security scans** | gitleaks, dependency review (on PRs), CodeQL. |

Pull requests opened by the lock workflow with `GITHUB_TOKEN` do not trigger CI automatically. To validate one, a maintainer starts it manually: **Actions → CI → Run workflow → branch `chore/update-uv-lock`**. Do the same for **Security scans**.

In an unrestricted development environment the same commands run locally: `uv sync --frozen`, `uv run pytest`, `uv run pytest -m e2e --no-cov` (after `uv run playwright install chromium`).

## Coverage of required behaviour

| Area | Main tests |
|---|---|
| Login, lockout, generic errors, inactive users | `test_accounts.py` |
| Roles are least-privilege; `is_staff` derived from roles; `sync_roles` idempotent | `test_accounts.py`, `test_commands_and_migrations.py` |
| Invitations and reset links use `SITE_URL`; no account enumeration; 1-hour tokens | `test_accounts.py` |
| Portal: anonymous user redirected, users without the portal permission get 403 | `test_accounts.py`, `test_sheet_music.py` |
| Attendance answers bound to the session user; deadline, cancelled and started events; organizer-only overview | `test_attendance.py` |
| Public events hide internal events and internal notes; rehearsals can't be public; `.ics` escaping and folding | `test_events.py` |
| Sheet music: PDF validation, copyright confirmation, versioning, authorized download headers, audit log | `test_sheet_music.py` |
| Gallery: EXIF stripping, orientation, size and pixel limits, format allow-list, publication checks, file deletion | `test_gallery.py` |
| Contact: honeypot, signed timing token, consent, rate limit (including behind a proxy), e-mail failure, retention purge | `test_contact.py` |
| Opt-in roster, consent withdrawal, own-profile only, escaped content, noindex portal | `test_public_and_privacy.py` |
| Security headers, CSP-safe templates, CSRF, error pages, production settings fail fast | `test_security.py` |

## Writing tests

- Use the fixtures in `tests/conftest.py`: `make_user`, `musician`, `organizer`, `editor`, `admin_user`, `make_event`, `login`.
- All test data is fictional, and e-mail addresses use the `example.test` domain.
- File roots point to a temporary directory (`config.settings.test`), so tests never touch real uploads.
- For a permission change, test both sides: the allowed role and a role that must be denied.

## Not automated

- Screen-reader and keyboard walkthroughs. Do one manually per release using the checklist in operations.md.
- Load and denial-of-service behaviour.
