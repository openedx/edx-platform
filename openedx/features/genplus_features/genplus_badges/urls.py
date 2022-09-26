"""
URLs for genplus badges app.
"""
from django.conf.urls import url, include


app_name = 'genplus_badges'

urlpatterns = (
    url(
        r'^api/v1/',
        include(
            'openedx.features.genplus_features.genplus_badges.api.v1.urls',
            namespace='genplus_badges_api_v1'
        )
    ),
)
