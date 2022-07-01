"""
Demographics API URLs.
"""
from django.conf.urls import include, url

from .v1 import urls as v1_urls

app_name = 'openedx.core.djangoapps.demographics'

urlpatterns = [
    url(r'^v1/', include(v1_urls))
]
