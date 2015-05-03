""" Commerce app tests package. """
import json

from django.test import TestCase
from django.test.utils import override_settings
from ecommerce_api_client.client import EcommerceApiClient
import httpretty
import jwt
import mock

from commerce import ecommerce_api_client
from student.tests.factories import UserFactory


class EcommerceApiClientTest(TestCase):
    """ Tests to ensure the client is initialized properly. """

    TEST_SIGNING_KEY = 'edx'
    TEST_API_URL = 'http://example.com/api'
    TEST_USER_EMAIL = 'test@example.com'
    TEST_CLIENT_ID = 'test-client-id'

    @override_settings(ECOMMERCE_API_SIGNING_KEY=TEST_SIGNING_KEY, ECOMMERCE_API_URL=TEST_API_URL)
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
            '{}/baskets/1/'.format(self.TEST_API_URL),
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
        expected_header = 'JWT {}'.format(jwt.encode(expected_payload, self.TEST_SIGNING_KEY))
        self.assertEqual(actual_header, expected_header)


class EcommerceApiTestMixin(object):
    """ Mixin for tests utilizing the E-Commerce API. """

    ECOMMERCE_API_URL = 'http://example.com/api'
    ECOMMERCE_API_SIGNING_KEY = 'edx'
    BASKET_ID = 7
    ORDER_NUMBER = '100004'
    PROCESSOR = 'test-processor'
    PAYMENT_DATA = {
        'payment_processor_name': PROCESSOR,
        'payment_form_data': {},
        'payment_page_url': 'http://example.com/pay',
    }
    ORDER_DATA = {'number': ORDER_NUMBER}
    ECOMMERCE_API_SUCCESSFUL_BODY = {
        'id': BASKET_ID,
        'order': {'number': ORDER_NUMBER},  # never both None.
        'payment_data': PAYMENT_DATA,
    }
    ECOMMERCE_API_SUCCESSFUL_BODY_JSON = json.dumps(ECOMMERCE_API_SUCCESSFUL_BODY)  # pylint: disable=invalid-name

    def _mock_ecommerce_api(self, status=200, body=None, is_payment_required=False):
        """
        Mock calls to the E-Commerce API.

        The calling test should be decorated with @httpretty.activate.
        """
        self.assertTrue(httpretty.is_enabled(), 'Test is missing @httpretty.activate decorator.')

        url = self.ECOMMERCE_API_URL + '/baskets/'
        if body is None:
            response_data = {'id': self.BASKET_ID, 'payment_data': None, 'order': None}
            if is_payment_required:
                response_data['payment_data'] = self.PAYMENT_DATA
            else:
                response_data['order'] = {'number': self.ORDER_NUMBER}
            body = json.dumps(response_data)
        httpretty.register_uri(httpretty.POST, url, status=status, body=body,
                               adding_headers={'Content-Type': 'application/json'})

    class mock_create_basket(object):  # pylint: disable=invalid-name
        """ Mocks calls to E-Commerce API client basket creation method. """

        patch = None

        def __init__(self, **kwargs):
            default_kwargs = {'return_value': EcommerceApiTestMixin.ECOMMERCE_API_SUCCESSFUL_BODY}
            default_kwargs.update(kwargs)
            _mock = mock.Mock()
            _mock.post = mock.Mock(**default_kwargs)
            EcommerceApiClient.baskets = _mock
            self.patch = _mock

        def __enter__(self):
            return self.patch

        def __exit__(self, exc_type, exc_val, exc_tb):  # pylint: disable=unused-argument
            pass

    class mock_basket_order(object):  # pylint: disable=invalid-name
        """ Mocks calls to E-Commerce API client basket order method. """

        patch = None

        def __init__(self, **kwargs):
            _mock = mock.Mock()
            _mock.order.get = mock.Mock(**kwargs)
            EcommerceApiClient.baskets = lambda client, basket_id: _mock
            self.patch = _mock

        def __enter__(self):
            return self.patch

        def __exit__(self, exc_type, exc_val, exc_tb):  # pylint: disable=unused-argument
            pass
