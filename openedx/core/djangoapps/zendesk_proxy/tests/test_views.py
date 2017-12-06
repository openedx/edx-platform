"""Tests for zendesk_proxy views."""
from copy import deepcopy
import ddt
import json
from mock import MagicMock, patch

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from openedx.core.lib.api.test_utils import ApiTestCase
from openedx.core.djangoapps.zendesk_proxy.v0.views import ZENDESK_REQUESTS_PER_HOUR


@ddt.ddt
@override_settings(
    ZENDESK_URL="https://www.superrealurlsthataredefinitelynotfake.com",
    ZENDESK_OAUTH_ACCESS_TOKEN="abcdefghijklmnopqrstuvwxyz1234567890"
)
class ZendeskProxyTestCase(ApiTestCase):
    """Tests for zendesk_proxy views."""

    def setUp(self):
        self.url = reverse('zendesk_proxy_v0')
        self.request_data = {
            'name': 'John Q. Student',
            'tags': ['python_unit_test'],
            'email': {
                'from': 'JohnQStudent@example.com',
                'subject': 'Python Unit Test Help Request',
                'message': "Help! I'm trapped in a unit test factory and I can't get out!",
            }
        }
        return super(ZendeskProxyTestCase, self).setUp()

    def test_post(self):
        with patch('requests.post', return_value=MagicMock(status_code=201)) as mock_post:
            response = self.request_without_auth(
                'post',
                self.url,
                data=json.dumps(self.request_data),
                content_type='application/json'
            )
            self.assertHttpCreated(response)
            (mock_args, mock_kwargs) = mock_post.call_args
            self.assertEqual(mock_args, ('https://www.superrealurlsthataredefinitelynotfake.com/api/v2/tickets.json',))
            self.assertEqual(
                mock_kwargs,
                {
                    'headers': {
                        'content-type': 'application/json',
                        'Authorization': 'Bearer abcdefghijklmnopqrstuvwxyz1234567890'
                    },
                    'data': '{"ticket": {"comment": {"body": "Help! I\'m trapped in a unit test factory and I can\'t get out!"}, "subject": "Python Unit Test Help Request", "tags": ["python_unit_test"], "requester": {"name": "John Q. Student", "email": "JohnQStudent@example.com"}}}'  # pylint: disable=line-too-long
                }
            )

    @ddt.data('name', 'tags', 'email')
    def test_bad_request(self, key_to_delete):
        test_data = deepcopy(self.request_data)
        _ = test_data.pop(key_to_delete)

        response = self.request_without_auth(
            'post',
            self.url,
            data=json.dumps(test_data),
            content_type='application/json'
        )
        self.assertHttpBadRequest(response)

    @override_settings(
        ZENDESK_URL=None,
        ZENDESK_OAUTH_ACCESS_TOKEN=None
    )
    def test_missing_settings(self):
        response = self.request_without_auth(
            'post',
            self.url,
            data=json.dumps(self.request_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 503)

    @ddt.data(201, 400, 401, 403, 404, 500)
    def test_zendesk_status_codes(self, mock_code):
        with patch('requests.post', return_value=MagicMock(status_code=mock_code)):
            response = self.request_without_auth(
                'post',
                self.url,
                data=json.dumps(self.request_data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, mock_code)

    def test_unexpected_error_pinging_zendesk(self):
        with patch('requests.post', side_effect=Exception("WHAMMY")):
            response = self.request_without_auth(
                'post',
                self.url,
                data=json.dumps(self.request_data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 500)

    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'zendesk_proxy',
            }
        }
    )
    def test_rate_limiting(self):
        """
        Confirm rate limits work as expected. Note that drf's rate limiting makes use of the default cache to enforce
        limits; that's why this test needs a "real" default cache (as opposed to the usual-for-tests DummyCache)
        """
        for _ in range(ZENDESK_REQUESTS_PER_HOUR):
            self.request_without_auth('post', self.url)
        response = self.request_without_auth('post', self.url)
        self.assertEqual(response.status_code, 429)
