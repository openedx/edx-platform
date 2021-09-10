"""
URLs for course_info API
"""


from django.conf import settings

from .views import CourseHandoutsList, CourseUpdatesList
from django.urls import re_path

urlpatterns = [
    re_path(
        fr'^{settings.COURSE_ID_PATTERN}/handouts$',
        CourseHandoutsList.as_view(),
        name='course-handouts-list'
    ),
    re_path(
        fr'^{settings.COURSE_ID_PATTERN}/updates$',
        CourseUpdatesList.as_view(),
        name='course-updates-list'
    ),
]
