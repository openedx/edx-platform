"""
A block basically corresponds to a usage ID in our system.

"""
from django.conf.urls import patterns, url, include
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns
from django.conf import settings

from .views import VideoSummaryList

urlpatterns = patterns('public_api.video_outlines.views',
    url(r'^{}'.format(settings.COURSE_ID_PATTERN), VideoSummaryList.as_view(), name='video-summary-list'),
#    url(
#        r'^(?P<username>\w+)/course_enrollments/$',
#        UserCourseEnrollmentsList.as_view(),
#        name='courseenrollment-detail'
#    ),
)

