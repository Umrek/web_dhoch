from apps.common.forms import PlainModelForm

from .models import MusicianProfile


class ProfileForm(PlainModelForm):
    """Self-service profile; users can only edit their own non-privileged fields."""

    class Meta:
        model = MusicianProfile
        fields = ["display_name", "instrument", "phone", "public_listing"]
