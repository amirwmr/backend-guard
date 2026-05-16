from __future__ import annotations

from django.contrib import admin

from apps.core.models import Widget


@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
