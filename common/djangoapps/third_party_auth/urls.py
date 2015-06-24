"""Url configuration for the auth module."""

from django.conf.urls import include, patterns, url

from .views import inactive_user_view

urlpatterns = patterns(
    '',
    url(r'^auth/inactive', inactive_user_view),
    url(r'^auth/', include('social.apps.django_app.urls', namespace='social')),
)
