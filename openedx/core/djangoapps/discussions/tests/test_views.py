"""
Test app view logic
"""
# pylint: disable=test-inherits-tests
import unittest

import ddt
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from xmodule.modulestore.tests.django_utils import CourseUserType
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.factories import CourseFactory

from ..models import AVAILABLE_PROVIDER_MAP


DATA_LEGACY_COHORTS = {
    'divided_inline_discussions': [],
    'divided_course_wide_discussions': [],
    'always_divide_inline_discussions': True,
    'division_scheme': 'none',
}
DATA_LEGACY_CONFIGURATION = {
    'allow_anonymous': True,
    'allow_anonymous_to_peers': True,
    'discussion_blackouts': [],
    'discussion_topics': {
        'General': {
            'id': 'course',
        },
    },
}
DATA_LTI_CONFIGURATION = {
    'lti_1p1_client_key': 'KEY',
    'lti_1p1_client_secret': 'SECRET',
    'lti_1p1_launch_url': 'https://localhost',
    'version': 'lti_1p1'
}


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'URLs are only configured in LMS')
class ApiTest(ModuleStoreTestCase, APITestCase):
    """
    Test basic API operations
    """
    CREATE_USER = True
    USER_TYPE = None

    def setUp(self):
        super().setUp()
        store = ModuleStoreEnum.Type.split
        self.course = CourseFactory.create(default_store=store)
        self.url = reverse(
            'discussions',
            kwargs={
                'course_key_string': str(self.course.id),
            }
        )
        if self.USER_TYPE:
            self.user = self.create_user_for_course(self.course, user_type=self.USER_TYPE)

    def _get(self):
        return self.client.get(self.url)

    def _post(self, data):
        return self.client.post(self.url, data, format='json')


class UnauthorizedApiTest(ApiTest):
    """
    Logged-out users should _not_ have any access
    """

    expected_response_code = status.HTTP_401_UNAUTHORIZED

    def test_access_get(self):
        response = self._get()
        assert response.status_code == self.expected_response_code

    def test_access_patch(self):
        response = self.client.patch(self.url)
        assert response.status_code == self.expected_response_code

    def test_access_post(self):
        response = self._post({})
        assert response.status_code == self.expected_response_code

    def test_access_put(self):
        response = self.client.put(self.url)
        assert response.status_code == self.expected_response_code


class AuthenticatedApiTest(UnauthorizedApiTest):
    """
    Logged-in users should _not_ have any access
    """

    expected_response_code = status.HTTP_403_FORBIDDEN
    USER_TYPE = CourseUserType.ENROLLED


