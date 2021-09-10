"""
URLs for user API
"""


from django.conf import settings

from .views import UserCourseEnrollmentsList, UserCourseStatus, UserDetail
from django.urls import re_path

urlpatterns = [
    re_path('^' + settings.USERNAME_PATTERN + '$', UserDetail.as_view(), name='user-detail'),
    re_path(
        '^' + settings.USERNAME_PATTERN + '/course_enrollments/$',
        UserCourseEnrollmentsList.as_view(),
        name='courseenrollment-detail'
    ),
    re_path(f'^{settings.USERNAME_PATTERN}/course_status_info/{settings.COURSE_ID_PATTERN}',
        UserCourseStatus.as_view(),
        name='user-course-status')
]
