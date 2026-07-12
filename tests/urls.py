"""Test URL configuration for django-telegram-q2."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("django_telegram_q2.telegram.urls")),
]
