from __future__ import annotations

from django.db import models


class Widget(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "widget"
        verbose_name_plural = "widgets"

    def __str__(self) -> str:
        return self.name
