"""
URL Routes for this app.
"""
from django.conf.urls import url
from .views import DemographicsStatusView


urlpatterns = [
    url(
        r'^demographics/status/$',
        DemographicsStatusView.as_view(),
        name='demographics_status'
    ),
]
