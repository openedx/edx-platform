"""URLs for API access management."""

from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from openedx.core.djangoapps.api_admin.decorators import api_access_enabled_or_404
from openedx.core.djangoapps.api_admin.views import ApiRequestView, ApiRequestStatusView, ApiTosView

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
        r'^$',
        api_access_enabled_or_404(login_required(ApiRequestView.as_view())),
        name="api-request"
    ),
)
