"""
Urls for verifying health (heartbeat) of the app.
"""
from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',

    url(r'^$', 'openedx.core.djangoapps.heartbeat.views.heartbeat', name='heartbeat'),
)
