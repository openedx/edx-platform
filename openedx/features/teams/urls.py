"""Defines the URL routes for this app."""

from django.conf.urls import patterns, url

from lms.djangoapps.teams.api_urls import TEAM_ID_PATTERN, TOPIC_ID_PATTERN
from .views import browse_teams, create_team, my_team, browse_topic_teams, update_team, view_team, edit_team_memberships

urlpatterns = patterns(
    'openedx.features.teams.views',

    url(r"^browse_teams/$", browse_teams, name="teams_dashboard"),
    url(r"^browse_teams/" + TOPIC_ID_PATTERN + "/$", browse_topic_teams, name="browse_topic_teams"),
    url(r"^" + TOPIC_ID_PATTERN + "/create/$", create_team, name="create_team"),
    url(r"^" + TEAM_ID_PATTERN + "/update/$", update_team, name="update_team"),
    url(r"^" + TEAM_ID_PATTERN + "/edit-memberships/$", edit_team_memberships, name="edit_team_memberships"),
    url(r"^my_team/$", my_team, name="my_team"),
    url(r"^team/" + TEAM_ID_PATTERN + "$", view_team, name="view_team"),
)
