"""Read operations for content. Falls back to placeholder text when a page is missing."""

from dataclasses import dataclass

from django.db.models import Q
from django.utils import timezone

from .defaults import DEFAULT_PAGES
from .models import Announcement, Page, SiteSettings


@dataclass(frozen=True)
class PageContent:
    key: str
    title: str
    intro: str
    body: str
    needs_legal_review: bool


LEGAL_KEYS = {
    "ochrana-osobnich-udaju",
    "cookies",
    "provozovatel",
    "prohlaseni-o-pristupnosti",
    "bezpecnost",
    "odstraneni-fotografie",
}


def get_page(key: str) -> PageContent:
    page = Page.objects.filter(key=key).first()
    if page is not None:
        return PageContent(key, page.title, page.intro, page.body, page.needs_legal_review)
    title, intro, body = DEFAULT_PAGES[key]
    return PageContent(key, title, intro, body, needs_legal_review=key in LEGAL_KEYS)


def get_site_settings() -> SiteSettings:
    return SiteSettings.load()


def active_announcements(limit: int = 5) -> list[Announcement]:
    now = timezone.now()
    queryset = Announcement.objects.filter(is_active=True, published_at__lte=now).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    )
    return list(queryset[:limit])
