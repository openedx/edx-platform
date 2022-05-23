"""
Authn API urls
"""
from django.urls import path
from openedx.core.djangoapps.user_authn.api.views import (
    MFEContextView,
    SendAccountActivationEmail,
    OptionalFieldsView,
)
urlpatterns = [
    path('third_party_auth_context', MFEContextView.as_view(), name='third_party_auth_context'),
    path('mfe_context', MFEContextView.as_view(), name='mfe_context'),
    path('send_account_activation_email', SendAccountActivationEmail.as_view(),
         name='send_account_activation_email'
         ),
    path('optional_fields', OptionalFieldsView.as_view(), name='optional_fields'),
]
