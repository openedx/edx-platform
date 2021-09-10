"""
Urls for verifying health (heartbeat) of the app.
"""

from openedx.core.djangoapps.heartbeat.views import heartbeat
from django.urls import path

urlpatterns = [
    path('', heartbeat, name='heartbeat'),
]