class AuthorizedApiTest(AuthenticatedApiTest):
    """
    Global Staff should have access to all supported methods
    """

    expected_response_code = status.HTTP_200_OK
    USER_TYPE = CourseUserType.GLOBAL_STAFF

    def test_access_patch(self):
        response = self.client.patch(self.url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_access_put(self):
        response = self.client.put(self.url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class CourseStaffAuthorizedTest(AuthorizedApiTest):
    """
    Course Staff should have the same access as Global Staff
    """

    USER_TYPE = CourseUserType.UNENROLLED_STAFF


@ddt.ddt
class DataTest(AuthorizedApiTest):
    """
    Check API-data correctness
    """

    def _assert_defaults(self, response):
        """
        Check for default values
        """
        data = response.json()
        assert response.status_code == self.expected_response_code
        assert not data['enabled']
        assert data['provider_type'] == 'legacy'
        assert data['providers']['available']['legacy'] == AVAILABLE_PROVIDER_MAP['legacy']
        assert data['lti_configuration'] == {}
        assert data['plugin_configuration'] == {
            'allow_anonymous': True,
            'allow_anonymous_to_peers': False,
            'always_divide_inline_discussions': False,
            'available_division_schemes': [],
            'discussion_blackouts': [],
            'discussion_topics': {'General': {'id': 'course'}},
            'divided_course_wide_discussions': [],
            'divided_inline_discussions': [],
            'division_scheme': 'none',
        }
        assert len(data['plugin_configuration']) > 0

    def _setup_lti(self):
        """
        Configure an LTI-based provider
        """
        payload = {
            'enabled': True,
            'provider_type': 'piazza',
            'lti_configuration': DATA_LTI_CONFIGURATION,
            'plugin_configuration': {
            }
        }
        response = self._post(payload)
        data = response.json()
        assert response.status_code == self.expected_response_code
        return data

    def test_get_nonexistent_with_defaults(self):
        """
        If no record exists, defaults should be returned.
        """
        response = self._get()
        self._assert_defaults(response)

    def test_post_everything(self):
        """
        API should accept requests to update _all_ fields at once
        """
        data = self._setup_lti()
        assert data['enabled']
        assert data['provider_type'] == 'piazza'
        assert data['providers']['available']['piazza'] == AVAILABLE_PROVIDER_MAP['piazza']
        assert data['lti_configuration'] == DATA_LTI_CONFIGURATION
        assert len(data['plugin_configuration']) == 0
        assert len(data['lti_configuration']) > 0
        response = self._get()
        # the GET should pull back the same data as the POST
        response_data = response.json()
        assert response_data == data

    def test_post_invalid_key(self):
        """
        Unsupported keys should be gracefully ignored
        """
        payload = {
            'non-existent-key': 'value',
        }
        response = self._post(payload)
        self._assert_defaults(response)

    def test_configuration_valid(self):
        """
        Check we can set basic configuration
        """
        provider_type = 'piazza'
        payload = {
            'enabled': True,
            'provider_type': provider_type,
            'plugin_configuration': {
                'key': 'value',
            },
        }
        self._post(payload)
        response = self._get()
        data = response.json()
        assert data['enabled']
        assert data['provider_type'] == provider_type
        assert data['plugin_configuration'] == payload['plugin_configuration']

    @ddt.data(
        {
            'enabled': 3,
        },
    )
    def test_configuration_invalid(self, payload):
        """
        Check validation of basic configuration
        """
        with self.assertRaises(ValidationError):
            response = self._post(payload)
        response = self._get()
        self._assert_defaults(response)

    def test_post_lti_valid(self):
        """
        Check we can set LTI configuration
        """
        provider_type = 'piazza'
        for key, value in DATA_LTI_CONFIGURATION.items():
            payload = {
                'enabled': True,
                'provider_type': provider_type,
                'lti_configuration': {
                    key: value,
                }
            }
            response = self._post(payload)
            response = self._get()
            data = response.json()
            assert data['enabled']
            assert data['provider_type'] == provider_type
            assert data['lti_configuration'][key] == value

    def test_post_lti_invalid(self):
        """
        Check validation of LTI configuration ignores unsupported values

        The fields are all open-ended strings and will accept any values.
        """
        provider_type = 'piazza'
        for key, value in DATA_LTI_CONFIGURATION.items():
            payload = {
                'enabled': True,
                'provider_type': provider_type,
                'lti_configuration': {
                    key: value,
                    'ignored-key': 'ignored value',
                }
            }
            response = self._post(payload)
            assert response
            response = self._get()
            data = response.json()
            assert data['enabled']
            assert data['provider_type'] == provider_type
            assert data['lti_configuration'][key] == value
            assert 'ignored-key' not in data['lti_configuration']

    def test_post_legacy_valid(self):
        """
        Check we can set legacy settings configuration
        """
        provider_type = 'legacy'
        for key, value in DATA_LEGACY_CONFIGURATION.items():
            payload = {
                'enabled': True,
                'provider_type': provider_type,
                'plugin_configuration': {
                    key: value,
                }
            }
            response = self._post(payload)
            assert response
            response = self._get()
            data = response.json()
            assert data['enabled']
            assert data['provider_type'] == provider_type
            assert data['plugin_configuration'][key] == value

    @ddt.data(
        {
            'allow_anonymous': 3,
        },
        {
            'allow_anonymous_to_peers': 3,
        },
        {
            'discussion_blackouts': 3,
        },
        {
            'discussion_topics': 3,
        },
    )
    def test_post_legacy_invalid(self, plugin_configuration):
        """
        Check validation of legacy settings configuration
        """
        provider_type = 'legacy'
        payload = {
            'enabled': True,
            'provider_type': provider_type,
            'plugin_configuration': plugin_configuration,
        }
        with self.assertRaises(ValidationError):
            response = self._post(payload)
            if status.is_client_error(response.status_code):
                raise ValidationError(str(response.status_code))
        response = self._get()
        self._assert_defaults(response)

    @ddt.data(*DATA_LEGACY_COHORTS.items())
    def test_post_cohorts_valid(self, kvp):
        """
        Check we can set legacy cohorts configuration
        """
        key, value = kvp
        provider_type = 'legacy'
        payload = {
            'enabled': True,
            'provider_type': provider_type,
            'plugin_configuration': {
                key: value,
            }
        }
        response = self._post(payload)
        response = self._get()
        data = response.json()
        assert data['enabled']
        assert data['provider_type'] == provider_type
        assert data['plugin_configuration'][key] == value

    @ddt.data(*DATA_LEGACY_COHORTS.items())
    def test_post_cohorts_invalid(self, kvp):
        """
        Check validation of legacy cohorts configuration
        """
        key, value = kvp
        if isinstance(value, str):
            # For the string value, we can only fail here if it's blank
            value = ''
        else:
            # Otherwise, submit a string when non-string is required
            value = str(value)
        provider_type = 'legacy'
        payload = {
            'enabled': True,
            'provider_type': provider_type,
            'plugin_configuration': {
                key: value,
            }
        }
        with self.assertRaises(ValidationError):
            response = self._post(payload)
            if status.is_client_error(response.status_code):
                raise ValidationError(str(response.status_code))
        response = self._get()
        self._assert_defaults(response)

    def test_change_to_lti(self):
        """
        Ensure we can switch to an LTI-backed provider (from a non-LTI one)
        """
        payload = {
            'enabled': True,
            'provider_type': 'legacy',
            'plugin_configuration': {
                'allow_anonymous': False,
            },
        }
        response = self._post(payload)
        data = response.json()
        data = self._setup_lti()
        assert data['enabled']
        assert data['provider_type'] == 'piazza'
        assert not data['plugin_configuration']
        assert data['lti_configuration']

    def test_change_from_lti(self):
        """
        Ensure we can switch away from an LTI-backed provider (to a non-LTI one)
        """
        data = self._setup_lti()
        payload = {
            'enabled': True,
            'provider_type': 'legacy',
            'plugin_configuration': {
                'allow_anonymous': False,
            },
        }
        response = self._post(payload)
        data = response.json()
        assert data['enabled']
        assert data['provider_type'] == 'legacy'
        assert not data['plugin_configuration']['allow_anonymous']
        assert not data['lti_configuration']
