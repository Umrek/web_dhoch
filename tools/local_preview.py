"""Static local preview server.

Static local preview only.
Not used by the production Django application.
Does not validate backend functionality.

Usage (repository root, Python 3.11+ standard library only):
    python tools/local_preview.py [--port 8080] [--no-browser]

Serves exactly two read-only locations, bound to 127.0.0.1 only:
    /                -> local_preview/            (preview HTML, CSS, JS, images)
    /static/...      -> src/static/               (the production CSS/JS/icons, reused unchanged;
                                                   GitHub Pages gets the same files copied to static/)
Everything else (repository root, .git, .env, sources, tests, media) returns 404.
"""

from __future__ import annotations

import argparse
import sys
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

HOST = "127.0.0.1"
REPO_DIR = Path(__file__).resolve().parents[1]
PREVIEW_DIR = (REPO_DIR / "local_preview").resolve()
STATIC_DIR = (REPO_DIR / "src" / "static").resolve()
STATIC_PREFIX = "/static/"

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
}
STATIC_TYPES = {".css", ".js", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".woff2"}

SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
        "connect-src 'none'; form-action 'none'; frame-ancestors 'none'; base-uri 'none'"
    ),
}


def resolve_request_path(raw_path: str) -> Path | None:
    """Map a URL path to an allowed file, or None. Rejects traversal, hidden and unknown files."""
    path = unquote(urlsplit(raw_path).path)
    if "\x00" in path or "\\" in path or not path.startswith("/"):
        return None
    if path.startswith(STATIC_PREFIX):
        base, rel, allowed = STATIC_DIR, path[len(STATIC_PREFIX) :], STATIC_TYPES
    else:
        base, rel, allowed = PREVIEW_DIR, path.lstrip("/"), set(CONTENT_TYPES)
        if rel == "" or rel.endswith("/"):
            rel += "index.html"
    parts = rel.split("/")
    if any(part in {"", ".", ".."} or part.startswith(".") for part in parts):
        return None
    candidate = (base / rel).resolve()
    if not candidate.is_relative_to(base) or not candidate.is_file():
        return None
    if candidate.suffix.lower() not in allowed:
        return None
    return candidate


class PreviewHandler(BaseHTTPRequestHandler):
    server_version = "LocalPreview"
    sys_version = ""

    def do_GET(self) -> None:
        self._serve(include_body=True)

    def do_HEAD(self) -> None:
        self._serve(include_body=False)

    def _reject(self) -> None:
        self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
        self.send_header("Allow", "GET, HEAD")
        self.send_header("Content-Length", "0")
        self.end_headers()

    do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _reject

    def _serve(self, include_body: bool) -> None:
        target = resolve_request_path(self.path)
        status = HTTPStatus.OK
        if target is None:
            status = HTTPStatus.NOT_FOUND
            target = PREVIEW_DIR / "404.html"
        body = target.read_bytes()
        self.send_response(status)
        content_type = CONTENT_TYPES.get(target.suffix.lower(), "application/octet-stream")
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        # Only method, path and status; no client address or headers are logged.
        status = args[1] if len(args) > 1 else ""
        sys.stderr.write(f"  {self.command} {urlsplit(self.path).path} -> {status}\n")


def port_number(value: str) -> int:
    try:
        port = int(value, 10)
    except ValueError:
        raise argparse.ArgumentTypeError("port musí být celé číslo") from None
    if not 1024 <= port <= 65535:
        raise argparse.ArgumentTypeError("port musí být v rozsahu 1024–65535")
    return port


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Statický lokální náhled webu (bez Django, bez instalace)."
    )
    parser.add_argument(
        "--port", type=port_number, default=8080, help="port na 127.0.0.1 (výchozí 8080)"
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="neotevírat prohlížeč automaticky"
    )
    args = parser.parse_args(argv)

    if not (PREVIEW_DIR / "index.html").is_file():
        print(f"Chyba: složka náhledu nebyla nalezena: {PREVIEW_DIR}", file=sys.stderr)
        return 1
    try:
        server = ThreadingHTTPServer((HOST, args.port), PreviewHandler)
    except OSError as exc:
        print(
            f"Chyba: port {args.port} nelze použít ({exc.strerror}). Zkuste --port 8081.",
            file=sys.stderr,
        )
        return 2
    server.daemon_threads = True

    url = f"http://{HOST}:{args.port}/"
    print("Statický lokální náhled webu Dechová hudba Oderské chasy")
    print("Nejde o běžící Django aplikaci; formuláře a přihlášení jsou jen ukázky.")
    print(f"Adresa náhledu: {url}")
    print("Ukončení: stiskněte Ctrl+C.")

    if not args.no_browser:

        def open_browser() -> None:
            try:
                if not webbrowser.open(url):
                    print(f"Prohlížeč se nepodařilo otevřít. Otevřete ručně: {url}")
            except webbrowser.Error:
                print(f"Prohlížeč se nepodařilo otevřít. Otevřete ručně: {url}")

        threading.Timer(0.5, open_browser).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nNáhled ukončen.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
