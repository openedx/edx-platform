"""
Authn API urls
"""

from django.conf.urls import url

from openedx.core.djangoapps.user_authn.api.views import MFEContextView, SendAccountActivationEmail
from openedx.core.djangoapps.user_authn.api.optional_fields import OptionalFieldsView

urlpatterns = [
    url(r'^third_party_auth_context$', MFEContextView.as_view(), name='third_party_auth_context'),
    url(r'^mfe_context$', MFEContextView.as_view(), name='mfe_context'),
    url(
        r'^send_account_activation_email$',
        SendAccountActivationEmail.as_view(),
        name='send_account_activation_email'
    ),
    url(r'^optional_fields$', OptionalFieldsView.as_view(), name='optional_fields'),
]
