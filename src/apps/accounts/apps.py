from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "apps.accounts"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = "Uživatelské účty"

    def ready(self) -> None:
        # Secondary, non-critical reaction only: write a security log line on lockout.
        from axes.signals import user_locked_out

        from .signals import log_lockout

        user_locked_out.connect(log_lockout, dispatch_uid="accounts.log_lockout")
