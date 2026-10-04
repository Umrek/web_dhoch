from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from apps.accounts.mixins import PortalRequiredMixin
from apps.content import selectors as content_selectors
from apps.events import selectors as event_selectors

from . import selectors, services
from .forms import ProfileForm


class DashboardView(PortalRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(
            request,
            "musicians/dashboard.html",
            {
                "profile": selectors.profile_for(request.user),
                "rehearsals": event_selectors.next_rehearsals(3),
                "concerts": event_selectors.next_concerts(3),
                "announcements": content_selectors.active_announcements(),
            },
        )


class ProfileView(PortalRequiredMixin, View):
    """Only the logged-in user's own profile is ever loaded (no id in the URL)."""

    def _profile(self, request: HttpRequest):
        return selectors.profile_for(request.user)

    def get(self, request: HttpRequest) -> HttpResponse:
        profile = self._profile(request)
        form = ProfileForm(instance=profile) if profile else None
        return render(request, "musicians/profile.html", {"form": form, "profile": profile})

    def post(self, request: HttpRequest) -> HttpResponse:
        profile = self._profile(request)
        if profile is None:
            return redirect("musicians:profile")
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            services.update_profile(profile, form)
            messages.success(request, "Profil byl uložen.")
            return redirect("musicians:profile")
        return render(request, "musicians/profile.html", {"form": form, "profile": profile}, status=400)
