"""
Authn API urls
"""

from django.conf.urls import url

from openedx.core.djangoapps.user_authn.api.views import MFEContextView, SendAccountActivationEmail

urlpatterns = [
    url(r'^third_party_auth_context$', MFEContextView.as_view(), name='third_party_auth_context'),
    url(r'^mfe_context$', MFEContextView.as_view(), name='mfe_context'),
    url(
        r'^send_account_activation_email$',
        SendAccountActivationEmail.as_view(),
        name='send_account_activation_email'
    ),
]
