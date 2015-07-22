"""Defines the URL routes for this app."""

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from .views import HomePageView

urlpatterns = patterns(
    'onboarding.views',
    url(r'^home', HomePageView.as_view(), name='home_page'),
)
