"""
URL definitions for api access request API v1.
"""
from django.conf.urls import patterns, url

from openedx.core.djangoapps.api_admin.api.v1 import views

urlpatterns = patterns(
    '',
    url(r'^api_access_request/$', views.ApiAccessRequestView.as_view(), name='list_api_access_request'),
)
