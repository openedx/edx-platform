import base64
import datetime
import json
import os
import sys
from calendar import timegm
from unittest import mock
from urllib.parse import urlparse

from httpretty import HTTPretty
from jose import jwt

from social_core.backends.open_id_connect import OpenIdConnectAuth

from ...exceptions import AuthTokenError
from ...utils import parse_qs
from .oauth import OAuth2Test

sys.path.insert(0, '..')


TEST_ROOT = os.path.dirname(os.path.dirname(__file__))

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


class OpenIdConnectTestMixin:
    """
    Mixin to test OpenID Connect consumers. Inheriting classes should also
    inherit OAuth2Test.
    """
    client_key = 'a-key'
    client_secret = 'a-secret-key'
    issuer = None  # id_token issuer
    openid_config_body = None
    key = None
    access_token_kwargs = {}

    def setUp(self):
        super().setUp()
        self.key = JWK_KEY.copy()
        self.public_key = JWK_PUBLIC_KEY.copy()

        HTTPretty.register_uri(HTTPretty.GET,
                               self.backend.OIDC_ENDPOINT + '/.well-known/openid-configuration',
                               status=200,
                               body=self.openid_config_body
                               )
        oidc_config = json.loads(self.openid_config_body)

        def jwks(_request, _uri, headers):
            return 200, headers, json.dumps({'keys': [self.key]})

        HTTPretty.register_uri(HTTPretty.GET,
                               oidc_config.get('jwks_uri'),
                               status=200,
                               body=json.dumps({'keys': [self.public_key]}))

    def extra_settings(self):
        settings = super().extra_settings()
        settings.update({
            f'SOCIAL_AUTH_{self.name}_KEY': self.client_key,
            f'SOCIAL_AUTH_{self.name}_SECRET': self.client_secret,
            f'SOCIAL_AUTH_{self.name}_ID_TOKEN_DECRYPTION_KEY':
                self.client_secret
        })
        return settings

    def get_id_token(self, client_key=None, expiration_datetime=None,
                     issue_datetime=None, nonce=None, issuer=None):
        """
        Return the id_token to be added to the access token body.
        """
        return {
            'iss': issuer,
            'nonce': nonce,
            'aud': client_key,
            'azp': client_key,
            'exp': expiration_datetime,
            'iat': issue_datetime,
            'sub': '1234'
        }

    def prepare_access_token_body(self, client_key=None, tamper_message=False,
                                  expiration_datetime=None, kid=None,
                                  issue_datetime=None, nonce=None,
                                  issuer=None):
        """
        Prepares a provider access token response. Arguments:

        client_id       -- (str) OAuth ID for the client that requested
                                 authentication.
        expiration_time -- (datetime) Date and time after which the response
                                      should be considered invalid.
        """

        body = {'access_token': 'foobar', 'token_type': 'bearer'}
        client_key = client_key or self.client_key
        now = datetime.datetime.utcnow()
        expiration_datetime = expiration_datetime or \
            (now + datetime.timedelta(seconds=30))
        issue_datetime = issue_datetime or now
        nonce = nonce or 'a-nonce'
        issuer = issuer or self.issuer
        id_token = self.get_id_token(
            client_key,
            timegm(expiration_datetime.utctimetuple()),
            timegm(issue_datetime.utctimetuple()),
            nonce,
            issuer
        )

        body['id_token'] = jwt.encode(
            claims=id_token,
            key=dict(self.key,
                     iat=timegm(issue_datetime.utctimetuple()),
                     nonce=nonce),
            algorithm='RS256',
            access_token='foobar',
            headers=dict(kid=kid),
        )

        if tamper_message:
            header, msg, sig = body['id_token'].split('.')
            id_token['sub'] = '1235'
            msg = base64.encodebytes(json.dumps(id_token).encode()).decode()
            body['id_token'] = '.'.join([header, msg, sig])

        return json.dumps(body)

    def authtoken_raised(self, expected_message, **access_token_kwargs):
        self.access_token_kwargs = access_token_kwargs
        with self.assertRaisesRegex(AuthTokenError, expected_message):
            self.do_login()

    def pre_complete_callback(self, start_url):
        nonce = parse_qs(urlparse(start_url).query)['nonce']

        self.access_token_kwargs.setdefault('nonce', nonce)
        self.access_token_body = self.prepare_access_token_body(
            **self.access_token_kwargs
        )
        super().pre_complete_callback(start_url)


    def test_invalid_signature(self):
        self.authtoken_raised(
            'Token error: Signature verification failed',
            tamper_message=True
        )

    def test_expired_signature(self):
        expiration_datetime = datetime.datetime.utcnow() - \
            datetime.timedelta(seconds=30)
        self.authtoken_raised('Token error: Signature has expired',
                              expiration_datetime=expiration_datetime)

    def test_invalid_issuer(self):
        self.authtoken_raised('Token error: Invalid issuer',
                              issuer='someone-else')

    def test_invalid_audience(self):
        self.authtoken_raised('Token error: Invalid audience',
                              client_key='someone-else')

    def test_invalid_issue_time(self):
        expiration_datetime = datetime.datetime.utcnow() - \
            datetime.timedelta(hours=1)
        self.authtoken_raised('Token error: Incorrect id_token: iat',
                              issue_datetime=expiration_datetime)

    def test_invalid_nonce(self):
        self.authtoken_raised(
            'Token error: Incorrect id_token: nonce',
            nonce='something-wrong',
            kid='testkey',
        )

    def test_invalid_kid(self):
        self.authtoken_raised('Token error: Signature verification failed', kid='doesnotexist')


class ExampleOpenIdConnectAuth(OpenIdConnectAuth):
    name = 'example123'
    OIDC_ENDPOINT = 'https://example.com/oidc'


class OpenIdConnectTest(OpenIdConnectTestMixin, OAuth2Test):
    backend_path = \
        'social_core.tests.backends.test_open_id_connect.ExampleOpenIdConnectAuth'
    issuer = 'https://example.com'
    openid_config_body = json.dumps({
        'issuer': 'https://example.com',
        'authorization_endpoint': 'https://example.com/oidc/auth',
        'token_endpoint': 'https://example.com/oidc/token',
        'userinfo_endpoint': 'https://example.com/oidc/userinfo',
        'revocation_endpoint': 'https://example.com/oidc/revoke',
        'jwks_uri': 'https://example.com/oidc/certs',
    })

    expected_username = 'cartman'

    def pre_complete_callback(self, start_url):
        super().pre_complete_callback(start_url)
        HTTPretty.register_uri('GET',
                               uri=self.backend.userinfo_url(),
                               status=200,
                               body=json.dumps({'preferred_username': self.expected_username}),
                               content_type='text/json')

    def test_everything_works(self):
        self.do_login()
