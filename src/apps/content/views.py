from django.http import Http404
from django.views.generic import TemplateView

from apps.events import selectors as event_selectors
from apps.gallery import selectors as gallery_selectors
from apps.musicians import selectors as musician_selectors

from . import selectors
from .models import PageKey

LEGAL_SLUGS = {
    "ochrana-osobnich-udaju": PageKey.PRIVACY,
    "cookies": PageKey.COOKIES,
    "provozovatel": PageKey.OPERATOR,
    "prohlaseni-o-pristupnosti": PageKey.ACCESSIBILITY,
    "bezpecnost": PageKey.SECURITY,
    "odstraneni-fotografie": PageKey.PHOTO_REMOVAL,
}


class HomeView(TemplateView):
    template_name = "content/home.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context.update(
            hero=selectors.get_page(PageKey.HOME_HERO),
            intro=selectors.get_page(PageKey.HOME_INTRO),
            upcoming_events=event_selectors.upcoming_public(limit=3),
            gallery_preview=gallery_selectors.preview_images(limit=6),
        )
        return context


class AboutView(TemplateView):
    template_name = "content/about.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context.update(
            history=selectors.get_page(PageKey.ABOUT_HISTORY),
            style=selectors.get_page(PageKey.ABOUT_STYLE),
            current=selectors.get_page(PageKey.ABOUT_CURRENT),
            roster=musician_selectors.public_roster(),
        )
        return context


class LegalPageView(TemplateView):
    template_name = "content/legal_page.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        key = LEGAL_SLUGS.get(kwargs["slug"])
        if key is None:
            raise Http404
        context["page"] = selectors.get_page(key)
        context["site_settings"] = selectors.get_site_settings()
        return context


class SecurityTxtView(TemplateView):
    template_name = "content/security.txt"
    content_type = "text/plain; charset=utf-8"


class RobotsTxtView(TemplateView):
    template_name = "content/robots.txt"
    content_type = "text/plain; charset=utf-8"
