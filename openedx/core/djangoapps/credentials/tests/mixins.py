"""Mixins for use during testing."""

from openedx.core.djangoapps.credentials.models import CredentialsApiConfig


class CredentialsApiConfigMixin(object):
    """ Utilities for working with Credentials configuration during testing."""

    CREDENTIALS_DEFAULTS = {
        'enabled': True,
        'internal_service_url': 'http://internal.credentials.org/',
        'public_service_url': 'http://public.credentials.org/',
        'enable_learner_issuance': True,
        'enable_studio_authoring': True,
    }

    def create_credential_config(self, **kwargs):
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
                "uuid": "dummy-uuid-1"
            },
            {
                "id": 2,
                "username": "test",
                "credential": {
                    "credential_id": 2,
                    "program_id": 2
                },
                "status": "awarded",
                "uuid": "dummy-uuid-2"
            },
            {
                "id": 3,
                "username": "test",
                "credential": {
                    "credential_id": 3,
                    "program_id": 3
                },
                "status": "revoked",
                "uuid": "dummy-uuid-3"
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
                "uuid": "dummy-uuid-4"
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
                "uuid": "dummy-uuid-5"
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
                "uuid": "dummy-uuid-6"
            }
        ]
    }
