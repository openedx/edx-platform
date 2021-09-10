"""
URL definitions for api access request API v1.
"""

from openedx.core.djangoapps.api_admin.api.v1 import views
from django.urls import path

app_name = 'v1'
urlpatterns = [
    path('api_access_request/', views.ApiAccessRequestView.as_view(), name='list_api_access_request'),
]
