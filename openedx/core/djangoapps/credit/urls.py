"""
URLs for the credit app.
"""
from django.conf.urls import patterns, url, include

from openedx.core.djangoapps.credit import views, routers, models

PROVIDER_ID_PATTERN = r'(?P<provider_id>{})'.format(models.CREDIT_PROVIDER_ID_REGEX)

PROVIDER_URLS = patterns(
    '',
    url(r'^request/$', views.CreditProviderRequestCreateView.as_view(), name='create_request'),
    url(r'^callback/?$', views.CreditProviderCallbackView.as_view(), name='provider_callback'),
)

V1_URLS = patterns(
    '',
    url(r'^providers/{}/'.format(PROVIDER_ID_PATTERN), include(PROVIDER_URLS)),
    url(r'^eligibility/$', views.CreditEligibilityView.as_view(), name='eligibility_details'),
)

router = routers.SimpleRouter()  # pylint: disable=invalid-name
router.register(r'courses', views.CreditCourseViewSet)
router.register(r'providers', views.CreditProviderViewSet)
V1_URLS += router.urls

urlpatterns = patterns(
    '',
    url(r'^v1/', include(V1_URLS)),
)
