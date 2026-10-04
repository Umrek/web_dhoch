from django.utils import timezone

from apps.common.audit import log_security_event

from .models import MusicianProfile


def update_profile(profile: MusicianProfile, form) -> MusicianProfile:
    """Save a validated ProfileForm; records consent changes for the public listing."""
    previous = MusicianProfile.objects.values_list("public_listing", flat=True).get(pk=profile.pk)
    updated = form.save(commit=False)
    if updated.public_listing != previous:
        updated.public_listing_changed_at = timezone.now()
        log_security_event(
            "public_listing_consent_changed",
            user_id=str(profile.user_id),
            public=updated.public_listing,
        )
    updated.save()
    return updated
