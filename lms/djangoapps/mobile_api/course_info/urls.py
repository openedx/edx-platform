"""
URLs for course_info API
"""


from django.conf import settings
from django.urls import path, re_path

<<<<<<< HEAD
from .views import CourseHandoutsList, CourseUpdatesList, CourseGoalsRecordUserActivity, BlocksInfoInCourseView
=======
from .views import (
    BlocksInfoInCourseView,
    CourseEnrollmentDetailsView,
    CourseGoalsRecordUserActivity,
    CourseHandoutsList,
    CourseUpdatesList
)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

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
<<<<<<< HEAD
=======
    re_path(
        fr'^{settings.COURSE_ID_PATTERN}/enrollment_details$',
        CourseEnrollmentDetailsView.as_view(),
        name='course-enrollment-details'
    ),
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    path('record_user_activity', CourseGoalsRecordUserActivity.as_view(), name='record_user_activity'),
    path('blocks/', BlocksInfoInCourseView.as_view(), name="blocks_info_in_course"),
]
