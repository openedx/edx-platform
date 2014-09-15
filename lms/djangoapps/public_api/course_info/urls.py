from django.conf.urls import patterns, url, include
from django.conf import settings
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from .views import CourseAboutDetail, CourseUpdatesList, CourseHandoutsList

urlpatterns = patterns(
    'public_api.course_info.views',
    url(
        r'^{}/about$'.format(settings.COURSE_ID_PATTERN),
        CourseAboutDetail.as_view(),
        name='course-about-detail'
    ),
    url(
        r'^{}/handouts$'.format(settings.COURSE_ID_PATTERN),
        CourseHandoutsList.as_view(),
        name='course-handouts-list'
    ),
    url(
        r'^{}/updates$'.format(settings.COURSE_ID_PATTERN),
        CourseUpdatesList.as_view(),
        name='course-updates-list'
    ),
)

