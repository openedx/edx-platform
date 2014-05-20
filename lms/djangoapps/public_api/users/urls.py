from django.conf.urls import patterns, url, include
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from .views import UserDetail, UserCourseEnrollmentsList

urlpatterns = patterns('public_api.users.views',
    url(r'^(?P<username>\w+)$', UserDetail.as_view(), name='user-detail'),
    url(
        r'^(?P<username>\w+)/course_enrollments/$',
        UserCourseEnrollmentsList.as_view(),
        name='courseenrollment-detail'
    ),
)

