"""
URL definitions for v1 Nexblocks API endpoints.
"""

from django.conf.urls import url
from .views import NexBlockInstanceDataView

urlpatterns = [
    url(r'^instance-data/$', NexBlockInstanceDataView.as_view(), name='instance_data')
]
