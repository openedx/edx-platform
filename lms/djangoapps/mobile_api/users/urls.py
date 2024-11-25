"""
URLs for user API
"""


from django.conf import settings
from django.urls import re_path

<<<<<<< HEAD
from .views import UserCourseEnrollmentsList, UserCourseStatus, UserDetail
=======
from .views import UserCourseEnrollmentsList, UserCourseStatus, UserDetail, UserEnrollmentsStatus
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

urlpatterns = [
    re_path('^' + settings.USERNAME_PATTERN + '$', UserDetail.as_view(), name='user-detail'),
    re_path(
        '^' + settings.USERNAME_PATTERN + '/course_enrollments/$',
        UserCourseEnrollmentsList.as_view(),
        name='courseenrollment-detail'
    ),
    re_path(f'^{settings.USERNAME_PATTERN}/course_status_info/{settings.COURSE_ID_PATTERN}',
            UserCourseStatus.as_view(),
<<<<<<< HEAD
            name='user-course-status')
=======
            name='user-course-status'),
    re_path(f'^{settings.USERNAME_PATTERN}/enrollments_status/',
            UserEnrollmentsStatus.as_view(),
            name='user-enrollments-status')
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
]
