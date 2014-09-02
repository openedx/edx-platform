"""
A block basically corresponds to a usage ID in our system.

"""
from django.conf.urls import patterns, url, include
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns
from django.conf import settings

from .views import VideoSummaryList, VideoTranscripts

urlpatterns = patterns('public_api.video_outlines.views',
#    url(r'^{}'.format(settings.COURSE_ID_PATTERN), VideoSummaryList.as_view(), name='video-summary-list'),

    url(r'^courses/(?P<course_id>[^/]*)$', VideoSummaryList.as_view(), name='video-summary-list'),
    url(
        r'^transcripts/(?P<course_id>[^/]*)/(?P<block_id>[^/]*)/(?P<lang>[^/]*)$',
        VideoTranscripts.as_view(),
        name='video-transcripts-detail'
    ),

#    url(
#        r'^(?P<username>\w+)/course_enrollments/$',
#        UserCourseEnrollmentsList.as_view(),
#        name='courseenrollment-detail'
#    ),
)

