from django.core.paginator import Paginator
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from . import selectors
from .ics import build_event_ics


@require_GET
def event_list(request: HttpRequest) -> HttpResponse:
    events = selectors.upcoming_public()
    return render(
        request,
        "events/list.html",
        {"month_groups": selectors.month_groups(events), "has_events": bool(events)},
    )


@require_GET
def event_archive(request: HttpRequest) -> HttpResponse:
    paginator = Paginator(selectors.past_public(), 20)
    page = paginator.get_page(request.GET.get("strana"))
    return render(request, "events/archive.html", {"page": page})


@require_GET
def event_detail(request: HttpRequest, slug: str) -> HttpResponse:
    event = selectors.public_event(slug)
    if event is None:
        raise Http404
    return render(
        request,
        "events/detail.html",
        {"event": event, "is_past": event.starts_at < timezone.now()},
    )


@require_GET
def event_ics(request: HttpRequest, slug: str) -> HttpResponse:
    event = selectors.public_event(slug)
    if event is None:
        raise Http404
    response = HttpResponse(build_event_ics(event), content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{event.slug}.ics"'
    return response
