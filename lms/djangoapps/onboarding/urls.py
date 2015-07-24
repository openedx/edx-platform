"""Defines the URL routes for this app."""

from django.conf import settings
from django.conf.urls import patterns, url

from .views import (
    HomePageView, LoginView, RegisterView, CourseDiscoveryView, CourseAboutView,
)

urlpatterns = patterns(
    'onboarding.views',
    url(r'^home$', HomePageView.as_view(), name='home_page'),
    url(r'^course_discovery$', CourseDiscoveryView.as_view(), name='course_discovery_page'),
    url(r'^course/(?P<org_string>[^/]*)/(?P<course_string>[^/]*)/(?P<run_string>[^/]*)', CourseAboutView.as_view(), name='course_about_page'),
)
