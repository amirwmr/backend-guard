from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.core.models import Widget
from apps.core.serializers import WidgetSerializer


def health_view(_request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok", "service": "django-standard"})


class WidgetListCreateView(generics.ListCreateAPIView):
    serializer_class = WidgetSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return Widget.objects.filter(is_active=True).order_by("name")
