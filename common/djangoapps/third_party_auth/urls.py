"""Url configuration for the auth module."""

from django.conf.urls import include, patterns, url

from .views import saml_metadata_view

urlpatterns = patterns(
    '',
    url(r'^auth/saml/metadata.xml', saml_metadata_view),
    url(r'^auth/', include('social.apps.django_app.urls', namespace='social')),
)
