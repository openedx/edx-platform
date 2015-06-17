""" Commerce app tests package. """
import json

import httpretty
import jwt
import mock

from commerce.api import EcommerceAPI
from commerce.constants import OrderStatus


class EcommerceApiTestMixin(object):
    """ Mixin for tests utilizing the E-Commerce API. """

    ECOMMERCE_API_URL = 'http://example.com/api'
    ECOMMERCE_API_SIGNING_KEY = 'edx'
    ORDER_NUMBER = '100004'
    ECOMMERCE_API_SUCCESSFUL_BODY = {
        'status': OrderStatus.COMPLETE,
        'number': ORDER_NUMBER,
        'payment_processor': 'cybersource',
        'payment_parameters': {'orderNumber': ORDER_NUMBER}
    }
    ECOMMERCE_API_SUCCESSFUL_BODY_JSON = json.dumps(ECOMMERCE_API_SUCCESSFUL_BODY)  # pylint: disable=invalid-name

    def assertValidJWTAuthHeader(self, request, user, key):
        """ Verifies that the JWT Authorization header is correct. """
        expected_jwt = jwt.encode({'username': user.username, 'email': user.email}, key)
        self.assertEqual(request.headers['Authorization'], 'JWT {}'.format(expected_jwt))

    def assertValidOrderRequest(self, request, user, jwt_signing_key, sku):
        """ Verifies that an order request to the E-Commerce Service is valid. """
        self.assertValidJWTAuthHeader(request, user, jwt_signing_key)

        self.assertEqual(request.body, '{{"sku": "{}"}}'.format(sku))
        self.assertEqual(request.headers['Content-Type'], 'application/json')

    def _mock_ecommerce_api(self, status=200, body=None):
        """
        Mock calls to the E-Commerce API.

        The calling test should be decorated with @httpretty.activate.
        """
        self.assertTrue(httpretty.is_enabled(), 'Test is missing @httpretty.activate decorator.')

        url = self.ECOMMERCE_API_URL + '/orders/'
        body = body or self.ECOMMERCE_API_SUCCESSFUL_BODY_JSON
        httpretty.register_uri(httpretty.POST, url, status=status, body=body)

    class mock_create_order(object):    # pylint: disable=invalid-name
        """ Mocks calls to EcommerceAPI.create_order. """

        patch = None

        def __init__(self, **kwargs):
            default_kwargs = {
                'return_value': (
                    EcommerceApiTestMixin.ORDER_NUMBER,
                    OrderStatus.COMPLETE,
                    EcommerceApiTestMixin.ECOMMERCE_API_SUCCESSFUL_BODY
                )
            }

            default_kwargs.update(kwargs)

            self.patch = mock.patch.object(EcommerceAPI, 'create_order', mock.Mock(**default_kwargs))

        def __enter__(self):
            self.patch.start()
            return self.patch.new

        def __exit__(self, exc_type, exc_val, exc_tb):  # pylint: disable=unused-argument
            self.patch.stop()
