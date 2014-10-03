"""
URLs for user API
"""
from django.conf.urls import patterns, url

from .views import UserDetail, UserCourseEnrollmentsList

urlpatterns = patterns(
    'mobile_api.users.views',
    url(r'^(?P<username>[\w.+-]+)$', UserDetail.as_view(), name='user-detail'),
    url(
        r'^(?P<username>[\w.+-]+)/course_enrollments/$',
        UserCourseEnrollmentsList.as_view(),
        name='courseenrollment-detail'
    ),
)
