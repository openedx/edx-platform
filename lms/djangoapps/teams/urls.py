"""
URLs for teams.
"""
from django.conf.urls import patterns, url
from startup import run


urlpatterns = patterns(
    "teams.views",
    url(r"^/$", "teams_dashboard", name="teams_dashboard"),
)

# HACK: what's the right way to get this executed on start up?
run()
