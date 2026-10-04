from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.common.audit import log_admin_event
from apps.contact.models import ContactMessage


class Command(BaseCommand):
    help = "Delete contact messages older than CONTACT_RETENTION_DAYS (GDPR storage limitation)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--dry-run", action="store_true", help="Only report the count.")

    def handle(self, *args, **options) -> None:
        cutoff = timezone.now() - timedelta(days=settings.CONTACT_RETENTION_DAYS)
        expired = ContactMessage.objects.filter(created_at__lt=cutoff)
        count = expired.count()
        if options["dry_run"]:
            self.stdout.write(f"Would delete {count} message(s).")
            return
        expired.delete()
        log_admin_event("contact_messages_purged", count=count)
        self.stdout.write(f"Deleted {count} message(s).")
