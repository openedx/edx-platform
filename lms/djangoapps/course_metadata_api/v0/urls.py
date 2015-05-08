"""
Courses Metadata API v0 URI specification
"""
from django.conf import settings
from django.conf.urls import patterns, url

from course_metadata_api.v0 import views


COURSE_ID_PATTERN = settings.COURSE_ID_PATTERN

urlpatterns = patterns(
    '',
    url(r'^courses/$', views.CourseList.as_view(), name='list'),
    url(r'^courses/{}/$'.format(COURSE_ID_PATTERN), views.CourseDetail.as_view(), name='detail'),
)
