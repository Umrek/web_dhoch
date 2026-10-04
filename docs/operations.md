# Operations

## Scheduled tasks

| When | Command | Why |
|---|---|---|
| Daily | `docker compose run --rm web python manage.py purge_contact_messages` | Enforces contact-message retention (GDPR storage limitation) |
| Daily | Database and file backup (below) | Recovery |
| Weekly | `docker compose run --rm web python manage.py clearsessions` | Removes expired sessions |
| Monthly | Merge Dependabot pull requests, then run **Update uv.lock** if needed | Security updates |

Use cron or a systemd timer on the host. Example: `0 3 * * * cd /srv/oderske-chasy && docker compose run --rm web python manage.py purge_contact_messages`.

## Backups

The following must be backed up together:

- the PostgreSQL database: `docker compose exec db pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" > backup.dump`
- the `gallery_data` volume
- the `sheet_music_data` volume

Store the backups encrypted and off the host, because they contain personal data. Test a restore at least twice a year:

1. Restore into a fresh stack with `pg_restore -c`.
2. Copy the volumes back.
3. Run `python manage.py check` and open a few photos and PDFs.

## Accounts

| Task | How |
|---|---|
| **Invite a member** | In the admin, create the user without a password and assign roles. Use the action “Odeslat odkaz pro nastavení hesla”, which e-mails a one-hour setup link. Then create the musician profile. |
| **Change roles** | Edit the user's groups. Admin access (`is_staff`) follows the roles automatically. |
| **Member leaves** | Deactivate the account (they can no longer log in, and drop from the public roster). Delete it only on request (see privacy-and-compliance.md). |
| **Locked out** | Lockouts expire after 15 minutes. To unlock sooner: `python manage.py axes_reset_username <email>`. |
| **Lost administrator access** | Run `python manage.py createsuperuser` in the container. |

## Logs and monitoring

The container writes JSON lines to stdout, which you read with `docker compose logs web`. Useful filters:

| Filter | Shows |
|---|---|
| `"logger": "security"` | Denials, lockouts, downloads |
| `"level": "ERROR"` | Failures |

Each request has an `X-Request-ID` response header for correlating logs.

Monitor `/health/ready/` from outside. A non-200 response means the database is unreachable.

## Incidents

**Suspected compromise:**

1. Rotate `SECRET_KEY`. This logs everybody out; to rotate without logging people out, use `SECRET_KEY_FALLBACKS`.
2. Reset administrator passwords.
3. Review the `security` logs.
4. Restore from backup if data was altered.

**Personal-data breach:** the operator decides on reporting to the data-protection authority (ÚOOÚ) within 72 hours.

**Photo removal request:** delete the image in the admin within a reasonable time, and confirm to the requester.

## Manual accessibility check (each release)

1. Navigate the home page, the event list, the contact form and login using only the keyboard. The focus must stay visible.
2. Submit the contact form empty. The error summary must receive focus and link to each field.
3. Zoom to 200 % and use a 320 px wide window. There must be no horizontal scrolling of the content.
4. Read the gallery with a screen reader. Every photo must have meaningful alternative text.
