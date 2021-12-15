"""
URLs file for the Entitlements API.
"""

from django.conf.urls import include
from django.urls import path

app_name = 'entitlements'
urlpatterns = [
    path('v1/', include('common.djangoapps.entitlements.rest_api.v1.urls')),
]
