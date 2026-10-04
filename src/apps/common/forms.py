"""Accessible form helpers shared by all domains."""

from django import forms


class AccessibleFormMixin:
    """Wire aria-describedby/aria-invalid for help texts and errors after validation."""

    def full_clean(self) -> None:
        super().full_clean()  # type: ignore[misc]
        for name, field in self.fields.items():  # type: ignore[attr-defined]
            bound = self[name]  # type: ignore[index]
            described: list[str] = []
            if field.help_text:
                described.append(f"{bound.auto_id}_helptext")
            if bound.errors:
                described.append(f"{bound.auto_id}_error")
                field.widget.attrs["aria-invalid"] = "true"
            if described:
                field.widget.attrs["aria-describedby"] = " ".join(described)


class PlainForm(AccessibleFormMixin, forms.Form):
    pass


class PlainModelForm(AccessibleFormMixin, forms.ModelForm):
    pass
