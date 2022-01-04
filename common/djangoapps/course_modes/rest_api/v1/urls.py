"""
URL definitions for the course_modes v1 API.
"""


from django.conf import settings

from common.djangoapps.course_modes.rest_api.v1 import views
from django.urls import re_path

app_name = 'v1'

urlpatterns = [
    re_path(
        fr'^courses/{settings.COURSE_ID_PATTERN}/$',
        views.CourseModesView.as_view(),
        name='course_modes_list'
    ),
    re_path(
        fr'^courses/{settings.COURSE_ID_PATTERN}/(?P<mode_slug>.*)$',
        views.CourseModesDetailView.as_view(),
        name='course_modes_detail'
    ),
]
