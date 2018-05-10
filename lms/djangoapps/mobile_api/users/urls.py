"""
URLs for user API
"""
from django.conf import settings
from django.conf.urls import patterns, url

from .views import UserCourseEnrollmentsList, UserCourseStatus, UserDetail

urlpatterns = patterns(
    'mobile_api.users.views',
    url('^' + settings.USERNAME_PATTERN + '$', UserDetail.as_view(), name='user-detail'),
    url(
        '^' + settings.USERNAME_PATTERN + '/course_enrollments/$',
        UserCourseEnrollmentsList.as_view(),
        name='courseenrollment-detail'
    ),
    url('^{}/course_status_info/{}'.format(settings.USERNAME_PATTERN, settings.COURSE_ID_PATTERN),
        UserCourseStatus.as_view(),
        name='user-course-status')
)
