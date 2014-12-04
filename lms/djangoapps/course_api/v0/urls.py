"""
Courses API v0 URI specification
The order of the URIs really matters here, due to the slash characters present in the identifiers
"""
from django.conf import settings
from django.conf.urls import patterns, url, include
from rest_framework.urlpatterns import format_suffix_patterns

from course_api.v0 import views


CONTENT_ID_PATTERN = r'(?P<content_id>[\.a-zA-Z0-9_+\/:-]+)'
COURSE_ID_PATTERN = settings.COURSE_ID_PATTERN

# pylint: disable=invalid-name
content_patterns = patterns(
    '',
    url(r'^$', views.CourseContentList.as_view(), name='list'),
    url(r'^{}/$'.format(CONTENT_ID_PATTERN), views.CourseContentDetail.as_view(), name='detail'),
)

course_patterns = patterns(
    '',
    url(r'^$', views.CourseDetail.as_view(), name='detail'),
    url(r'^graded_content/$', views.CourseGradedContent.as_view(), name='graded_content'),
    url(r'^grading_policy/$', views.CourseGradingPolicy.as_view(), name='grading_policy'),
    url(r'^content/', include(content_patterns, namespace='content')),
)

urlpatterns = patterns(
    '',
    url(r'^$', views.CourseList.as_view(), name='list'),
    url(r'^{}/'.format(COURSE_ID_PATTERN), include(course_patterns))
)

urlpatterns = format_suffix_patterns(urlpatterns)
