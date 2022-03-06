"""
URL Routes for this app.
"""
from django.urls import path
from .views import DemographicsStatusView


urlpatterns = [
    path('demographics/status/', DemographicsStatusView.as_view(),
         name='demographics_status'
         ),
]
