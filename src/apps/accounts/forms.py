from django import forms
from django.contrib.auth import forms as auth_forms
from django.contrib.auth import get_user_model

from apps.common.forms import AccessibleFormMixin

User = get_user_model()

GENERIC_LOGIN_ERROR = "Zadaný e-mail nebo heslo není správné."


class EmailAuthenticationForm(AccessibleFormMixin, auth_forms.AuthenticationForm):
    username = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"autocomplete": "username", "autofocus": True}),
    )
    password = forms.CharField(
        label="Heslo",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    error_messages = {"invalid_login": GENERIC_LOGIN_ERROR, "inactive": GENERIC_LOGIN_ERROR}


class PasswordChangeForm(AccessibleFormMixin, auth_forms.PasswordChangeForm):
    pass


class SetPasswordForm(AccessibleFormMixin, auth_forms.SetPasswordForm):
    pass


class PasswordResetForm(AccessibleFormMixin, auth_forms.PasswordResetForm):
    pass


class UserCreateForm(forms.ModelForm):
    """Admin form for creating staff/other accounts (no password; invitation e-mail follows)."""

    class Meta:
        model = User
        fields = ("email", "full_name", "groups")

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Účet s tímto e-mailem už existuje.")
        return email
