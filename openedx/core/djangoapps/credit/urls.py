"""
URLs for the credit app.
"""
from django.conf import settings
from django.conf.urls import patterns, url

from .views import create_credit_request, credit_provider_callback

from openedx.core.djangoapps.credit.tests.fake_update_min_grade import(
    UpdateMinGradeRequirementFakeView
)

urlpatterns = patterns(
    '',

    url(
        r"^v1/provider/(?P<provider_id>[^/]+)/request/$",
        create_credit_request,
        name="create_request"
    ),

    url(
        r"^v1/provider/(?P<provider_id>[^/]+)/callback/?$",
        credit_provider_callback,
        name="provider_callback"
    ),
)

if settings.FEATURES.get('ENABLE_MIN_GRADE_STATUS_UPDATE'):
    urlpatterns += (url(
        r'^check_grade',
        UpdateMinGradeRequirementFakeView.as_view(),
        name='UpdateMinRequirementFakeView'
    ),)
