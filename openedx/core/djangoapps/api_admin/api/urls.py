"""
URL definitions for api access request API.
"""
from django.conf.urls import include, url

urlpatterns = [
    url(r'^v1/', include('openedx.core.djangoapps.api_admin.api.v1.urls', namespace='v1')),
]
