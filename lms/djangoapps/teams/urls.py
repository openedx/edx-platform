"""Defines the URL routes for this app."""

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from .views import TeamsDashboardView

urlpatterns = patterns(
    'teams.views',
    url(r"^/$", login_required(TeamsDashboardView.as_view()), name="teams_dashboard")
)
