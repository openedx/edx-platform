"""
URLs for the credentials support in LMS and Studio.
"""
from django.conf.urls import url, include


urlpatterns = [
    url(r'^v1/', include('openedx.core.djangoapps.credentials.api.urls')),
]
