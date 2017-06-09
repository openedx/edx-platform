"""Learner dashboard URL routing configuration"""
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^programs/$', views.program_listing, name='program_listing_view'),
    # Matches paths like 'programs/123/' and 'programs/123/foo/', but not 'programs/123/foo/bar/'.
    # Also accepts strings that look like UUIDs, to support retrieval of catalog-based MicroMasters.
    url(r'^programs/(?P<program_id>[0-9a-f-]+)/[\w\-]*/?$', views.program_details, name='program_details_view'),
]
