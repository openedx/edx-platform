"""Url configuration for the auth module."""

from django.conf.urls import include, patterns, url

from .views import inactive_user_view, saml_metadata_view, post_to_custom_auth_form

urlpatterns = patterns(
    '',
    url(r'^auth/inactive', inactive_user_view),
    url(r'^auth/custom_auth_entry', post_to_custom_auth_form, name='tpa_post_to_custom_auth_form'),
    url(r'^auth/saml/metadata.xml', saml_metadata_view),
    url(r'^auth/', include('social.apps.django_app.urls', namespace='social')),
)
