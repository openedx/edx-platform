"""
URLs for genplus learning app.
"""
from django.conf.urls import url, include


app_name = 'genplus_learning'

urlpatterns = (
    url(
        r'^api/v1/',
        include(
            'openedx.features.genplus_features.genplus_learning.api.v1.urls',
            namespace='genplus_learning_api_v1'
        )
    ),
)
