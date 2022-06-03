"""
URLs for genplus core app.
"""
from django.conf.urls import url, include


app_name = 'genplus'

urlpatterns = (
    url(
        r'^api/v1/',
        include('openedx.features.genplus_features.genplus.api.v1.urls', namespace='genplus_api_v1')
    ),
)
