# PowerShell helper for Windows developers (no make required). Usage: .\scripts\dev.ps1 <task>
param([Parameter(Position = 0)][string]$Task = "help")
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

switch ($Task) {
    "setup"     { uv sync --frozen; uv run pre-commit install }
    "run"       { uv run python src/manage.py migrate --noinput; uv run python src/manage.py sync_roles; uv run python src/manage.py runserver }
    "test"      { uv run pytest }
    "lint"      { uv run ruff check .; uv run ruff format --check .; uv run djlint --lint src/templates }
    "format"    { uv run ruff check --fix .; uv run ruff format . }
    "typecheck" { uv run mypy src }
    "check"     { uv run python src/manage.py check; uv run python src/manage.py makemigrations --check --dry-run }
    "demo"      { uv run python src/manage.py load_demo_data }
    "e2e"       { uv run playwright install chromium; uv run pytest -m e2e --no-cov }
    default     { Write-Host "Tasks: setup run test lint format typecheck check demo e2e" }
}
