"""
Demographics API URLs.
"""
from django.conf.urls import include

from .v1 import urls as v1_urls
from django.urls import path

app_name = 'openedx.core.djangoapps.demographics'

urlpatterns = [
    path('v1/', include(v1_urls))
]
