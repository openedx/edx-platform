"""
Instructor API endpoint urls.
"""

from django.urls import include, path, re_path

from openedx.core.constants import COURSE_ID_PATTERN
from .views import api_urls


urlpatterns = [
    re_path(rf'^courses/{COURSE_ID_PATTERN}/instructor/api/', include(api_urls.urlpatterns)),
    path(
        'api/instructor/v1/',
        include((api_urls.v1_api_urls, 'lms.djangoapps.instructor'), namespace='instructor_api_v1'),
    ),
]
