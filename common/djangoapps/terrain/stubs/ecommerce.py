"""
Stub implementation of ecommerce service for acceptance tests
"""


import re

import six.moves.urllib.parse

from .http import StubHttpRequestHandler, StubHttpService


class StubEcommerceServiceHandler(StubHttpRequestHandler):  # pylint: disable=missing-class-docstring

    # pylint: disable=missing-function-docstring
    def do_GET(self):
        pattern_handlers = {
            '/api/v2/orders/$': self.get_orders_list,
        }
        if self.match_pattern(pattern_handlers):
            return
        self.send_response(404, content='404 Not Found')

    def match_pattern(self, pattern_handlers):
        """
        Find the correct handler method given the path info from the HTTP request.
        """
        path = six.moves.urllib.parse.urlparse(self.path).path
        for pattern in pattern_handlers:
            match = re.match(pattern, path)
            if match:
                pattern_handlers[pattern](**match.groupdict())
                return True
        return None

    def get_orders_list(self):
        """
        Stubs the orders list endpoint.
        """
        orders = {
            'results': [
                {
                    'status': 'Complete',
                    'number': 'Edx-123',
                    'total_excl_tax': '100.00',
                    'date_placed': '2016-04-21T23:14:23Z',
                    'lines': [
                        {
                            'title': 'Test Course',
                            'line_price_excl_tax': '100.00',
                            'product': {
                                'product_class': 'Seat'
                            }
                        }
                    ],
                }
            ]
        }
        orders = self.server.config.get('orders', orders)
        self.send_json_response(orders)


class StubEcommerceService(StubHttpService):
    HANDLER_CLASS = StubEcommerceServiceHandler
