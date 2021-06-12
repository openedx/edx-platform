"""
Instructor API endpoint urls.
"""

from django.conf.urls import url, include

from openedx.core.constants import COURSE_ID_PATTERN
from .views import api_urls


urlpatterns = [
    url(rf'^courses/{COURSE_ID_PATTERN}/instructor/api/', include(api_urls.urlpatterns)),
    url(
        r'^api/instructor/v1/',
        include((api_urls.v1_api_urls, 'lms.djangoapps.instructor'), namespace='instructor_api_v1'),
    ),
]
