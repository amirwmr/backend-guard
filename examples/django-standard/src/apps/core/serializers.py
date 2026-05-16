from __future__ import annotations

from rest_framework import serializers

from apps.core.models import Widget


class WidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Widget
        fields = ("id", "name", "description", "is_active", "created_at")
        read_only_fields = ("id", "created_at")
