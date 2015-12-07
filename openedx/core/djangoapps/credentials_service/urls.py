"""
URLs for the credentials service.
"""
from django.conf.urls import patterns, url, include

urlpatterns = [
    url(r'^v1/',
        include('openedx.core.djangoapps.credentials_service.api.v1.urls', namespace='v1')
    ),
]
