"""
URLs for user API
"""
from django.conf.urls import patterns, url
from django.conf import settings

from .views import UserDetail, UserCourseEnrollmentsList, UserCourseStatus

USERNAME_PATTERN = r'(?P<username>[\w.+-]+)'

urlpatterns = patterns(
    'mobile_api.users.views',
    url('^' + USERNAME_PATTERN + '$', UserDetail.as_view(), name='user-detail'),
    url(
        '^' + USERNAME_PATTERN + '/course_enrollments/$',
        UserCourseEnrollmentsList.as_view(),
        name='courseenrollment-detail'
    ),
    url('^{}/course_status_info/{}'.format(USERNAME_PATTERN, settings.COURSE_ID_PATTERN),
        UserCourseStatus.as_view(),
        name='user-course-status')
)
