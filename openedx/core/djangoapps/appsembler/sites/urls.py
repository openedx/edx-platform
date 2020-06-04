from django.conf import settings
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from openedx.core.djangoapps.appsembler.sites.api import (
    CustomDomainView,
    DomainAvailabilityView,
    DomainSwitchView,
    FindUsernameByEmailView,
    HostFilesView,
    FileUploadView,
    SiteConfigurationViewSet,
    SiteCreateView,
    SiteViewSet,
    UsernameAvailabilityView,
)

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'site-configurations', SiteConfigurationViewSet)
router.register(r'sites', SiteViewSet)

# The API URLs are now determined automatically by the router.
# Additionally, we include the login URLs for the browsable API.
urlpatterns = [
    url(r'^upload_file/', FileUploadView.as_view()),
    url(r'^username/{}/'.format(settings.USERNAME_PATTERN), UsernameAvailabilityView.as_view()),
    url(r'^find_username_by_email/', FindUsernameByEmailView.as_view(), name='tahoe_find_username_by_email'),
    url(r'^domain/(?P<subdomain>[\w.@+-]+)/', DomainAvailabilityView.as_view()),
    url(r'^custom_domain/', CustomDomainView.as_view()),
    url(r'^domain_switch/', DomainSwitchView.as_view()),
    url(r'^register/', SiteCreateView.as_view(), name='tahoe_site_creation'),
    url(r'^', include(router.urls)),
]

if settings.APPSEMBLER_FEATURES.get('ENABLE_FILE_HOST_API', True):
    urlpatterns += [
        url(r'^host_files', HostFilesView.as_view()),
    ]
