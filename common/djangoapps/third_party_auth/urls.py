"""Url configuration for the auth module."""

from django.conf.urls import include, url

from .views import (
    IdPRedirectView,
    inactive_user_view,
    lti_login_and_complete_view,
    post_to_custom_auth_form,
    saml_metadata_view
)

urlpatterns = [
    url(r'^auth/inactive', inactive_user_view, name="third_party_inactive_redirect"),
    url(r'^auth/custom_auth_entry', post_to_custom_auth_form, name='tpa_post_to_custom_auth_form'),
    url(r'^auth/saml/metadata.xml', saml_metadata_view),
    url(r'^auth/login/(?P<backend>lti)/$', lti_login_and_complete_view),
    url(r'^auth/idp_redirect/(?P<provider_slug>[\w-]+)', IdPRedirectView.as_view(), name="idp_redirect"),
    url(r'^auth/', include('social_django.urls', namespace='social')),
    url(r'^auth/saml/v0/', include('common.djangoapps.third_party_auth.samlproviderconfig.urls')),
    url(r'^auth/saml/v0/', include('common.djangoapps.third_party_auth.samlproviderdata.urls')),
    url(r'^auth/saml/v0/', include('common.djangoapps.third_party_auth.saml_configuration.urls')),
]
