"""
Learner's Dashboard urls
"""

from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns(
    '',
    url(r'^programs', views.view_programs, name="program_listing_view")
)
