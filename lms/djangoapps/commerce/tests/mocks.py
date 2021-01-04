""" Commerce app tests package. """
# pylint: disable=invalid-name


import json

import httpretty
from django.conf import settings

from . import factories


class mock_ecommerce_api_endpoint(object):
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

    host = settings.ECOMMERCE_API_URL.strip('/')

    def __init__(self, response=None, status=200, expect_called=True, exception=None, reset_on_exit=True):
        """
        Keyword Arguments:
            response: a JSON-serializable Python type representing the desired response body.
            status: desired HTTP status for the response.
            expect_called: a boolean indicating whether an API request was expected; set
                to False if we should ensure that no request arrived, or None to skip checking
                if the request arrived
            exception: raise this exception instead of returning an HTTP response when called.
            reset_on_exit (bool): Indicates if `httpretty` should be reset after the decorator exits.
        """
        self.response = response or self.default_response
        self.status = status
        self.expect_called = expect_called
        self.exception = exception
        self.reset_on_exit = reset_on_exit

    def get_uri(self):
        """
        Returns the uri to register with httpretty for this contextmanager.
        """
        return self.host + '/' + self.get_path().lstrip('/')

    def get_path(self):
        """
        Returns the path of the URI to register with httpretty for this contextmanager.

        Subclasses must override this method.

        Returns:
            str
        """
        raise NotImplementedError

    def _exception_body(self, request, uri, headers):
        """Helper used to create callbacks in order to have httpretty raise Exceptions."""
        raise self.exception

    def __enter__(self):
        httpretty.enable()
        httpretty.register_uri(
            self.method,
            self.get_uri(),
            status=self.status,
            body=self._exception_body if self.exception is not None else json.dumps(self.response),
            adding_headers={'Content-Type': 'application/json'},
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.expect_called is None:
            called_if_expected = True
        else:
            called_if_expected = self.expect_called == (httpretty.last_request().headers != {})
        httpretty.disable()

        if self.reset_on_exit:
            httpretty.reset()

        assert called_if_expected


class mock_basket_order(mock_ecommerce_api_endpoint):
    """ Mocks calls to E-Commerce API client basket order method. """

    default_response = {'number': 1}
    method = httpretty.GET

    def __init__(self, basket_id, **kwargs):
        super(mock_basket_order, self).__init__(**kwargs)
        self.basket_id = basket_id

    def get_path(self):
        return '/baskets/{}/order/'.format(self.basket_id)


class mock_create_refund(mock_ecommerce_api_endpoint):
    """ Mocks calls to E-Commerce API client refund creation method. """

    default_response = []
    method = httpretty.POST

    def get_path(self):
        return '/refunds/'


class mock_payment_processors(mock_ecommerce_api_endpoint):
    """
    Mocks calls to E-Commerce API payment processors method.
    """

    default_response = ['foo', 'bar']
    method = httpretty.GET

    def get_path(self):
        return "/payment/processors/"


class mock_process_refund(mock_ecommerce_api_endpoint):
    """ Mocks calls to E-Commerce API client refund process method. """

    default_response = []
    method = httpretty.PUT

    def __init__(self, refund_id, **kwargs):
        super(mock_process_refund, self).__init__(**kwargs)
        self.refund_id = refund_id

    def get_path(self):
        return '/refunds/{}/process/'.format(self.refund_id)


class mock_order_endpoint(mock_ecommerce_api_endpoint):
    """ Mocks calls to E-Commerce API client basket order method. """

    default_response = {'number': 'EDX-100001'}
    method = httpretty.GET

    def __init__(self, order_number, **kwargs):
        super(mock_order_endpoint, self).__init__(**kwargs)
        self.order_number = order_number

    def get_path(self):
        return '/orders/{}/'.format(self.order_number)


class mock_get_orders(mock_ecommerce_api_endpoint):
    """ Mocks calls to E-Commerce API client order get method. """

    default_response = {
        'results': [
            factories.OrderFactory(
                lines=[
                    factories.OrderLineFactory(
                        product=factories.ProductFactory(attribute_values=[factories.ProductAttributeFactory(
                            name='certificate_type',
                            value='verified'
                        )])
                    )
                ]
            ),
            factories.OrderFactory(
                lines=[
                    factories.OrderLineFactory(
                        product=factories.ProductFactory(attribute_values=[factories.ProductAttributeFactory(
                            name='certificate_type',
                            value='verified'
                        )])
                    ),
                    factories.OrderLineFactory(
                        product=factories.ProductFactory(attribute_values=[factories.ProductAttributeFactory(
                            name='certificate_type',
                            value='verified'
                        )])
                    ),
                ]
            ),
            factories.OrderFactory(
                lines=[
                    factories.OrderLineFactory(product=factories.ProductFactory(product_class='Coupon'))
                ]
            ),
        ]
    }
    method = httpretty.GET

    def get_path(self):
        return '/orders/'
