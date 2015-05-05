"""
Discussion API URLs
"""
from django.conf import settings
from django.conf.urls import patterns, url

from discussion_api.views import CourseTopicsView


urlpatterns = patterns(
    "discussion_api",
    url(
        r"^v1/course_topics/{}".format(settings.COURSE_ID_PATTERN),
        CourseTopicsView.as_view(),
        name="course_topics"
    ),
)
