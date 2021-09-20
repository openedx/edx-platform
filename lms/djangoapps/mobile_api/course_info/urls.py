"""
URLs for course_info API
"""


from django.conf import settings
from django.conf.urls import url

from .views import CourseHandoutsList, CourseUpdatesList, CourseGoalsRecordUserActivity

urlpatterns = [
    url(
        fr'^{settings.COURSE_ID_PATTERN}/handouts$',
        CourseHandoutsList.as_view(),
        name='course-handouts-list'
    ),
    url(
        fr'^{settings.COURSE_ID_PATTERN}/updates$',
        CourseUpdatesList.as_view(),
        name='course-updates-list'
    ),
    url(r'^record_user_activity$', CourseGoalsRecordUserActivity.as_view(), name='record_user_activity'),
]
