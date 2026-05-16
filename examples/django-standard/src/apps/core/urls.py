from __future__ import annotations

from django.urls import path

from apps.core.views import WidgetListCreateView

urlpatterns = [
    path("widgets/", WidgetListCreateView.as_view(), name="widget-list"),
]
