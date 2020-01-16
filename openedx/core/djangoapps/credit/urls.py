"""
URLs for the credit app.
"""


from django.conf.urls import include, url

from openedx.core.djangoapps.credit import models, routers, views

PROVIDER_ID_PATTERN = r'(?P<provider_id>{})'.format(models.CREDIT_PROVIDER_ID_REGEX)

PROVIDER_URLS = [
    url(r'^request/$', views.CreditProviderRequestCreateView.as_view(), name='create_request'),
    url(r'^callback/?$', views.CreditProviderCallbackView.as_view(), name='provider_callback'),
]

V1_URLS = [
    url(r'^providers/{}/'.format(PROVIDER_ID_PATTERN), include(PROVIDER_URLS)),
    url(r'^eligibility/$', views.CreditEligibilityView.as_view(), name='eligibility_details'),
]

router = routers.SimpleRouter()  # pylint: disable=invalid-name
router.register(r'courses', views.CreditCourseViewSet)
router.register(r'providers', views.CreditProviderViewSet)
V1_URLS += router.urls

app_name = 'credit'
urlpatterns = [
    url(r'^v1/', include(V1_URLS)),
]
