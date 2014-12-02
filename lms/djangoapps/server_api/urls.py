# pylint: disable=C0103
"""
    The URI scheme for resources is as follows:
        Resource type: /api/{resource_type}
        Specific resource: /api/{resource_type}/{resource_id}

    The remaining URIs provide information about the API and/or module
        System: General context and intended usage
        API: Top-level description of overall API (must live somewhere)
"""
from django.conf.urls import include, patterns, url

from rest_framework.routers import SimpleRouter

from server_api.system import views as system_views

urlpatterns = patterns(
    '',
    url(r'^$', system_views.ApiDetail.as_view()),
    url(r'^system$', system_views.SystemDetail.as_view()),
    url(r'^users/*', include('server_api.users.urls')),
    url(r'^groups/*', include('server_api.groups.urls')),
    url(r'^sessions/*', include('server_api.sessions.urls')),
    url(r'^courses/*', include('server_api.courses.urls')),
)

server_api_router = SimpleRouter()

urlpatterns += server_api_router.urls
