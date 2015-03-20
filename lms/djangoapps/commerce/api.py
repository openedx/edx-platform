""" E-Commerce API client """

import json
import logging

from django.conf import settings
import jwt
import requests
from requests import Timeout
from rest_framework.status import HTTP_200_OK

from commerce.exceptions import InvalidResponseError, TimeoutError, InvalidConfigurationError


log = logging.getLogger(__name__)


class EcommerceAPI(object):
    """ E-Commerce API client. """

    def __init__(self, url=None, key=None, timeout=None):
        self.url = url or settings.ECOMMERCE_API_URL
        self.key = key or settings.ECOMMERCE_API_SIGNING_KEY
        self.timeout = timeout or getattr(settings, 'ECOMMERCE_API_TIMEOUT', 5)

        if not (self.url and self.key):
            raise InvalidConfigurationError('Values for both url and key must be set.')

        # Remove slashes, so that we can properly format URLs regardless of
        # whether the input includes a trailing slash.
        self.url = self.url.strip('/')

    def _get_jwt(self, user):
        """
        Returns a JWT object with the specified user's info.

        Raises AttributeError if settings.ECOMMERCE_API_SIGNING_KEY is not set.
        """
        data = {
            'username': user.username,
            'email': user.email
        }
        return jwt.encode(data, self.key)

    def create_order(self, user, sku):
        """
        Create a new order.

        Arguments
            user    --  User for which the order should be created.
            sku     --  SKU of the course seat being ordered.

        Returns a tuple with the order number, order status, API response data.
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'JWT {}'.format(self._get_jwt(user))
        }

        url = '{}/orders/'.format(self.url)

        try:
            response = requests.post(url, data=json.dumps({'sku': sku}), headers=headers, timeout=self.timeout)
            data = response.json()
        except Timeout:
            msg = 'E-Commerce API request timed out.'
            log.error(msg)
            raise TimeoutError(msg)

        except ValueError:
            msg = 'E-Commerce API response is not valid JSON.'
            log.exception(msg)
            raise InvalidResponseError(msg)

        status_code = response.status_code

        if status_code == HTTP_200_OK:
            return data['number'], data['status'], data
        else:
            msg = u'Response from E-Commerce API was invalid: (%(status)d) - %(msg)s'
            msg_kwargs = {
                'status': status_code,
                'msg': data.get('user_message'),
            }
            log.error(msg, msg_kwargs)
            raise InvalidResponseError(msg % msg_kwargs)
