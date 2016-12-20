"""Mixins for use during testing."""
import json

import httpretty

from openedx.core.djangoapps.credentials.models import CredentialsApiConfig


class CredentialsApiConfigMixin(object):
    """ Utilities for working with Credentials configuration during testing."""

    CREDENTIALS_DEFAULTS = {
        'enabled': True,
        'internal_service_url': 'http://internal.credentials.org/',
        'public_service_url': 'http://public.credentials.org/',
        'enable_learner_issuance': True,
        'enable_studio_authoring': True,
        'cache_ttl': 0,
    }

    def create_credentials_config(self, **kwargs):
        """ Creates a new CredentialsApiConfig with DEFAULTS, updated with any
        provided overrides.
        """
        fields = dict(self.CREDENTIALS_DEFAULTS, **kwargs)
        CredentialsApiConfig(**fields).save()

        return CredentialsApiConfig.current()


class CredentialsDataMixin(object):
    """Mixin mocking Credentials API URLs and providing fake data for testing."""
    CREDENTIALS_API_RESPONSE = {
        "next": None,
        "results": [
            {
                "id": 1,
                "username": "test",
                "credential": {
                    "credential_id": 1,
                    "program_id": 1
                },
                "status": "awarded",
                "uuid": "dummy-uuid-1",
                "certificate_url": "http://credentials.edx.org/credentials/dummy-uuid-1/"
            },
            {
                "id": 2,
                "username": "test",
                "credential": {
                    "credential_id": 2,
                    "program_id": 2
                },
                "status": "awarded",
                "uuid": "dummy-uuid-2",
                "certificate_url": "http://credentials.edx.org/credentials/dummy-uuid-2/"
            },
            {
                "id": 3,
                "username": "test",
                "credential": {
                    "credential_id": 3,
                    "program_id": 3
                },
                "status": "revoked",
                "uuid": "dummy-uuid-3",
                "certificate_url": "http://credentials.edx.org/credentials/dummy-uuid-3/"
            },
            {
                "id": 4,
                "username": "test",
                "credential": {
                    "course_id": "edx/test01/2015",
                    "credential_id": 4,
                    "certificate_type": "honor"
                },
                "status": "awarded",
                "uuid": "dummy-uuid-4",
                "certificate_url": "http://credentials.edx.org/credentials/dummy-uuid-4/"
            },
            {
                "id": 5,
                "username": "test",
                "credential": {
                    "course_id": "edx/test02/2015",
                    "credential_id": 5,
                    "certificate_type": "verified"
                },
                "status": "awarded",
                "uuid": "dummy-uuid-5",
                "certificate_url": "http://credentials.edx.org/credentials/dummy-uuid-5/"
            },
            {
                "id": 6,
                "username": "test",
                "credential": {
                    "course_id": "edx/test03/2015",
                    "credential_id": 6,
                    "certificate_type": "honor"
                },
                "status": "revoked",
                "uuid": "dummy-uuid-6",
                "certificate_url": "http://credentials.edx.org/credentials/dummy-uuid-6/"
            }
        ]
    }

    CREDENTIALS_NEXT_API_RESPONSE = {
        "next": None,
        "results": [
            {
                "id": 7,
                "username": "test",
                "credential": {
                    "credential_id": 7,
                    "program_id": 7
                },
                "status": "awarded",
                "uuid": "dummy-uuid-7",
                "certificate_url": "http://credentials.edx.org/credentials/dummy-uuid-7"
            },
            {
                "id": 8,
                "username": "test",
                "credential": {
                    "credential_id": 8,
                    "program_id": 8
                },
                "status": "awarded",
                "uuid": "dummy-uuid-8",
                "certificate_url": "http://credentials.edx.org/credentials/dummy-uuid-8/"
            }
        ]
    }

    def mock_credentials_api(self, user, data=None, status_code=200, reset_url=True, is_next_page=False):
        """Utility for mocking out Credentials API URLs."""
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock Credentials API calls.')
        internal_api_url = CredentialsApiConfig.current().internal_api_url.strip('/')

        url = internal_api_url + '/user_credentials/?username=' + user.username

        if reset_url:
            httpretty.reset()

        if data is None:
            data = self.CREDENTIALS_API_RESPONSE

        body = json.dumps(data)

        if is_next_page:
            next_page_url = internal_api_url + '/user_credentials/?page=2&username=' + user.username
            self.CREDENTIALS_NEXT_API_RESPONSE['next'] = next_page_url
            next_page_body = json.dumps(self.CREDENTIALS_NEXT_API_RESPONSE)
            httpretty.register_uri(
                httpretty.GET, next_page_url, body=body, content_type='application/json', status=status_code
            )
            httpretty.register_uri(
                httpretty.GET, url, body=next_page_body, content_type='application/json', status=status_code
            )
        else:
            httpretty.register_uri(
                httpretty.GET, url, body=body, content_type='application/json', status=status_code
            )
