"""
Okta OAuth2 and OpenIdConnect:
    https://python-social-auth.readthedocs.io/en/latest/backends/okta.html
"""
from .okta import OktaOAuth2
from .open_id_connect import OpenIdConnectAuth


class OktaOpenIdConnect(OktaOAuth2, OpenIdConnectAuth):
    """Okta OpenID-Connect authentication backend"""
    name = 'okta-openidconnect'
    REDIRECT_STATE = False
    ACCESS_TOKEN_METHOD = 'POST'
    RESPONSE_TYPE = 'code'
