import json

from .oauth import OAuth2Test


class MicrosoftOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.microsoft.MicrosoftOAuth2'
    user_data_url = 'https://graph.microsoft.com/v1.0/me'
    expected_username = 'foobar'
    user_data_body = json.dumps({
        'displayName': 'foo bar',
        'givenName': 'foobar',
        'jobTitle': 'Auditor',
        'mail': 'foobar@foobar.com',
        'mobilePhone': None,
        'officeLocation': '12/1110',
        'preferredLanguage': 'en-US',
        'surname': 'Bowen',
        'userPrincipalName': 'foobar',
        'id': '48d31887-5fad-4d73-a9f5-3c356e68a038'
    })
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer',
        'id_token': '',
        'expires_in': 3600,
        'expires_on': 1423650396,
        'not_before': 1423646496
    })
    refresh_token_body = json.dumps({
        'access_token': 'foobar-new-token',
        'token_type': 'bearer',
        'expires_in': 3600,
        'refresh_token': 'foobar-new-refresh-token',
        'scope': 'identity'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

    def test_refresh_token(self):
        user, social = self.do_refresh_token()
        self.assertEqual(social.extra_data['access_token'], 'foobar-new-token')
