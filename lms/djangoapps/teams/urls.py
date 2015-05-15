"""
URLs for teams.
"""
from django.conf.urls import patterns, url


urlpatterns = patterns(
    "teams.views",
    url(r"^/$", "teams_dashboard", name="teams_dashboard"),
)
