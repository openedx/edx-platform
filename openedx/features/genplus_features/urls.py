"""
URLs for genplus features.
"""
from django.conf.urls import url, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

genplus_url_patterns = [
    url(r'^genplus/', include('openedx.features.genplus_features.genplus.urls')),
    url(r'^genplus/learning/', include('openedx.features.genplus_features.genplus_learning.urls')),
    url(r'^genplus/teach/', include('openedx.features.genplus_features.genplus_teach.urls')),
]

schema_view = get_schema_view(
    openapi.Info(
        title="GenZ API",
        default_version="v1",
        description="GenZ API documentation",
    ),
    patterns=genplus_url_patterns,
    public=True,
)

genplus_url_patterns += [
    url(r'^genplus/swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
