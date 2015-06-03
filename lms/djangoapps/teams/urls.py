"""
URLs for teams.
"""
from django.conf.urls import patterns, url
from teams.views import TeamsDashboardView


urlpatterns = patterns(
    "teams.views",
    url(r"^/$", TeamsDashboardView.as_view(), name="teams_dashboard"),
)
