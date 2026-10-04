from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from . import services
from .forms import ContactForm


@require_http_methods(["GET", "POST"])
def contact(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            if not form.is_bot:  # bots get the same success page and nothing is stored
                try:
                    services.check_rate_limit(request)
                except services.RateLimited:
                    return render(request, "contact/form.html", {"form": ContactForm(), "rate_limited": True}, status=429)
                services.submit_message(
                    name=form.cleaned_data["name"],
                    email=form.cleaned_data["email"],
                    message=form.cleaned_data["message"],
                )
            return redirect("contact:thanks")
        if form.is_bot:
            return redirect("contact:thanks")
        return render(request, "contact/form.html", {"form": form}, status=400)
    return render(request, "contact/form.html", {"form": ContactForm()})


@require_http_methods(["GET"])
def thanks(request: HttpRequest) -> HttpResponse:
    return render(request, "contact/thanks.html")
