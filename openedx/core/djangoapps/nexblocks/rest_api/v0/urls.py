"""
URL definitions for v1 Nexblocks API endpoints.
"""

from django.conf.urls import url
from django.conf import settings

from .views import NexBlockInstanceDataView

urlpatterns = [
    url(
        r'^instance-data/{}$'.format(settings.USAGE_ID_PATTERN),
        NexBlockInstanceDataView.as_view(),
        name='instance_data',
    )
]
