"""URLs for API access management."""


from django.conf.urls import include, url
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required

from openedx.core.djangoapps.api_admin.decorators import api_access_enabled_or_404
from openedx.core.djangoapps.api_admin.views import (
    ApiRequestStatusView,
    ApiRequestView,
    ApiTosView,
    CatalogEditView,
    CatalogListView,
    CatalogPreviewView,
    CatalogSearchView
)

app_name = 'api_admin'
urlpatterns = (
    url(
        r'^status/$',
        api_access_enabled_or_404(login_required(ApiRequestStatusView.as_view())),
        name="api-status"
    ),
    url(
        r'^terms-of-service/$',
        api_access_enabled_or_404(ApiTosView.as_view()),
        name="api-tos"
    ),
    url(
        r'^catalogs/preview/$',
        staff_member_required(
            api_access_enabled_or_404(CatalogPreviewView.as_view()),
            login_url='dashboard',
            redirect_field_name=None
        ),
        name='catalog-preview',
    ),
    url(
        r'^catalogs/user/(?P<username>[\w.@+-]+)/$',
        staff_member_required(
            api_access_enabled_or_404(CatalogListView.as_view()),
            login_url='dashboard',
            redirect_field_name=None
        ),
        name='catalog-list',
    ),
    url(
        r'^catalogs/(?P<catalog_id>\d+)/$',
        staff_member_required(
            api_access_enabled_or_404(CatalogEditView.as_view()),
            login_url='dashboard',
            redirect_field_name=None
        ),
        name='catalog-edit',
    ),
    url(
        r'^catalogs/$',
        staff_member_required(
            api_access_enabled_or_404(CatalogSearchView.as_view()),
            login_url='dashboard',
            redirect_field_name=None
        ),
        name='catalog-search',
    ),
    url(
        r'^$',
        api_access_enabled_or_404(login_required(ApiRequestView.as_view())),
        name="api-request"
    ),
    url(
        r'^api/', include('openedx.core.djangoapps.api_admin.api.urls', namespace='api'),
    ),
)
