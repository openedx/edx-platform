import json

from .oauth import OAuth2Test


class GiteaOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.gitea.GiteaOAuth2'
    user_data_url = 'https://gitea.com/api/v1/user'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer',
        'expires_in': 7200,
        'refresh_token': 'barfoo'
    })
    user_data_body = json.dumps({
        'id': 123456,
        'login': 'foobar',
        'full_name': 'Foo Bar',
        'email': 'foobar@example.com',
        'avatar_url': 'https://gitea.com/user/avatar/foobar/-1',
        'language': 'en-US',
        'is_admin': False,
        'last_login': '2016-12-28T12:26:19+01:00',
        'created': '2016-12-28T12:26:19+01:00',
        'restricted': False,
        'username': 'foobar'
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()


class GiteaCustomDomainOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.gitea.GiteaOAuth2'
    user_data_url = 'https://example.com/api/v1/user'
    expected_username = 'foobar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer',
        'expires_in': 7200,
        'refresh_token': 'barfoo'
    })
    user_data_body = json.dumps({
        'id': 123456,
        'login': 'foobar',
        'full_name': 'Foo Bar',
        'email': 'foobar@example.com',
        'avatar_url': 'https://example.com/user/avatar/foobar/-1',
        'language': 'en-US',
        'is_admin': False,
        'last_login': '2016-12-28T12:26:19+01:00',
        'created': '2016-12-28T12:26:19+01:00',
        'restricted': False,
        'username': 'foobar'
    })

    def test_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITEA_API_URL': 'https://example.com'
        })
        self.do_login()

    def test_partial_pipeline(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_GITEA_API_URL': 'https://example.com'
        })
        self.do_partial_pipeline()
