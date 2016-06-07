""" Commerce app tests package. """
import json

import httpretty

from commerce.tests import TEST_API_URL


class mock_ecommerce_api_endpoint(object):  # pylint: disable=invalid-name
    """
    Base class for contextmanagers used to mock calls to api endpoints.

    The contextmanager internally activates and deactivates httpretty as
    required, therefore it is not advised to use this mock endpoint in
    test cases where httpretty is being used directly.
    """

    # override this in subclasses.
    default_response = None

    # override this in subclasses, using one of httpretty's method constants
    method = None

    def __init__(self, response=None, status=200, expect_called=True, exception=None):
        """
        Keyword Arguments:
            response: a JSON-serializable Python type representing the desired response body.
            status: desired HTTP status for the response.
            expect_called: a boolean indicating whether an API request was expected; set
                to False if we should ensure that no request arrived.
            exception: raise this exception instead of returning an HTTP response when called.
        """
        self.response = response or self.default_response
        self.status = status
        self.expect_called = expect_called
        self.exception = exception

    def get_uri(self):
        """
        Return the uri to register with httpretty for this contextmanager.

        Subclasses must override this method.
        """
        raise NotImplementedError

    def _exception_body(self, request, uri, headers):  # pylint: disable=unused-argument
        """Helper used to create callbacks in order to have httpretty raise Exceptions."""
        raise self.exception  # pylint: disable=raising-bad-type

    def __enter__(self):
        httpretty.reset()
        httpretty.enable()
        httpretty.register_uri(
            self.method,
            self.get_uri(),
            status=self.status,
            body=self._exception_body if self.exception is not None else json.dumps(self.response),
            adding_headers={'Content-Type': 'application/json'},
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self.expect_called == (httpretty.last_request().headers != {})
        httpretty.disable()


class mock_create_basket(mock_ecommerce_api_endpoint):  # pylint: disable=invalid-name
    """ Mocks calls to E-Commerce API client basket creation method. """

    default_response = {
        'id': 7,
        'order': {'number': '100004'},  # never both None.
        'payment_data': {
            'payment_processor_name': 'test-processor',
            'payment_form_data': {},
            'payment_page_url': 'http://example.com/pay',
        },
    }
    method = httpretty.POST

    def get_uri(self):
        return TEST_API_URL + '/baskets/'


class mock_basket_order(mock_ecommerce_api_endpoint):  # pylint: disable=invalid-name
    """ Mocks calls to E-Commerce API client basket order method. """

    default_response = {'number': 1}
    method = httpretty.GET

    def __init__(self, basket_id, **kwargs):
        super(mock_basket_order, self).__init__(**kwargs)
        self.basket_id = basket_id

    def get_uri(self):
        return TEST_API_URL + '/baskets/{}/order/'.format(self.basket_id)


class mock_create_refund(mock_ecommerce_api_endpoint):  # pylint: disable=invalid-name
    """ Mocks calls to E-Commerce API client refund creation method. """

    default_response = []
    method = httpretty.POST

    def get_uri(self):
        return TEST_API_URL + '/refunds/'


class mock_order_endpoint(mock_ecommerce_api_endpoint):  # pylint: disable=invalid-name
    """ Mocks calls to E-Commerce API client basket order method. """

    default_response = {'number': 'EDX-100001'}
    method = httpretty.GET

    def __init__(self, order_number, **kwargs):
        super(mock_order_endpoint, self).__init__(**kwargs)
        self.order_number = order_number

    def get_uri(self):
        return TEST_API_URL + '/orders/{}/'.format(self.order_number)
