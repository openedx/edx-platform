import json
from urllib.parse import urlencode

from httpretty import HTTPretty

from ...exceptions import AuthForbidden
from .oauth import OAuth1Test, OAuth2Test


class BitbucketOAuthMixin:
    user_data_url = 'https://api.bitbucket.org/2.0/user'
    expected_username = 'foobar'
    bb_api_user_emails = 'https://api.bitbucket.org/2.0/user/emails'

    user_data_body = json.dumps({
        'created_on': '2012-03-29T18:07:38+00:00',
        'display_name': 'Foo Bar',
        'links': {
            'avatar': {'href': 'https://bitbucket.org/account/foobar/avatar/32/'},
            'followers': {'href': 'https://api.bitbucket.org/2.0/users/foobar/followers'},
            'following': {'href': 'https://api.bitbucket.org/2.0/users/foobar/following'},
            'hooks': {'href': 'https://api.bitbucket.org/2.0/users/foobar/hooks'},
            'html': {'href': 'https://bitbucket.org/foobar'},
            'repositories': {'href': 'https://api.bitbucket.org/2.0/repositories/foobar'},
            'self': {'href': 'https://api.bitbucket.org/2.0/users/foobar'}},
        'location': 'Fooville, Bar',
        'type': 'user',
        'username': 'foobar',
        'uuid': '{397621dc-0f78-329f-8d6d-727396248e3f}',
        'website': 'http://foobar.com'
    })

    emails_body = json.dumps({
        'page': 1,
        'pagelen': 10,
        'size': 2,
        'values': [
            {
                'email': 'foo@bar.com',
                'is_confirmed': True,
                'is_primary': True,
                'links': {'self': {'href': 'https://api.bitbucket.org/2.0/user/emails/foo@bar.com'}},
                'type': 'email'
            },
            {
                'email': 'not@confirme.com',
                'is_confirmed': False,
                'is_primary': False,
                'links': {'self': {'href': 'https://api.bitbucket.org/2.0/user/emails/not@confirmed.com'}},
                'type': 'email'
            }
        ]
    })


class BitbucketOAuth1Test(BitbucketOAuthMixin, OAuth1Test):
    backend_path = 'social_core.backends.bitbucket.BitbucketOAuth'

    request_token_body = urlencode({
        'oauth_token_secret': 'foobar-secret',
        'oauth_token': 'foobar',
        'oauth_callback_confirmed': 'true'
    })

    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })

    def test_login(self):
        HTTPretty.register_uri(HTTPretty.GET,
                               self.bb_api_user_emails,
                               status=200, body=self.emails_body)
        self.do_login()

    def test_partial_pipeline(self):
        HTTPretty.register_uri(HTTPretty.GET,
                               self.bb_api_user_emails,
                               status=200, body=self.emails_body)
        self.do_partial_pipeline()


class BitbucketOAuth1FailTest(BitbucketOAuth1Test):
    emails_body = json.dumps({
        'page': 1,
        'pagelen': 10,
        'size': 1,
        'values': [
            {
                'email': 'foo@bar.com',
                'is_confirmed': False,
                'is_primary': True,
                'links': {'self': {'href': 'https://api.bitbucket.org/2.0/user/emails/foo@bar.com'}},
                'type': 'email'
            }
        ]
    })

    def test_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_BITBUCKET_VERIFIED_EMAILS_ONLY': True
        })
        with self.assertRaises(AuthForbidden):
            super().test_login()

    def test_partial_pipeline(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_BITBUCKET_VERIFIED_EMAILS_ONLY': True
        })
        with self.assertRaises(AuthForbidden):
            super().test_partial_pipeline()


class BitbucketOAuth2Test(BitbucketOAuthMixin, OAuth2Test):
    backend_path = 'social_core.backends.bitbucket.BitbucketOAuth2'

    access_token_body = json.dumps({
        'access_token': 'foobar_access',
        'scopes': 'foo_scope',
        'expires_in': 3600,
        'refresh_token': 'foobar_refresh',
        'token_type': 'bearer'
    })

    def test_login(self):
        HTTPretty.register_uri(HTTPretty.GET,
                               self.bb_api_user_emails,
                               status=200, body=self.emails_body)
        self.do_login()

    def test_partial_pipeline(self):
        HTTPretty.register_uri(HTTPretty.GET,
                               self.bb_api_user_emails,
                               status=200, body=self.emails_body)
        self.do_partial_pipeline()


class BitbucketOAuth2FailTest(BitbucketOAuth2Test):
    emails_body = json.dumps({
        'page': 1,
        'pagelen': 10,
        'size': 1,
        'values': [
            {
                'email': 'foo@bar.com',
                'is_confirmed': False,
                'is_primary': True,
                'links': {'self': {'href': 'https://api.bitbucket.org/2.0/user/emails/foo@bar.com'}},
                'type': 'email'
            }
        ]
    })

    def test_login(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_BITBUCKET_OAUTH2_VERIFIED_EMAILS_ONLY': True
        })
        with self.assertRaises(AuthForbidden):
            super().test_login()

    def test_partial_pipeline(self):
        self.strategy.set_settings({
            'SOCIAL_AUTH_BITBUCKET_OAUTH2_VERIFIED_EMAILS_ONLY': True
        })
        with self.assertRaises(AuthForbidden):
            super().test_partial_pipeline()
