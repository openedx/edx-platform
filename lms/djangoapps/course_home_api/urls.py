"""
Contains all the URLs for the Course Home
"""


from django.conf import settings
from django.urls import re_path

from lms.djangoapps.course_home_api.dates.v1.views import DatesTabView
from lms.djangoapps.course_home_api.course_metadata.v1.views import CourseHomeMetadataView
from lms.djangoapps.course_home_api.outline.v1.views import OutlineTabView

urlpatterns = []

# URL for Course metadata content
urlpatterns += [
    re_path(
        r'v1/course_metadata/{}'.format(settings.COURSE_KEY_PATTERN),
        CourseHomeMetadataView.as_view(),
        name='course-home-course-metadata'
    ),
]

# Dates Tab URLs
urlpatterns += [
    re_path(
        r'v1/dates/{}'.format(settings.COURSE_KEY_PATTERN),
        DatesTabView.as_view(),
        name='course-home-dates-tab'
    ),
]

# Outline Tab URLs
urlpatterns += [
    re_path(
        r'v1/outline/{}'.format(settings.COURSE_KEY_PATTERN),
        OutlineTabView.as_view(),
        name='course-home-outline-tab'
    ),
]
