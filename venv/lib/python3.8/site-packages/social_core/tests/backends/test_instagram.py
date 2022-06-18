import json

from .oauth import OAuth2Test


class InstagramOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.instagram.InstagramOAuth2'
    user_data_url = 'https://graph.instagram.com/me'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer',
        'meta': {
            'code': 200
        },
        'user': {
            'username': 'foobar',
            'id': '101010101'
        }
    })
    user_data_body = json.dumps({
        'meta': {
            'code': 200
        },
        'username': 'foobar',
        'id': '101010101'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
