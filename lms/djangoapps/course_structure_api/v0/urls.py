"""
Courses Structure API v0 URI specification
"""
from django.conf import settings
from django.conf.urls import patterns, url

from course_structure_api.v0 import views


COURSE_ID_PATTERN = settings.COURSE_ID_PATTERN

urlpatterns = patterns(
    '',
    url(r'^courses/$', views.CourseList.as_view(), name='list'),
    url(r'^courses/{}/$'.format(COURSE_ID_PATTERN), views.CourseDetail.as_view(), name='detail'),
    url(r'^course_structures/{}/$'.format(COURSE_ID_PATTERN), views.CourseStructure.as_view(), name='structure'),
    url(
        r'^grading_policies/{}/$'.format(COURSE_ID_PATTERN),
        views.CourseGradingPolicy.as_view(),
        name='grading_policy'
    ),
)
