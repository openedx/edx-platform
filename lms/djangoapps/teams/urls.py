"""Defines the URL routes for this app."""

from django.conf.urls import patterns, url

from .views import TeamsDashboardView

urlpatterns = patterns(
    'teams.views',
    url(r"^/$", TeamsDashboardView.as_view(), name="teams_dashboard")
)
