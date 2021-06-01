# pylint: skip-file
"""
Discussion API URLs
"""


from django.conf import settings
from django.conf.urls import include, url
from rest_framework.routers import SimpleRouter

from lms.djangoapps.discussion.rest_api.views import (
    CommentViewSet,
    CourseDiscussionRolesAPIView,
    CourseDiscussionSettingsAPIView,
    CourseTopicsView,
    CourseView,
    ReplaceUsernamesView,
    RetireUserView,
    ThreadViewSet
)

ROUTER = SimpleRouter()
ROUTER.register("threads", ThreadViewSet, basename="thread")
ROUTER.register("comments", CommentViewSet, basename="comment")

urlpatterns = [
    url(
        r"^v1/courses/{}/settings$".format(
            settings.COURSE_ID_PATTERN
        ),
        CourseDiscussionSettingsAPIView.as_view(),
        name="discussion_course_settings",
    ),
    url(
        r"^v1/courses/{}/roles/(?P<rolename>[A-Za-z0-9+ _-]+)/?$".format(
            settings.COURSE_ID_PATTERN
        ),
        CourseDiscussionRolesAPIView.as_view(),
        name="discussion_course_roles",
    ),
    url(
        r"^v1/courses/{}".format(settings.COURSE_ID_PATTERN),
        CourseView.as_view(),
        name="discussion_course"
    ),
    url(r"^v1/accounts/retire_forum", RetireUserView.as_view(), name="retire_discussion_user"),
    url(r"^v1/accounts/replace_username", ReplaceUsernamesView.as_view(), name="replace_discussion_username"),
    url(
        r"^v1/course_topics/{}".format(settings.COURSE_ID_PATTERN),
        CourseTopicsView.as_view(),
        name="course_topics"
    ),
    url("^v1/", include(ROUTER.urls)),
]
