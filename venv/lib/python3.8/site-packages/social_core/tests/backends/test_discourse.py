from urllib.parse import parse_qs, urlparse

import requests
from httpretty import HTTPretty

from ...exceptions import AuthException
from .base import BaseBackendTest


class DiscourseTest(BaseBackendTest):
    backend_path = 'social_core.backends.discourse.DiscourseAuth'
    expected_username = 'beepboop'
    raw_complete_url = '/complete/{0}/'

    def post_start(self):
        pass

    def do_start(self):
        self.post_start()
        start = self.backend.start()
        start_url = start.url
        return_url = self.backend.redirect_uri
        # NOTE: This is how we generated sso:
        # sso = b64encode(urlencode({
        #     'email': 'user@example.com',
        #     'username': 'beepboop',
        #     'nonce': '6YRje7xlXhpyeJ6qtvBeTUjHkXo1UCTQmCrzN8GXfja3AoAFk2' + \
        #              'CieDRYgSqMYi4W',
        #     'return_sso_url': 'http://myapp.com'
        # }))
        sso = 'dXNlcm5hbWU9YmVlcGJvb3Ambm9uY2U9NllSamU3eGxYaHB5ZUo2cXR2QmV' + \
              'UVWpIa1hvMVVDVFFtQ3J6TjhHWGZqYTNBb0FGazJDaWVEUllnU3FNWWk0Vy' + \
              'ZlbWFpbD11c2VyJTQwZXhhbXBsZS5jb20mcmV0dXJuX3Nzb191cmw9aHR0c' + \
              'CUzQSUyRiUyRm15YXBwLmNvbQ=='
        # NOTE: the signature was verified using the 'foo' key, like so:
        # hmac.new('foo', sso, sha256).hexdigest()
        sig = '04063f17c99a97b1a765c1e0d7bbb61afb8471d79a39ddcd6af5ba3c93eb10e1'
        response_query_params = f'sso={sso}&sig={sig}'

        response_url = f'{return_url}?{response_query_params}'
        HTTPretty.register_uri(
            HTTPretty.GET, start_url, status=301, location=response_url
        )
        HTTPretty.register_uri(
            HTTPretty.GET,
            return_url,
            status=200,
            content_type='text/html',
        )

        response = requests.get(start_url)
        query_values = {
            k: v[0] for k, v in parse_qs(urlparse(response.url).query).items()
        }
        self.strategy.set_request_data(query_values, self.backend)

        return self.backend.complete()

    def test_login(self):
        """
        Test that we can authenticate with the Discourse IdP
        """
        # pretend we've started with a URL like /login/discourse:
        self.strategy.set_settings(
            {'SERVER_URL': 'http://example.com', 'SECRET': 'foo'}
        )
        self.do_login()

    def test_failed_login(self):
        """
        Test that authentication fails when our request is signed with a
        different secret than our payload
        """
        self.strategy.set_settings(
            {'SERVER_URL': 'http://example.com', 'SECRET': 'bar'}
        )
        with self.assertRaises(AuthException):
            self.do_login()
