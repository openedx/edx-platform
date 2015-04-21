""" Commerce app tests package. """
import json

import httpretty
import jwt
import mock

from commerce.api import EcommerceAPI


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
        'order': {'number': ORDER_NUMBER},   # never both None.
        'payment_data': PAYMENT_DATA,
    }
    ECOMMERCE_API_SUCCESSFUL_BODY_JSON = json.dumps(ECOMMERCE_API_SUCCESSFUL_BODY)  # pylint: disable=invalid-name

    def assertValidJWTAuthHeader(self, request, user, key):
        """ Verifies that the JWT Authorization header is correct. """
        expected_jwt = jwt.encode({'username': user.username, 'email': user.email}, key)
        self.assertEqual(request.headers['Authorization'], 'JWT {}'.format(expected_jwt))

    def assertValidBasketRequest(self, request, user, jwt_signing_key, sku, processor):
        """ Verifies that an order request to the E-Commerce Service is valid. """
        self.assertValidJWTAuthHeader(request, user, jwt_signing_key)
        expected_body_data = {
            'products': [{'sku': sku}],
            'checkout': True,
            'payment_processor_name': processor
        }
        self.assertEqual(json.loads(request.body), expected_body_data)
        self.assertEqual(request.headers['Content-Type'], 'application/json')

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
        httpretty.register_uri(httpretty.POST, url, status=status, body=body)

    class mock_create_basket(object):    # pylint: disable=invalid-name
        """ Mocks calls to EcommerceAPI.create_basket. """

        patch = None

        def __init__(self, **kwargs):
            default_kwargs = {'return_value': EcommerceApiTestMixin.ECOMMERCE_API_SUCCESSFUL_BODY}
            default_kwargs.update(kwargs)
            self.patch = mock.patch.object(EcommerceAPI, 'create_basket', mock.Mock(**default_kwargs))

        def __enter__(self):
            self.patch.start()
            return self.patch.new

        def __exit__(self, exc_type, exc_val, exc_tb):  # pylint: disable=unused-argument
            self.patch.stop()
