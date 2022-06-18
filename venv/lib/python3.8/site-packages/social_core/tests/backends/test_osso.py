import json
from urllib.parse import urlencode

from httpretty import HTTPretty

from social_core.backends.osso import OssoOAuth2

from .oauth import OAuth2Test


class OssoOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.osso.OssoOAuth2'
    user_data_url = 'https://demo.ossoapp.com/oauth/me'
    expected_username = 'user@example.com'
    access_token_body = json.dumps(
        {
            'access_token': '3633395cffe739bb87089235c152155ae73b6794f7af353b2aa189aeeacee1ec',
            'token_type': 'bearer',
            'expires_in': 600
        }
    )
    user_data_body = json.dumps(
        {
            'email': 'user@example.com',
            'id': 'f23611a5-2817-43e2-94b7-99b25235ad2d',
            'idp': 'Okta',
            'requested': {
                'email': None,
                'domain': 'example.com'
            }
        }
    )

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()