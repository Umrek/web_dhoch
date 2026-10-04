from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from apps.accounts.mixins import PermissionDeniedLoggedMixin, PortalRequiredMixin
from apps.events import selectors as event_selectors
from apps.events.models import Event, EventKind

from . import selectors, services
from .forms import ResponseForm


class MemberEventListView(PortalRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        kind = request.GET.get("druh")
        kind = kind if kind in EventKind.values else None
        upcoming = request.GET.get("archiv") != "1"
        events = list(event_selectors.member_events(kind=kind, upcoming=upcoming)[:100])
        responses = selectors.own_responses(request.user, events)
        now = timezone.now()
        rows = [
            {"event": e, "response": responses.get(str(e.pk)), "open": e.accepts_responses(now)}
            for e in events
        ]
        return render(
            request,
            "attendance/event_list.html",
            {"rows": rows, "kind": kind, "upcoming": upcoming, "kinds": EventKind.choices},
        )


class MemberEventDetailView(PortalRequiredMixin, View):
    def _event(self, slug: str) -> Event:
        return get_object_or_404(Event, slug=slug)

    def get(self, request: HttpRequest, slug: str) -> HttpResponse:
        event = self._event(slug)
        response = selectors.own_responses(request.user, [event]).get(str(event.pk))
        form = ResponseForm(
            initial={"status": response.status, "note": response.note} if response else None
        )
        return self._render(request, event, response, form)

    def post(self, request: HttpRequest, slug: str) -> HttpResponse:
        event = self._event(slug)
        form = ResponseForm(request.POST)
        if form.is_valid():
            try:
                services.respond_to_event(
                    user=request.user,
                    event=event,
                    status=form.cleaned_data["status"],
                    note=form.cleaned_data["note"],
                )
            except services.ResponsesClosed:
                messages.error(request, "Odpovědi na tuto akci jsou již uzavřeny.")
            else:
                messages.success(request, "Vaše odpověď byla uložena.")
            return redirect("attendance:detail", slug=event.slug)
        response = selectors.own_responses(request.user, [event]).get(str(event.pk))
        return self._render(request, event, response, form, status=400)

    def _render(self, request, event, response, form, status: int = 200) -> HttpResponse:
        context = {
            "event": event,
            "response": response,
            "form": form,
            "open": event.accepts_responses(timezone.now()),
            "can_view_overview": request.user.has_perm("attendance.view_attendanceresponse"),
        }
        return render(request, "attendance/event_detail.html", context, status=status)


class EventOverviewView(PermissionDeniedLoggedMixin, View):
    """Organizers/administrators only (model permission); musicians get 403."""

    permission_required = "attendance.view_attendanceresponse"

    def get(self, request: HttpRequest, slug: str) -> HttpResponse:
        event = get_object_or_404(Event, slug=slug)
        if not request.user.is_staff:
            raise PermissionDenied
        return render(
            request,
            "attendance/overview.html",
            {"event": event, "overview": selectors.event_overview(event)},
        )
