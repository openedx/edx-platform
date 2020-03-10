"""Client to communicate with discovery service from lms"""

import json

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from edx_rest_api_client.client import OAuthAPIClient
from provider.oauth2.models import Client
from rest_framework import status

VERSION = 'v1'


class DiscoveryClient(OAuthAPIClient):

    def __init__(self):
        client = get_object_or_404(Client, name='discovery')
        super(DiscoveryClient, self).__init__(settings.LMS_ROOT_URL, client.client_id, client.client_secret)
        self._api_url = '{discovery_url}/api/{version}'.format(discovery_url=client.url, version=VERSION)

    def active_programs(self):
        response = self.request('GET', '{api_url}/programs/?status=active'.format(api_url=self._api_url))
        if response.status_code == status.HTTP_200_OK:
            return json.loads(response.text)
        raise PermissionDenied
