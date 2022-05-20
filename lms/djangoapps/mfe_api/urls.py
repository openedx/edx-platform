""" URLs configuration for the mfe api."""

from django.urls import path

from lms.djangoapps.mfe_api.views import MFEConfigView

app_name = 'mfe_api'
urlpatterns = [
    path('v1/config', MFEConfigView.as_view(), name='config'),
]
