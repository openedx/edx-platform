import json

from .oauth import OAuth2Test


class ZoomOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.zoom.ZoomOAuth2'
    user_data_url = 'https://api.zoom.us/v2/users/me'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar-token',
        'token_type': 'bearer',
        'refresh_token': 'foobar-refresh-token',
        'expires_in': 3599,
        'scope': 'identity'
    })
    user_data_body = json.dumps({
        'id': 'foobar',
        'first_name': 'Foo',
        'last_name': 'Bar',
        'email': 'foobar@email.com',
        'type': 2,
        'role_name': 'Foobar',
        'pmi': 1234567890,
        'use_pmi': False,
        'vanity_url': 'https://foobar.zoom.us/my/foobar',
        'personal_meeting_url': 'https://foobar.zoom.us/j/1234567890',
        'timezone': 'America/Denver',
        'verified': 1,
        'dept': '',
        'created_at': '2019-04-05T15:24:32Z',
        'last_login_time': '2019-12-16T18:02:48Z',
        'last_client_version': 'version',
        'pic_url': 'https://foobar.zoom.us/p/123456789',
        'host_key': '123456',
        'jid': 'foobar@xmpp.zoom.us',
        'group_ids': [],
        'im_group_ids': [
            'foobar-group-id'
        ],
        'account_id': 'foobar-account-id',
        'language': 'en-US',
        'phone_country': 'US',
        'phone_number': '+1 1234567891',
        'status': 'active'
    })
    refresh_token_body = json.dumps({
        'access_token': 'foobar-new-token',
        'token_type': 'bearer',
        'refresh_token': 'foobar-new-refresh-token',
        'expires_in': 3599,
        'scope': 'identity'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()

    def test_refresh_token(self):
        user, social = self.do_refresh_token()
        self.assertEqual(user.username, self.expected_username)
        self.assertEqual(social.extra_data['access_token'], 'foobar-new-token')
