# Privacy and compliance

> These are technical measures. The legal texts on the site are placeholders marked "[Doplní provozovatel]" and must be reviewed by the operator before launch. Each legal page shows a "not final" notice until `needs_legal_review` is switched off in the admin.

## Personal data processed

| Data | Whose | Purpose | Visibility | Retention |
|---|---|---|---|---|
| E-mail, name, password hash | Members, staff | Account and login | Administrators | While the account exists |
| Profile: display name, section, instrument | Members | Band organization | Members and staff; public **only with opt-in** | While the account exists |
| Phone (optional) | Members | Contact by organizers | Administrators only, never public | While the account exists |
| Attendance answers and notes | Members | Event planning | The member; organizers and administrators | With the event |
| Contact messages (name, e-mail, text) | Visitors | Answering the inquiry | Administrators | `CONTACT_RETENTION_DAYS` (default 90), then purged |
| Photos | People in photos | Presenting the band | Public when published | Until removed |
| Security logs | Everyone | Security and troubleshooting | Operator | Per hosting log retention |

No analytics or third-party trackers are used. The only cookies are the session cookie and the CSRF cookie (both strictly necessary), so no consent banner is needed. This assumes no tracking is added later.

## Built-in measures

- **Public-roster consent:** opt-in, can be withdrawn at any time in "Můj profil". The time of each change is recorded (`public_listing_changed_at`) and logged. Only name, section and instrument are ever shown.
- **Contact form:** an explicit acknowledgement is required. No IP address or user agent is stored. The rate limiter keeps only a salted hash in the cache, which expires with the rate-limit window.
- **Retention:** schedule `python manage.py purge_contact_messages` daily (see operations.md).
- **Photo metadata:** EXIF and GPS data are removed on upload, and originals are never kept. A removal-request page is linked from the gallery.
- **Data minimization:** public pages and `.ics` files never contain internal notes, phone numbers or e-mail addresses.

## Data-subject requests

| Request | How to handle it |
|---|---|
| Access | An administrator exports the user's profile and attendance from the admin site |
| Rectification | Members edit their own profile; administrators edit the rest |
| Erasure | Deleting the user removes the profile and attendance (cascade). Uploaded sheet music keeps the file, with the uploader set to empty |
| Photo removal | Delete the image in the admin. Its files are deleted together with the database row |

## Copyright (sheet music and photos)

Sheet music may be protected by copyright. Uploading requires confirming the right to share the file within the band. Files are available to logged-in members only, and the list page shows a reminder not to redistribute them. Photos should only be uploaded with the photographer's permission.

## Accessibility

The target is WCAG 2.1 AA:

- skip link, landmarks, `lang="cs"`
- visible focus, labelled form fields, error summary with links to the fields
- table captions, alternative text required for every photo
- reduced-motion support

The accessibility statement page is a placeholder for the operator to complete.
