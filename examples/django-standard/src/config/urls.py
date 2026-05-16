from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

from apps.core.views import health_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_view, name="health"),
    path("api/v1/", include("apps.core.urls")),
]
