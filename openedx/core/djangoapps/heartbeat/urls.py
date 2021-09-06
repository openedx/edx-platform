"""
Urls for verifying health (heartbeat) of the app.
"""


from django.conf.urls import url

from openedx.core.djangoapps.heartbeat.views import heartbeat

urlpatterns = [
    url(r'^$', heartbeat, name='heartbeat'),
]
