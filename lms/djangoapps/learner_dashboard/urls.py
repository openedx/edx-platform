"""Learner dashboard URL routing configuration"""
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^programs/$', views.view_programs, name='program_listing_view'),
    # Matches paths like 'programs/123/' and 'programs/123/foo/', but not 'programs/123/foo/bar/'.
    url(r'^programs/(?P<program_id>\d+)/[\w\-]*/?$', views.program_details, name='program_details_view'),
]
