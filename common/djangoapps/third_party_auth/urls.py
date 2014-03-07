"""Url configuration for the auth module."""

from django.conf.urls import include, patterns, url

urlpatterns = patterns(
    '', url(r'^auth/', include('social.apps.django_app.urls', namespace='social')),
)
