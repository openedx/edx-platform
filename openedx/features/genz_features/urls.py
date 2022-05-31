"""
URLs for genz app.
"""
from django.conf.urls import url, include


app_name = 'genz_features'

urlpatterns = (
    url(
        r'^api/v1/',
        include('openedx.features.genz_features.api.v1.urls', namespace='genz_api_v1')
    ),
)
