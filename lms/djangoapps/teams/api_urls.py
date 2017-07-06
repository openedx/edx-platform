"""Defines the URL routes for the Team API."""

from django.conf import settings
from django.conf.urls import patterns, url

from .views import (
    TeamsListView,
    TeamsDetailView,
    TopicDetailView,
    TopicListView,
    MembershipListView,
    MembershipDetailView
)

TEAM_ID_PATTERN = r'(?P<team_id>[a-z\d_-]+)'
USERNAME_PATTERN = r'(?P<username>[\w.+-]+)'
TOPIC_ID_PATTERN = r'(?P<topic_id>[A-Za-z\d_.-]+)'

urlpatterns = patterns(
    '',
    url(
        r'^v0/teams/$',
        TeamsListView.as_view(),
        name="teams_list"
    ),
    url(
        r'^v0/teams/' + TEAM_ID_PATTERN + '$',
        TeamsDetailView.as_view(),
        name="teams_detail"
    ),
    url(
        r'^v0/topics/$',
        TopicListView.as_view(),
        name="topics_list"
    ),
    url(
        r'^v0/topics/' + TOPIC_ID_PATTERN + ',' + settings.COURSE_ID_PATTERN + '$',
        TopicDetailView.as_view(),
        name="topics_detail"
    ),
    url(
        r'^v0/team_membership/$',
        MembershipListView.as_view(),
        name="team_membership_list"
    ),
    url(
        r'^v0/team_membership/' + TEAM_ID_PATTERN + ',' + USERNAME_PATTERN + '$',
        MembershipDetailView.as_view(),
        name="team_membership_detail"
    )
)
