"""
Discussion API URLs
"""
from django.conf import settings
from django.conf.urls import include, patterns, url

from rest_framework.routers import SimpleRouter

from discussion_api.views import CommentViewSet, CourseTopicsView, ThreadViewSet


ROUTER = SimpleRouter()
ROUTER.register("threads", ThreadViewSet, base_name="thread")
ROUTER.register("comments", CommentViewSet, base_name="comment")

urlpatterns = patterns(
    "discussion_api",
    url(
        r"^v1/course_topics/{}".format(settings.COURSE_ID_PATTERN),
        CourseTopicsView.as_view(),
        name="course_topics"
    ),
    url("^v1/", include(ROUTER.urls)),
)
