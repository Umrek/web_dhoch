from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.common.admin_actions import confirm_action
from apps.common.audit import log_admin_event

from . import services
from .forms import UserCreateForm
from .roles import STAFF_ROLES  # noqa: F401  (documented dependency of refresh_staff_flag)

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "is_active", "role_list", "last_login")
    list_filter = ("is_active", "groups")
    search_fields = ("email", "full_name")
    readonly_fields = ("last_login", "date_joined")
    filter_horizontal = ("groups", "user_permissions")
    actions = ["send_invitation_action", "deactivate_action"]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).prefetch_related("groups")

    @admin.display(description="Role")
    def role_list(self, obj: "User") -> str:
        return ", ".join(group.name for group in obj.groups.all())

    def get_form(self, request: HttpRequest, obj: "User | None" = None, **kwargs: object):
        if obj is None:
            kwargs["form"] = UserCreateForm
            kwargs["fields"] = ("email", "full_name", "groups")
        return super().get_form(request, obj, **kwargs)

    def get_fieldsets(self, request: HttpRequest, obj: "User | None" = None):
        if obj is None:
            return [(None, {"fields": ("email", "full_name", "groups")})]
        sets: list = [
            (None, {"fields": ("email", "full_name", "is_active", "groups")}),
            ("Záznam", {"fields": ("last_login", "date_joined")}),
        ]
        if request.user.is_superuser:
            sets.insert(
                1,
                ("Oprávnění (pouze superuživatel)", {"fields": ("is_superuser", "user_permissions")}),
            )
        return sets

    def has_delete_permission(self, request: HttpRequest, obj: "User | None" = None) -> bool:
        # Accounts are deactivated or anonymised, never hard-deleted from the admin.
        return False

    def has_change_permission(self, request: HttpRequest, obj: "User | None" = None) -> bool:
        if obj is not None and obj.is_superuser and not request.user.is_superuser:
            return False  # prevents vertical privilege escalation / takeover of superusers
        return super().has_change_permission(request, obj)

    def save_model(self, request: HttpRequest, obj: "User", form, change: bool) -> None:
        if not change:
            obj.set_unusable_password()
        super().save_model(request, obj, form, change)

    def save_related(self, request: HttpRequest, form, formsets, change: bool) -> None:
        old_roles = {getattr(g, "pk", g) for g in form.initial.get("groups", [])} if change else set()
        super().save_related(request, form, formsets, change)
        user = form.instance
        services.refresh_staff_flag(user)
        new_roles = set(user.groups.values_list("pk", flat=True))
        if new_roles != old_roles:
            log_admin_event("roles_changed", user_id=str(user.pk), actor_id=str(request.user.pk))
        if not change:
            services.send_invitation(user)
            self.message_user(request, "Pozvánka byla odeslána.", messages.SUCCESS)

    @admin.action(description="Odeslat odkaz pro nastavení hesla")
    def send_invitation_action(self, request: HttpRequest, queryset: QuerySet) -> None:
        sent = 0
        for user in queryset.filter(is_active=True):
            if user.is_superuser and not request.user.is_superuser:
                continue
            services.send_invitation(user)
            sent += 1
        self.message_user(request, f"Odesláno odkazů: {sent}.", messages.SUCCESS)

    @admin.action(description="Deaktivovat vybrané účty")
    def deactivate_action(self, request: HttpRequest, queryset: QuerySet):
        queryset = queryset.exclude(pk=request.user.pk)
        if not request.user.is_superuser:
            queryset = queryset.filter(is_superuser=False)
        return confirm_action(
            self,
            request,
            queryset,
            action_name="deactivate_action",
            title="Potvrdit deaktivaci účtů",
            description="Deaktivované účty se nebudou moci přihlásit.",
            perform=lambda user: services.set_user_active(user, active=False, actor=request.user),
            success_message="Deaktivováno účtů: {count}.",
        )
