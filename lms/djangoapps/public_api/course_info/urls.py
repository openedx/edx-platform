"""
A block basically corresponds to a usage ID in our system.

"""
from django.conf.urls import patterns, url, include
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from .views import CourseAboutDetail, CourseUpdatesList, CourseHandoutsList

urlpatterns = patterns('public_api.course_info.views',
    url(r'^(?P<course_id>[^/]*)/about$', CourseAboutDetail.as_view(), name='course-about-detail'),
    url(r'^(?P<course_id>[^/]*)/handouts$', CourseHandoutsList.as_view(), name='course-handouts-list'),
    url(r'^(?P<course_id>[^/]*)/updates$', CourseUpdatesList.as_view(), name='course-updates-list'),

#    url(
#        r'^(?P<username>\w+)/course_enrollments/$',
#        UserCourseEnrollmentsList.as_view(),
#        name='courseenrollment-detail'
#    ),
)

