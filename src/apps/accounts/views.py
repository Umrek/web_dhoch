from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import views as auth_views
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

from . import forms


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = forms.EmailAuthenticationForm
    redirect_authenticated_user = True


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = forms.PasswordChangeForm
    success_url = reverse_lazy("accounts:password_change_done")


class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"


class PasswordResetView(auth_views.PasswordResetView):
    """Always answers identically (no account enumeration); links use SITE_URL, not Host."""

    template_name = "accounts/password_reset_form.html"
    form_class = forms.PasswordResetForm
    email_template_name = "accounts/email/password_reset.txt"
    html_email_template_name = "accounts/email/password_reset.html"
    subject_template_name = "accounts/email/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")

    def form_valid(self, form: forms.PasswordResetForm) -> HttpResponseRedirect:
        site = urlparse(settings.SITE_URL)
        form.save(
            domain_override=site.netloc,
            use_https=site.scheme == "https",
            token_generator=self.token_generator,
            from_email=self.from_email,
            email_template_name=self.email_template_name,
            subject_template_name=self.subject_template_name,
            request=self.request,
            html_email_template_name=self.html_email_template_name,
            extra_email_context={"site_name": settings.SITE_NAME},
        )
        return HttpResponseRedirect(self.get_success_url())


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = forms.SetPasswordForm
    success_url = reverse_lazy("accounts:password_reset_complete")


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"
