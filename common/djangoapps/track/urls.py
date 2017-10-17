"""
URLs for track app
"""

from django.conf import settings
from django.conf.urls import url

from track.views import segmentio, view_tracking_log, user_track

urlpatterns = [
    url(r'^event$', user_track),
    url(r'^segmentio/event$', segmentio.segmentio_event),
]

if settings.FEATURES.get('ENABLE_SQL_TRACKING_LOGS'):
    urlpatterns += [
        url(r'^event_logs$', view_tracking_log),
        url(r'^event_logs/(?P<args>.+)$', view_tracking_log),
    ]
