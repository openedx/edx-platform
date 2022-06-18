import json

from httpretty import HTTPretty

from social_core.tests.backends.oauth import OAuth2Test
from social_core.tests.backends.test_open_id_connect import \
    OpenIdConnectTestMixin

JWK_KEY = {
    'kty': 'RSA',
    'd': 'ZmswNokEvBcxW_Kvcy8mWUQOQCBdGbnM0xR7nhvGHC-Q24z3XAQWlMWbsmGc_R1o'
         '_F3zK7DBlc3BokdRaO1KJirNmnHCw5TlnBlJrXiWpFBtVglUg98-4sRRO0VWnGXK'
         'JPOkBQ6b_DYRO3b0o8CSpWowpiV6HB71cjXTqKPZf-aXU9WjCCAtxVjfIxgQFu5I'
         '-G1Qah8mZeY8HK_y99L4f0siZcbUoaIcfeWBhxi14ODyuSAHt0sNEkhiIVBZE7QZ'
         'm-SEP1ryT9VAaljbwHHPmg7NC26vtLZhvaBGbTTJnEH0ZubbN2PMzsfeNyoCIHy4'
         '4QDSpQDCHfgcGOlHY_t5gQ',
    'e': 'AQAB',
    'use': 'sig',
    'kid': 'testkey',
    'alg': 'RS256',
    'n': 'pUfcJ8WFrVue98Ygzb6KEQXHBzi8HavCu8VENB2As943--bHPcQ-nScXnrRFAUg8'
         'H5ZltuOcHWvsGw_AQifSLmOCSWJAPkdNb0w0QzY7Re8NrPjCsP58Tytp5LicF0Ao'
         'Ag28UK3JioY9hXHGvdZsWR1Rp3I-Z3nRBP6HyO18pEgcZ91c9aAzsqu80An9X4DA'
         'b1lExtZorvcd5yTBzZgr-MUeytVRni2lDNEpa6OFuopHXmg27Hn3oWAaQlbymd4g'
         'ifc01oahcwl3ze2tMK6gJxa_TdCf1y99Yq6oilmVvZJ8kwWWnbPE-oDmOVPVnEyT'
         'vYVCvN4rBT1DQ-x0F1mo2Q',
}

JWK_PUBLIC_KEY = {key: value for key, value in JWK_KEY.items() if key != 'd'}


class OktaOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.okta.OktaOAuth2'
    user_data_url = 'https://dev-000000.oktapreview.com/oauth2/v1/userinfo'
    expected_username = 'foo'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'family_name': 'Bar',
        'sub': '101010101010101010101',
        'locale': 'en',
        'email_verified': True,
        'given_name': 'Foo',
        'email': 'foo@bar.com',
        'name': 'Foo Bar',
        'nickname': 'foobar',
        'middle_name': '',
        'profile': 'https://example.com/foo.bar',
        'zoneinfo': 'America/Los_Angeles',
        'updated_at': 1311280970,
        'preferred_username': 'foo',
    })

    def test_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_OKTA_OAUTH2_API_URL': 'https://dev-000000.oktapreview.com/oauth2'
        })
        self.do_login()

    def test_partial_pipeline(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_OKTA_OAUTH2_API_URL': 'https://dev-000000.oktapreview.com/oauth2'
        })
        self.do_partial_pipeline()


class OktaOpenIdConnectTest(OpenIdConnectTestMixin, OAuth2Test):
    backend_path = \
        'social_core.backends.okta_openidconnect.OktaOpenIdConnect'
    user_data_url = \
        'https://dev-000000.oktapreview.com/oauth2/v1/userinfo'
    issuer = 'https://dev-000000.oktapreview.com/oauth2'
    openid_config_body = json.dumps({
        'issuer': 'https://dev-000000.oktapreview.com/oauth2',
        'authorization_endpoint': 'https://dev-000000.oktapreview.com/oauth2/v1/authorize',
        'token_endpoint': 'https://dev-000000.oktapreview.com/oauth2/v1/token',
        'userinfo_endpoint': 'https://dev-000000.oktapreview.com/oauth2/v1/userinfo',
        'jwks_uri': 'https://dev-000000.oktapreview.com/oauth2/v1/keys',
        'response_types_supported': [
            'code',
            'token',
            'id_token',
            'code token',
            'code id_token',
            'token id_token',
            'code token id_token',
            'none',
        ],
        'subject_types_supported': [
            'public',
        ],
        'id_token_signing_alg_values_supported': [
            'RS256',
        ],
        'scopes_supported': [
            'openid',
            'email',
            'profile',
        ],
        'token_endpoint_auth_methods_supported': [
            'client_secret_post',
            'client_secret_basic',
        ],
        'claims_supported': [
            'aud',
            'email',
            'email_verified',
            'exp',
            'family_name',
            'given_name',
            'iat',
            'iss',
            'locale',
            'name',
            'picture',
            'sub',
        ],
    })
    expected_username = 'foo'

    def setUp(self):
        super(OpenIdConnectTestMixin, self).setUp()
        # Settings for Okta
        self.strategy.set_settings({
            'SOCIAL_AUTH_OKTA_OPENIDCONNECT_API_URL': 'https://dev-000000.oktapreview.com/oauth2'
        })
        self.backend.OIDC_ENDPOINT = 'https://dev-000000.oktapreview.com/oauth2'

        self.key = JWK_KEY.copy()
        self.public_key = JWK_PUBLIC_KEY.copy()

        HTTPretty.register_uri(HTTPretty.GET,
                               self.backend.OIDC_ENDPOINT + '/.well-known/openid-configuration',
                               status=200,
                               body=self.openid_config_body)
        oidc_config = json.loads(self.openid_config_body)

        def jwks(_request, _uri, headers):
            return 200, headers, json.dumps({'keys': [self.key]})

        HTTPretty.register_uri(HTTPretty.GET,
                               oidc_config.get('jwks_uri'),
                               status=200,
                               body=json.dumps({'keys': [self.public_key]}))

        self.backend.JWKS_URI = oidc_config.get('jwks_uri')
        self.backend.ID_TOKEN_ISSUER = oidc_config.get('issuer')
