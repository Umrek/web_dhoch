# Security

## Threats considered

| Threat | Controls |
|---|---|
| Password guessing | django-axes locks per account and per IP. Passwords at least 12 characters plus Django validators. Accounts are created only by invitation (no public sign-up) |
| Account enumeration | Password reset always gives the same answer. Login errors are generic |
| Host-header poisoning in e-mail links | Invitation and reset links are built from `SITE_URL`, never from the request `Host` |
| Unauthorized data access (IDOR) | Object-level checks (see architecture.md). Own data is always taken from the session |
| Privilege escalation | Roles come from fixed permission lists. `is_staff` is derived from roles. Musicians get 403 on organizer pages |
| XSS | Auto-escaping everywhere. Editable content is plain text. CSP without `unsafe-inline` scripts. No inline event handlers |
| CSRF / clickjacking | Django CSRF middleware. Logout is POST only. `X-Frame-Options: DENY` and `frame-ancestors 'none'` |
| Malicious uploads | Sheet music: `.pdf` extension, `%PDF-` signature and size limit, random storage names. Photos: decoded by Pillow with a pixel-bomb limit, then re-encoded to JPEG (drops EXIF/GPS and embedded payloads) |
| Direct file access | Private storage raises on `.url()`. No `MEDIA_URL`. Files are served only through views that check permissions. PDFs go out with `Content-Disposition: attachment`, `Cache-Control: private, no-store` and `nosniff` |
| Contact-form spam | Honeypot, signed timestamp (minimum fill time and maximum age), and a per-client rate limit keyed by a salted hash of the client IP |
| Rate-limit evasion via spoofed `X-Forwarded-For` | Only the hop added by our own trusted proxy (`PROXY_COUNT`) is used |
| Session theft | `__Host-` cookie names, `Secure`, `HttpOnly`, `SameSite=Lax`, HSTS, SSL redirect |
| Misconfiguration | Production settings refuse to start with a weak or missing secret, wildcard hosts, a non-https origin or `SITE_URL`, a non-PostgreSQL database, or missing e-mail settings |
| Supply chain | Exact pins, a hash-locked `uv.lock` generated only in CI, `uv sync --frozen`, pip-audit, Dependabot, dependency review, gitleaks, CodeQL |

## Headers

Set by `SecurityHeadersMiddleware`, Django's security middleware and django-csp:

- CSP (`default-src 'self'`, no inline scripts, `object-src 'none'`, `frame-ancestors 'none'`)
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: same-origin`
- `Permissions-Policy` that disables unused browser features
- `Cross-Origin-Opener-Policy: same-origin`

## Logging and auditing

Logs are JSON lines on stdout, each with a request ID. Security events (`security` logger) include:

- portal and permission denials
- lockouts
- sheet-music downloads
- attendance changes
- consent changes for the public roster

Admin actions (status changes, uploads, deletions, purges) are logged by `log_admin_event`. Logs never contain passwords, tokens, message bodies or raw IP addresses.

## Secrets

- Secrets come only from environment variables.
- `.env` is git-ignored, and `.env.example` contains placeholders only.
- gitleaks scans every push.
- Rotate `SECRET_KEY` with `SECRET_KEY_FALLBACKS`: add the old key there, deploy, then remove it after the session lifetime.

## Known limitations

- No two-factor authentication. Admin accounts should use long, unique passwords from a password manager.
- Rate limiting depends on the shared database cache. It is not a substitute for network-level protection against floods.
- Uploaded PDFs are checked for type, not scanned for malware. Only trusted staff can upload them.
