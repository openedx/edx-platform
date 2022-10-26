"""
URLs for genplus features.
"""
from django.conf.urls import url, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from openedx.features.genplus_features.genplus import views as genplus_views

genplus_url_patterns = [
    url(r'^auth/?$', genplus_views.authenticate_user, name='genplus-auth'),
    url(r'^genplus/', include('openedx.features.genplus_features.genplus.urls')),
    url(r'^genplus/learning/', include('openedx.features.genplus_features.genplus_learning.urls')),
    url(r'^genplus/teach/', include('openedx.features.genplus_features.genplus_teach.urls')),
    url(r'^genplus/badges/', include('openedx.features.genplus_features.genplus_badges.urls')),
    url(r'^genplus/assessment/', include('openedx.features.genplus_features.genplus_assessments.urls')),
]

schema_view = get_schema_view(
    openapi.Info(
        title="GenZ API",
        default_version="v1",
        description="GenZ custom features API documentation",
    ),
    patterns=genplus_url_patterns,
    public=True,
    permission_classes=[permissions.AllowAny]
)

genplus_url_patterns += [
    url(r'^genplus/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^genplus/swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
