import time

from django import forms
from django.conf import settings
from django.core import signing

from apps.common.forms import PlainForm

_SALT = "contact-form-v1"


def issue_token() -> str:
    return signing.dumps(int(time.time()), salt=_SALT)


class ContactForm(PlainForm):
    name = forms.CharField(label="Jméno", max_length=120)
    email = forms.EmailField(label="E-mail", max_length=254)
    message = forms.CharField(
        label="Zpráva", max_length=4000, widget=forms.Textarea(attrs={"rows": 7})
    )
    consent = forms.BooleanField(
        label="Beru na vědomí zpracování osobních údajů za účelem odpovědi na dotaz.",
        error_messages={"required": "Pro odeslání je nutné vzít zpracování údajů na vědomí."},
    )
    # Honeypot: hidden from people (CSS) and assistive tech (aria-hidden on wrapper).
    website = forms.CharField(required=False, label="Web", widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))
    token = forms.CharField(required=False, widget=forms.HiddenInput)

    is_bot = False

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial["token"] = issue_token()

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("website"):
            self.is_bot = True
            return cleaned
        try:
            issued = signing.loads(
                cleaned.get("token", ""), salt=_SALT, max_age=settings.CONTACT_MAX_AGE_SECONDS
            )
        except signing.BadSignature:
            raise forms.ValidationError(
                "Platnost formuláře vypršela. Načtěte stránku znovu a zkuste to prosím ještě jednou."
            ) from None
        if time.time() - issued < settings.CONTACT_MIN_FILL_SECONDS:
            raise forms.ValidationError("Formulář byl odeslán příliš rychle. Zkuste to prosím znovu.")
        return cleaned
