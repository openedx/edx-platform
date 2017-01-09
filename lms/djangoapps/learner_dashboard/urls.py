"""Learner dashboard URL routing configuration"""
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^programs/$', views.program_listing, name='program_listing_view'),
    url(r'^programs/(?P<program_uuid>[0-9a-f]{32})/$', views.program_details, name='program_details_view'),
]
