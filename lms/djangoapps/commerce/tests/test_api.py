""" Tests the E-Commerce API module. """

import json

from ddt import ddt, data
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase
from django.test.utils import override_settings
import httpretty
from requests import Timeout

from commerce.api import EcommerceAPI
from commerce.constants import OrderStatus
from commerce.exceptions import InvalidResponseError, TimeoutError, InvalidConfigurationError
from commerce.tests import EcommerceApiTestMixin
from student.tests.factories import UserFactory


@ddt
@override_settings(ECOMMERCE_API_URL=EcommerceApiTestMixin.ECOMMERCE_API_URL,
                   ECOMMERCE_API_SIGNING_KEY=EcommerceApiTestMixin.ECOMMERCE_API_SIGNING_KEY)
class EcommerceAPITests(EcommerceApiTestMixin, TestCase):
    """ Tests for the E-Commerce API client. """

    SKU = '1234'

    def setUp(self):
        super(EcommerceAPITests, self).setUp()
        self.url = reverse('commerce:orders')
        self.user = UserFactory()
        self.api = EcommerceAPI()

    def test_constructor_url_strip(self):
        """ Verifies that the URL is stored with trailing slashes removed. """
        url = 'http://example.com'
        api = EcommerceAPI(url, 'edx')
        self.assertEqual(api.url, url)

        api = EcommerceAPI(url + '/', 'edx')
        self.assertEqual(api.url, url)

    @override_settings(ECOMMERCE_API_URL=None, ECOMMERCE_API_SIGNING_KEY=None)
    def test_no_settings(self):
        """
        If the settings ECOMMERCE_API_URL and ECOMMERCE_API_SIGNING_KEY are invalid, the constructor should
        raise a ValueError.
        """
        self.assertRaises(InvalidConfigurationError, EcommerceAPI)

    @httpretty.activate
    def test_create_order(self):
        """ Verify the method makes a call to the E-Commerce API with the correct headers and data. """
        self._mock_ecommerce_api()
        number, status, body = self.api.create_order(self.user, self.SKU)

        # Validate the request sent to the E-Commerce API endpoint.
        request = httpretty.last_request()
        self.assertValidOrderRequest(request, self.user, self.ECOMMERCE_API_SIGNING_KEY, self.SKU)

        # Validate the data returned by the method
        self.assertEqual(number, self.ORDER_NUMBER)
        self.assertEqual(status, OrderStatus.COMPLETE)
        self.assertEqual(body, self.ECOMMERCE_API_SUCCESSFUL_BODY)

    @httpretty.activate
    @data(400, 401, 405, 406, 429, 500, 503)
    def test_create_order_with_invalid_http_status(self, status):
        """ If the E-Commerce API returns a non-200 status, the method should raise an InvalidResponseError. """
        self._mock_ecommerce_api(status=status, body=json.dumps({'user_message': 'FAIL!'}))
        self.assertRaises(InvalidResponseError, self.api.create_order, self.user, self.SKU)

    @httpretty.activate
    def test_create_order_with_invalid_json(self):
        """ If the E-Commerce API returns un-parseable data, the method should raise an InvalidResponseError. """
        self._mock_ecommerce_api(body='TOTALLY NOT JSON!')
        self.assertRaises(InvalidResponseError, self.api.create_order, self.user, self.SKU)

    @httpretty.activate
    def test_create_order_with_timeout(self):
        """ If the call to the E-Commerce API times out, the method should raise a TimeoutError. """

        def request_callback(_request, _uri, _headers):
            """ Simulates API timeout """
            raise Timeout

        self._mock_ecommerce_api(body=request_callback)

        self.assertRaises(TimeoutError, self.api.create_order, self.user, self.SKU)
