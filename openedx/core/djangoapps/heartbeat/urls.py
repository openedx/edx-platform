"""
Urls for verifying health (heartbeat) of the app.
"""
from __future__ import absolute_import

from django.conf.urls import url

from openedx.core.djangoapps.heartbeat.views import heartbeat

urlpatterns = [
    url(r'^$', heartbeat, name='heartbeat'),
]
