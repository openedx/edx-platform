"""
Authn API urls
"""

from django.conf.urls import url

from openedx.core.djangoapps.user_authn.api.views import MFEContextView

urlpatterns = [
    url(r'^third_party_auth_context$', MFEContextView.as_view(), name='third_party_auth_context'),
    url(r'^mfe_context$', MFEContextView.as_view(), name='mfe_context'),
]
