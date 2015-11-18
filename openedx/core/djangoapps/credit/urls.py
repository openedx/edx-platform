"""
URLs for the credit app.
"""
from django.conf.urls import patterns, url, include

from openedx.core.djangoapps.credit import views, routers
from openedx.core.djangoapps.credit.api.provider import get_credit_provider_info

PROVIDER_ID_PATTERN = r'(?P<provider_id>[^/]+)'

V1_URLS = patterns(
    '',

    url(
        r'^providers/$',
        views.get_providers_detail,
        name='providers_detail'
    ),

    url(
        r'^providers/{provider_id}/$'.format(provider_id=PROVIDER_ID_PATTERN),
        get_credit_provider_info,
        name='get_provider_info'
    ),

    url(
        r'^providers/{provider_id}/request/$'.format(provider_id=PROVIDER_ID_PATTERN),
        views.create_credit_request,
        name='create_request'
    ),

    url(
        r'^providers/{provider_id}/callback/?$'.format(provider_id=PROVIDER_ID_PATTERN),
        views.credit_provider_callback,
        name='provider_callback'
    ),

    url(
        r'^eligibility/$',
        views.get_eligibility_for_user,
        name='eligibility_details'
    ),
)

router = routers.SimpleRouter()  # pylint: disable=invalid-name
router.register(r'courses', views.CreditCourseViewSet)
V1_URLS += router.urls

urlpatterns = patterns(
    '',
    url(r'^v1/', include(V1_URLS)),
)
