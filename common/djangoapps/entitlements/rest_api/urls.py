"""
URLs file for the Entitlements API.
"""

from django.conf.urls import include, url

app_name = 'entitlements'
urlpatterns = [
    url(r'^v1/', include('entitlements.rest_api.v1.urls')),
]
