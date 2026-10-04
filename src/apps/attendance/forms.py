from django import forms

from apps.common.forms import PlainForm

from .models import AttendanceStatus


class ResponseForm(PlainForm):
    status = forms.ChoiceField(label="Vaše odpověď", choices=AttendanceStatus.choices, widget=forms.RadioSelect)
    note = forms.CharField(label="Poznámka (nepovinné)", max_length=300, required=False)
