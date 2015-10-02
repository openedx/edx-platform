"""
Course API URLs
"""
from django.conf import settings
from django.conf.urls import patterns, url, include

from .views import CourseView


urlpatterns = patterns(
    '',
    url(r'^v1/courses/{}'.format(settings.COURSE_KEY_PATTERN), CourseView.as_view(), name="course_detail"),
    url(r'', include('course_api.blocks.urls'))
)
