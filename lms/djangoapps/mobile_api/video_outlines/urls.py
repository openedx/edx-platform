"""
URLs for video outline API
"""

from django.conf import settings
from django.conf.urls import url

from .views import VideoSummaryList, VideoTranscripts

urlpatterns = [
    url(
        r'^courses/{}$'.format(settings.COURSE_ID_PATTERN),
        VideoSummaryList.as_view(),
        name='video-summary-list'
    ),
    url(
        r'^transcripts/{}/(?P<block_id>[^/]*)/(?P<lang>[^/]*)$'.format(settings.COURSE_ID_PATTERN),
        VideoTranscripts.as_view(),
        name='video-transcripts-detail'
    ),
]
