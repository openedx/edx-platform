"""Client to communicate with discovery service from lms"""

import json
import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404
from edx_rest_api_client.client import OAuthAPIClient
from provider.oauth2.models import Client
from requests import RequestException
from rest_framework import status

logger = logging.getLogger(__name__)

VERSION = 'v1'


class DiscoveryClient(OAuthAPIClient):

    def __init__(self):
        client = get_object_or_404(Client, name='discovery')
        super(DiscoveryClient, self).__init__(settings.LMS_ROOT_URL, client.client_id, client.client_secret)
        self._api_url = '{discovery_url}/api/{version}'.format(discovery_url=client.url, version=VERSION)

    def _get(self, path):
        try:
            self.response = self.request('GET', '{api_url}{path}'.format(api_url='http://local.philanthropyu.org:18381/api/v1', path=path))
        except RequestException as exc:
            logger.error(exc.response.text)
            raise ValidationError(json.loads(exc.response.text).get('error'))
        return self._handle_response()

    def _handle_response(self):
        status_code = self.response.status_code
        response_body = json.loads(self.response.text)
        if status_code == status.HTTP_200_OK:
            return response_body

        logger.error(self.response.text)
        if status_code == status.HTTP_403_FORBIDDEN:
            raise PermissionDenied
        raise Http404 if status_code == status.HTTP_404_NOT_FOUND else ValidationError(response_body.get('detail'))

    def active_programs(self):
        return self._get('/programs/?status=active')

    def get_program(self, uuid):
        return self._get('/programs/{uuid}'.format(uuid=uuid))
