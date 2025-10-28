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
    re_path(
        r'^api/instructor/courses/{course_id}/'.format(
            course_id=COURSE_ID_PATTERN
        ),
        include((api_urls.urlpatterns, 'lms.djangoapps.instructor'), namespace='instructor_api_course_patterns'),
    ),
]
