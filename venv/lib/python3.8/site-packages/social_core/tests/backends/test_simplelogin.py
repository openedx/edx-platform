import json

from .oauth import OAuth2Test


class SimpleLoginOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.simplelogin.SimpleLoginOAuth2'
    user_data_url = 'https://app.simplelogin.io/oauth2/userinfo'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'client': 'Continental',
        'email': 'john@wick.com',
        'email_verified': True,
        'id': 1,
        'name': 'John Wick',
        'avatar_url': 'http://wick.com/john.png'
    })
    expected_username = 'john@wick.com'

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
