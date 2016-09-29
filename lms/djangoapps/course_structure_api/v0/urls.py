"""
Courses Structure API v0 URI specification

TODO: delete me once grading policy is implemented in course_api.
"""
from django.conf import settings
from django.conf.urls import patterns, url

from course_structure_api.v0 import views


COURSE_ID_PATTERN = settings.COURSE_ID_PATTERN

urlpatterns = patterns(
    '',
    url(
        r'^grading_policies/{}/$'.format(COURSE_ID_PATTERN),
        views.CourseGradingPolicy.as_view(),
        name='grading_policy'
    ),
)
