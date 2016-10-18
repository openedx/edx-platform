"""
Urls for verifying health (heartbeat) of the app.
"""
from django.conf.urls import url, patterns

urlpatterns = patterns(
    '',

    url(r'^$', 'openedx.core.djangoapps.heartbeat.views.heartbeat', name='heartbeat'),
)
