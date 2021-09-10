"""
URL Routes for this app.
"""
from .views import DemographicsStatusView
from django.urls import path


urlpatterns = [
    path('demographics/status/', DemographicsStatusView.as_view(),
        name='demographics_status'
    ),
]
