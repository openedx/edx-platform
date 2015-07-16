"""
URLs for the credit app.
"""
from django.conf.urls import patterns, url

from .api.provider import get_credit_provider_info
from .views import create_credit_request, credit_provider_callback, get_providers_detail, get_eligibility_for_user

PROVIDER_ID_PATTERN = r'(?P<provider_id>[^/]+)'

urlpatterns = patterns(
    '',

    url(
        r"^v1/providers/(?P<provider_id>[^/]+)/$",
        get_credit_provider_info,
        name="get_provider_info"
    ),
    url(
        r"^v1/providers/$",
        get_providers_detail,
        name="providers_detail"
    ),

    url(
        r"^v1/providers/{provider_id}/request/$".format(provider_id=PROVIDER_ID_PATTERN),
        create_credit_request,
        name="create_request"
    ),

    url(
        r"^v1/providers/{provider_id}/callback/?$".format(provider_id=PROVIDER_ID_PATTERN),
        credit_provider_callback,
        name="provider_callback"
    ),

    url(
        r"^v1/eligibility/$",
        get_eligibility_for_user,
        name="eligibility_details"
    ),

)
