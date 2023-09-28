"""
Demographics API URLs.
"""
from django.urls import path, include

from .v1 import urls as v1_urls

app_name = 'openedx.core.djangoapps.demographics'

urlpatterns = [
    path('v1/', include(v1_urls))
]
