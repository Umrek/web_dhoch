# Dechová hudba Oderské chasy – web

Web a interní portál dechové hudby Oderské chasy. The code is in English; the interface is in Czech.

- **Public site:** home page, about the band, events with an `.ics` export, a photo gallery, a contact form, and legal pages.
- **Portal for musicians (members only):** dashboard, own profile, events with attendance responses, and sheet music (PDFs downloaded only through an authorized view).
- **Administration:** roles (Muzikant, Redaktor obsahu, Organizátor akcí, Administrátor) implemented as Django groups.

Stack: Python 3.12, Django 5.2 LTS, PostgreSQL in production, Gunicorn and WhiteNoise, uv. Details are in [docs/architecture.md](docs/architecture.md).

## Status of external validation

At handover, the following had **not** been run, because the development machine has only Python 3.11 and no Docker, and its TLS-inspecting proxy prevents uv from verifying PyPI:

- `uv.lock` does not exist yet. Generate it with the manually triggered **Update uv.lock** workflow (Actions tab), then review and merge its pull request. CI fails without the lock on purpose.
- The test suite, `makemigrations --check`, the Docker build and the Playwright tests run in CI on Python 3.12. The migrations are hand-written; the CI step `makemigrations --check --dry-run` is the first real check of them. **No CI run has been carried out yet**, so the project status is *validation in progress*. See [docs/testing.md](docs/testing.md#authoritative-validation-github-actions).

Never work around a TLS problem by disabling certificate verification or by using `--allow-insecure-host`.

## Local development

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), and a committed `uv.lock`.

```sh
cp .env.example .env           # local values; never commit .env
uv sync --frozen
uv run python src/manage.py migrate
uv run python src/manage.py sync_roles
uv run python src/manage.py load_demo_data   # fictional data, DEBUG only
uv run python src/manage.py runserver
```

On Windows without `make`, use `.\scripts\dev.ps1 setup|run|test|lint|format|typecheck|check|demo|e2e`. With `make`, the same tasks are available as `make <task>`.

The local settings (`config.settings.local`) use SQLite and print e-mail to the console. `load_demo_data` prints the demo password once; all demo accounts use the reserved `.invalid` domain.

## Restricted local visual preview

Use this on workstations where Django, Python 3.12, Docker and packages cannot be installed. It needs **no installation**: only the Python 3.11+ standard library and a browser.

```powershell
python tools/local_preview.py              # or: py -3.11 tools/local_preview.py
python tools/local_preview.py --port 8081  # different port (1024–65535)
python tools/local_preview.py --no-browser # do not open the browser automatically
```

- The preview opens at <http://127.0.0.1:8080/>. Stop it with **Ctrl+C**.
- The server listens on `127.0.0.1` only.
- It serves only:
  - `local_preview/` (static HTML with fictional Czech content);
  - the production CSS, JS and icons from `src/static/`, reused unchanged.
  Everything else returns 404, including the repository root, `.git`, `.env`, sources and tests.
- This is **not the Django application**. Login, the contact form, attendance answers, sheet-music downloads and logout are visual examples only. They show "Toto je pouze lokální náhled…" and send nothing.
- When templates change, update the matching pages in `local_preview/` by hand.
- `local_preview/` and `tools/` are excluded from the Docker image (`.dockerignore`) and are not part of any Django URL.
- Tests, migrations, PostgreSQL, permissions, private files and production behaviour are validated only in GitHub Actions. See [docs/testing.md](docs/testing.md).

## Quality checks

| Command | Purpose |
|---|---|
| `uv run pytest` | Unit and integration tests; fails below 80 % coverage |
| `uv run pytest -m e2e --no-cov` | Browser smoke tests (Playwright, Chromium) |
| `uv run ruff check . && uv run ruff format --check .` | Lint and formatting |
| `uv run mypy src` | Type checking (django-stubs) |
| `uv run bandit -r src -c pyproject.toml` | Static security analysis |
| `uv run pre-commit run --all-files` | All pre-commit hooks |

## Documentation

- [docs/architecture.md](docs/architecture.md) – structure, domains, dependencies
- [docs/security.md](docs/security.md) – threat model and controls
- [docs/privacy-and-compliance.md](docs/privacy-and-compliance.md) – GDPR, retention, copyright
- [docs/deployment.md](docs/deployment.md) – production configuration and release
- [docs/operations.md](docs/operations.md) – backups, accounts, routine tasks
- [docs/testing.md](docs/testing.md) – test strategy and coverage map
- [SECURITY.md](SECURITY.md) – how to report a vulnerability
