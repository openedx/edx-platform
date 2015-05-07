""" Commerce app tests package. """
import json

from django.test import TestCase
from django.test.utils import override_settings
import httpretty
import jwt
import mock

from commerce import ecommerce_api_client
from student.tests.factories import UserFactory


TEST_API_URL = 'http://example.com/api'
TEST_API_SIGNING_KEY = 'edx'
TEST_BASKET_ID = 7
TEST_ORDER_NUMBER = '100004'
TEST_PAYMENT_DATA = {
    'payment_processor_name': 'test-processor',
    'payment_form_data': {},
    'payment_page_url': 'http://example.com/pay',
}


class EcommerceApiClientTest(TestCase):
    """ Tests to ensure the client is initialized properly. """

    TEST_USER_EMAIL = 'test@example.com'
    TEST_CLIENT_ID = 'test-client-id'

    @override_settings(ECOMMERCE_API_SIGNING_KEY=TEST_API_SIGNING_KEY, ECOMMERCE_API_URL=TEST_API_URL)
    @httpretty.activate
    def test_tracking_context(self):
        """ Ensure the tracking context is set up in the api client correctly
        and automatically. """
        user = UserFactory()
        user.email = self.TEST_USER_EMAIL
        user.save()  # pylint: disable=no-member

        # fake an ecommerce api request.
        httpretty.register_uri(
            httpretty.POST,
            '{}/baskets/1/'.format(TEST_API_URL),
            status=200, body='{}',
            adding_headers={'Content-Type': 'application/json'}
        )
        mock_tracker = mock.Mock()
        mock_tracker.resolve_context = mock.Mock(return_value={'client_id': self.TEST_CLIENT_ID})
        with mock.patch('commerce.tracker.get_tracker', return_value=mock_tracker):
            ecommerce_api_client(user).baskets(1).post()

        # make sure the request's JWT token payload included correct tracking context values.
        actual_header = httpretty.last_request().headers['Authorization']
        expected_payload = {
            'username': user.username,
            'email': user.email,
            'tracking_context': {
                'lms_user_id': user.id,  # pylint: disable=no-member
                'lms_client_id': self.TEST_CLIENT_ID,
            },
        }
        expected_header = 'JWT {}'.format(jwt.encode(expected_payload, TEST_API_SIGNING_KEY))
        self.assertEqual(actual_header, expected_header)
