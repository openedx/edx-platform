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

from api_manager.organizations.views import OrganizationsViewSet
from api_manager.system import views as system_views
from projects import views as project_views

urlpatterns = patterns(
    '',
    url(r'^$', system_views.ApiDetail.as_view()),
    url(r'^system$', system_views.SystemDetail.as_view()),
    url(r'^users/*', include('api_manager.users.urls')),
    url(r'^groups/*', include('api_manager.groups.urls')),
    url(r'^sessions/*', include('api_manager.sessions.urls')),
    url(r'^courses/*', include('api_manager.courses.urls')),
)

server_api_router = SimpleRouter()
server_api_router.register(r'organizations', OrganizationsViewSet)

# Project-related ViewSets
server_api_router.register(r'projects', project_views.ProjectsViewSet)
server_api_router.register(r'workgroups', project_views.WorkgroupsViewSet)
server_api_router.register(r'submissions', project_views.WorkgroupSubmissionsViewSet)
server_api_router.register(r'workgroup_reviews', project_views.WorkgroupReviewsViewSet)
server_api_router.register(r'submission_reviews', project_views.WorkgroupSubmissionReviewsViewSet)
server_api_router.register(r'peer_reviews', project_views.WorkgroupPeerReviewsViewSet)
server_api_router.register(r'groups', project_views.GroupViewSet)
server_api_router.register(r'users', project_views.UserViewSet)
urlpatterns += server_api_router.urls
