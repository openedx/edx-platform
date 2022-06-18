import json

from .oauth import OAuth2Test
from .test_open_id_connect import OpenIdConnectTestMixin


class FenceOpenIdConnectTest(OpenIdConnectTestMixin, OAuth2Test):
    backend_path = \
        'social_core.backends.fence.Fence'
    issuer = 'https://nci-crdc.datacommons.io/'
    openid_config_body = json.dumps({
        'issuer': 'https://nci-crdc.datacommons.io/',
        'authorization_endpoint': 'https://nci-crdc.datacommons.io/user/oauth2/authorize',
        'userinfo_endpoint': 'https://nci-crdc.datacommons.io/user/user/',
        'token_endpoint': 'https://nci-crdc.datacommons.io/user/oauth2/token',
        'revocation_endpoint': 'https://nci-crdc.datacommons.io/user/oauth2/revoke',
        'jwks_uri': 'https://auth.globus.org/jwk.json',
        'response_types_supported': [
            'code',
            'token',
            'token id_token',
            'id_token'
        ],
        'id_token_signing_alg_values_supported': [
            'RS512'
        ],
        'scopes_supported': [
            'ga4gh_passport_v1',
            'openid',
            'google_credentials',
            'google_service_account',
            'data',
            'user',
            'google_link',
            'admin',
            'fence'
        ],
        'token_endpoint_auth_methods_supported': [
            'authorization_code',
            'implicit'
        ],
        'claims_supported': [
            'aud',
            'sub',
            'iss',
            'exp',
            'jti',
            'auth_time',
            'azp',
            'nonce',
            'context'
        ],
        'subject_types_supported': ['public']
    })
