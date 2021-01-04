"""
URLs for track app
"""


from django.conf import settings
from django.conf.urls import url

import track.views
import track.views.segmentio

urlpatterns = [
    url(r'^event$', track.views.user_track),
    url(r'^segmentio/event$', track.views.segmentio.segmentio_event),
]
