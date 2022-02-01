"""Url configuration for the auth module."""

from django.conf.urls import include
from django.urls import path, re_path

from .views import (
    IdPRedirectView,
    inactive_user_view,
    lti_login_and_complete_view,
    post_to_custom_auth_form,
    saml_metadata_view
)

urlpatterns = [
    path('auth/inactive', inactive_user_view, name="third_party_inactive_redirect"),
    path('auth/custom_auth_entry', post_to_custom_auth_form, name='tpa_post_to_custom_auth_form'),
    re_path(r'^auth/saml/metadata.xml', saml_metadata_view),
    re_path(r'^auth/login/(?P<backend>lti)/$', lti_login_and_complete_view),
    path('auth/idp_redirect/<slug:provider_slug>', IdPRedirectView.as_view(), name="idp_redirect"),
    path('auth/', include('social_django.urls', namespace='social')),
    path('auth/saml/v0/', include('common.djangoapps.third_party_auth.samlproviderconfig.urls')),
    path('auth/saml/v0/', include('common.djangoapps.third_party_auth.samlproviderdata.urls')),
    path('auth/saml/v0/', include('common.djangoapps.third_party_auth.saml_configuration.urls')),
]
