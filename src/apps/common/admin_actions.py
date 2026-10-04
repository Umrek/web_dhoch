"""Reusable confirmation step for destructive or security-sensitive admin actions."""

from collections.abc import Callable

from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse


def confirm_action(
    modeladmin: admin.ModelAdmin,
    request: HttpRequest,
    queryset: QuerySet,
    *,
    action_name: str,
    title: str,
    description: str,
    perform: Callable[[object], None],
    success_message: str,
) -> HttpResponse | None:
    """Ask for explicit confirmation, then call ``perform(obj)`` for each object."""
    if request.POST.get("confirm") == "yes":
        count = 0
        for obj in queryset:
            perform(obj)
            count += 1
        modeladmin.message_user(request, success_message.format(count=count), messages.SUCCESS)
        return None
    context = {
        **modeladmin.admin_site.each_context(request),
        "title": title,
        "description": description,
        "objects": list(queryset),
        "action_name": action_name,
        "opts": modeladmin.model._meta,
        "selected": request.POST.getlist(ACTION_CHECKBOX_NAME),
        "action_checkbox_name": ACTION_CHECKBOX_NAME,
    }
    return TemplateResponse(request, "admin/confirm_action.html", context)
