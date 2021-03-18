"""
URL definitions for the course_modes v1 API.
"""


from django.conf import settings
from django.conf.urls import url

from common.djangoapps.course_modes.rest_api.v1 import views

app_name = 'v1'

urlpatterns = [
    url(
        fr'^courses/{settings.COURSE_ID_PATTERN}/$',
        views.CourseModesView.as_view(),
        name='course_modes_list'
    ),
    url(
        fr'^courses/{settings.COURSE_ID_PATTERN}/(?P<mode_slug>.*)$',
        views.CourseModesDetailView.as_view(),
        name='course_modes_detail'
    ),
]
