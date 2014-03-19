"""Url configuration for the auth module."""

from django.conf.urls import include, patterns, url

# String. Base of URL path component.
_PATH_BASE = 'auth/'

urlpatterns = patterns(
    '', url(r'^' + _PATH_BASE, include('social.apps.django_app.urls', namespace='social')),
)
