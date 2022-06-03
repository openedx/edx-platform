"""
URLs for genplus teach app.
"""
from django.conf.urls import url, include


app_name = 'genplus_teach'

urlpatterns = (
    url(
        r'^api/v1/',
        include(
            'openedx.features.genplus_features.genplus_teach.api.v1.urls',
            namespace='genplus_teach_api_v1'
        )
    ),
)
