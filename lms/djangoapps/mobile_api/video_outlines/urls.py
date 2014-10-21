"""
URLs for video outline API
"""
from django.conf.urls import patterns, url
from django.conf import settings

from .views import VideoSummaryList, VideoTranscripts, MissingVideoList

urlpatterns = patterns(
    'mobile_api.video_outlines.views',
    url(
        r'^courses/{}$'.format(settings.COURSE_ID_PATTERN),
        VideoSummaryList.as_view(),
        name='video-summary-list'
    ),
    url(
        r'^courses/{}/missing$'.format(settings.COURSE_ID_PATTERN),
        MissingVideoList.as_view(),
        name='missing-video-list'
    ),

    url(
        r'^transcripts/{}/(?P<block_id>[^/]*)/(?P<lang>[^/]*)$'.format(settings.COURSE_ID_PATTERN),
        VideoTranscripts.as_view(),
        name='video-transcripts-detail'
    ),
)
