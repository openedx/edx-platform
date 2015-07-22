"""Defines the URL routes for this app."""

from django.conf import settings
from django.conf.urls import patterns, url

from .views import (
    HomePageView, LoginView, RegisterView, CourseDiscoveryView, CourseAboutView,
)

urlpatterns = patterns(
    'onboarding.views',
    url(r'^home$', HomePageView.as_view(), name='home_page'),
    url(r'^login$', LoginView.as_view(), name='login_page'),
    url(r'^register$', RegisterView.as_view(), name='registration_page'),
    url(r'^course_discovery$', CourseDiscoveryView.as_view(), name='course_discovery_page'),
    url(r'^course/{}$'.format(settings.COURSE_KEY_PATTERN), CourseAboutView.as_view(), name='course_about_page'),
)
