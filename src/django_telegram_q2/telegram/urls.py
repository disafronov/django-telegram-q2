"""URL configuration for django-telegram-q2 webhook endpoint."""

from django.urls import path

from . import views

urlpatterns = [
    path("webhook/", views.webhook, name="webhook"),
]
