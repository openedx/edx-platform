"""
URL definitions for v1 Nexblocks API endpoints.
"""

from django.conf import settings
from django.conf.urls import url

from .views import NexBlockInstanceDataView

urlpatterns = [
    url(
        r"^instance-data/{}$".format(settings.USAGE_ID_PATTERN),
        NexBlockInstanceDataView.as_view(),
        name="instance_data",
    )
]
