"""
Test app view logic
"""
# pylint: disable=test-inherits-tests
import itertools
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import ddt
from django.core.exceptions import ValidationError
from django.urls import reverse
from lti_consumer.models import CourseAllowPIISharingInLTIFlag
from rest_framework import status
from rest_framework.test import APITestCase

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.discussion.django_comment_client.tests.factories import RoleFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import CourseUserType, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from ..models import AVAILABLE_PROVIDER_MAP, DEFAULT_CONFIG_ENABLED, DEFAULT_PROVIDER_TYPE, Provider

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
DEFAULT_LEGACY_CONFIGURATION = {
    **DATA_LEGACY_CONFIGURATION,
    'allow_anonymous_to_peers': False,
    'always_divide_inline_discussions': False,
    'divided_inline_discussions': [],
    'divided_course_wide_discussions': [],
    'division_scheme': 'none',
    'available_division_schemes': [],

}

DEFAULT_LTI_CONFIGURATION = {
    'lti_1p1_client_key': '',
    'lti_1p1_client_secret': '',
    'lti_1p1_launch_url': '',
    'version': None,
    'pii_share_email': False,
    'pii_share_username': False,
}

DATA_LTI_CONFIGURATION = {
    'lti_1p1_client_key': 'KEY',
    'lti_1p1_client_secret': 'SECRET',
    'lti_1p1_launch_url': 'https://localhost',
    'version': 'lti_1p1'
}


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
        if self.USER_TYPE:
            self.user = self.create_user_for_course(self.course, user_type=self.USER_TYPE)

    @property
    def url(self):
        """Returns the discussion API url. """
        return reverse(
            'discussions',
            kwargs={
                'course_key_string': str(self.course.id),
            }
        )

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


class CourseInstructorAuthorizedTest(AuthorizedApiTest):
    """
    Course instructor should have the same access as Global Staff.
    """

    USER_TYPE = CourseUserType.COURSE_INSTRUCTOR


class CourseDiscussionRoleAuthorizedTests(ApiTest):
    """Test cases for discussion api for users with discussion privileges."""

    def setUp(self):
        super().setUp()

        self.course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        self.student_role = RoleFactory(name='Student', course_id=self.course.id)
        self.moderator_role = RoleFactory(name='Moderator', course_id=self.course.id)
        self.community_ta_role = RoleFactory(name='Community TA', course_id=self.course.id)
        self.student_user = UserFactory(password=self.TEST_PASSWORD)
        self.moderator_user = UserFactory(password=self.TEST_PASSWORD)
        self.community_ta_user = UserFactory(password=self.TEST_PASSWORD)
        self.student_role.users.add(self.student_user)
        self.moderator_role.users.add(self.moderator_user)
        self.community_ta_role.users.add(self.community_ta_user)

    def login(self, user):
        """Login the given user."""
        self.client.login(username=user.username, password=self.TEST_PASSWORD)

    def test_student_role_access_get(self):
        """Tests that student role does not have access to the API"""
        self.login(self.student_user)
        response = self._get()
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_student_role_access_post(self):
        """Tests that student role does not have access to the API"""
        self.login(self.student_user)
        response = self._post({})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_moderator_role_access_get(self):
        """Tests that discussion moderator role have access to the API"""
        self.login(self.moderator_user)
        response = self._get()
        assert response.status_code == status.HTTP_200_OK

    def test_moderator_role_access_post(self):
        """Tests that discussion moderator role have access to the API"""
        self.login(self.moderator_user)
        response = self._post({})
        assert response.status_code == status.HTTP_200_OK

    def test_community_ta_role_access_get(self):
        """Tests that discussion community TA role have access to the API"""
        self.login(self.community_ta_user)
        response = self._get()
        assert response.status_code == status.HTTP_200_OK

    def test_community_ta_role_access_post(self):
        """Tests that discussion community TA role have access to the API"""
        self.login(self.community_ta_user)
        response = self._post({})
        assert response.status_code == status.HTTP_200_OK


@ddt.ddt
class DataTest(AuthorizedApiTest):
    """
    Check API-data correctness
    """

    def get(self):
        """Makes a get request and returns json data"""
        response = super()._get()
        return response.json()

    def get_and_assert_defaults(self):
        """
        Assert that course has default discussion configuration
        """
        response = self._get()
        self._assert_defaults(response)

    def _assert_defaults(self, response):
        """
        Check for default values
        """
        data = response.json()
        assert response.status_code == self.expected_response_code
        assert data['enabled'] == DEFAULT_CONFIG_ENABLED
        assert data['provider_type'] == DEFAULT_PROVIDER_TYPE
        assert data['providers']['available']['legacy'] == AVAILABLE_PROVIDER_MAP['legacy']
        assert not [
            name for name, spec in data['providers']['available'].items()
            if "messages" not in spec
        ], "Found available providers without messages field"

        assert data['lti_configuration'] == DEFAULT_LTI_CONFIGURATION
        assert data['plugin_configuration'] == DEFAULT_LEGACY_CONFIGURATION

    def _configure_lti_discussion_provider(self, provider=Provider.PIAZZA):
        """
        Configure an LTI-based discussion provider for a course.
        """
        payload = {
            'enabled': True,
            'provider_type': provider,
            'lti_configuration': DATA_LTI_CONFIGURATION,
            'plugin_configuration': {}
        }
        response = self._post(payload)
        data = response.json()
        assert response.status_code == self.expected_response_code
        return data

    @contextmanager
    def _pii_sharing_for_course(self, enabled):
        instance = CourseAllowPIISharingInLTIFlag.objects.create(course_id=self.course.id, enabled=enabled)
        yield
        instance.delete()

    def test_get_non_configured_provider_for_course(self):
        """
        Tests that if no provider is configured for a course, default configuration
        is returned.
        """
        self.get_and_assert_defaults()

    @ddt.data(
        {"pii_share_username": True},
        {"pii_share_email": True},
        {"pii_share_email": True, "pii_share_username": True},
    )
    def test_post_pii_fields_with_non_configured_pii(self, pii_fields):
        """
        Tests that if PII sharing is not set, user is not able to update
        PII settings for a course.
        """
        data = self._configure_lti_discussion_provider()
        data['lti_configuration'].update(pii_fields)
        response = self._post(data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @ddt.data(
        {"pii_share_username": True},
        {"pii_share_email": True},
        {"pii_share_email": True, "pii_share_username": True},
    )
    def test_post_pii_fields_with_pii_disabled(self, pii_fields):
        """
        Test that when PII sharing is disabled for the course, user is not able
        update PII settings for a course.
        """
        data = self._configure_lti_discussion_provider()
        data['lti_configuration'].update(pii_fields)
        with self._pii_sharing_for_course(enabled=False):
            response = self._post(data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            lti_configuration = self.get()['lti_configuration']
            no_pii_fields_updated = [
                lti_configuration.get(pii_field) != pii_value for pii_field, pii_value in pii_fields.items()
            ]
            assert all(no_pii_fields_updated)

    @ddt.data(
        {"pii_share_username": True},
        {"pii_share_email": True},
        {"pii_share_email": True, "pii_share_username": True},
    )
    def test_post_pii_fields_with_pii_enabled(self, pii_fields):
        """
        Test that when PII sharing is enabled for the course, user is able
        update PII settings for the course.
        """
        data = self._configure_lti_discussion_provider()
        data['lti_configuration'].update(pii_fields)
        with self._pii_sharing_for_course(enabled=True):
            response = self._post(data)
            assert response.status_code == status.HTTP_200_OK

            lti_configuration = self.get()['lti_configuration']
            all_pii_fields_updated = [
                lti_configuration[pii_field] == pii_value for pii_field, pii_value in pii_fields.items()
            ]
            assert all(all_pii_fields_updated)

    @ddt.data(
        True,
        False
    )
    def test_get_pii_fields(self, pii_sharing):
        """
        Tests that when PII sharing is enabled, API included PII info.
        """
        self._configure_lti_discussion_provider()
        with self._pii_sharing_for_course(enabled=pii_sharing):
            data = self.get()
            # If pii_sharing is true, then the fields should be present, and absent otherwise
            assert ('pii_share_email' in data['lti_configuration']) == pii_sharing
            assert ('pii_share_username' in data['lti_configuration']) == pii_sharing

    @ddt.data(
        Provider.ED_DISCUSS,
        Provider.INSCRIBE,
        Provider.PIAZZA,
        Provider.YELLOWDIG,
    )
    def test_post_everything(self, provider):
        """
        API should accept requests to update _all_ fields at once
        """
        data = self._configure_lti_discussion_provider(provider=provider)
        assert data['enabled']
        assert data['provider_type'] == provider
        assert data['providers']['available'][provider] == AVAILABLE_PROVIDER_MAP[provider]
        assert data['plugin_configuration'] == DEFAULT_LEGACY_CONFIGURATION
        assert data['lti_configuration'] == DATA_LTI_CONFIGURATION

        response_data = self.get()
        # the GET should pull back the same data as the POST
        assert response_data == data

    def test_post_invalid_key(self):
        """
        Tests that unsupported keys should be gracefully ignored.
        """
        payload = {
            'non-existent-key': 'value',
        }
        response = self._post(payload)
        assert response.status_code == status.HTTP_200_OK

    @ddt.data(
        Provider.ED_DISCUSS,
        Provider.INSCRIBE,
        Provider.PIAZZA,
        Provider.YELLOWDIG,
    )
    def test_add_valid_configuration(self, provider_type):
        """
        Test that basic configuration is set & retrieved successfully.
        """
        payload = {
            'enabled': True,
            'provider_type': provider_type,
            'plugin_configuration': {
                'key': 'value',
            },
        }
        self._post(payload)

        data = self.get()
        assert data['enabled']
        assert data['provider_type'] == provider_type
        assert data['plugin_configuration'] == DEFAULT_LEGACY_CONFIGURATION

    def test_change_plugin_configuration(self):
        """
        Tests custom config values persist that when changing discussion
        provider from edx provider to other provider.
        """
        payload = {
            'provider_type': Provider.PIAZZA,
            'plugin_configuration': {
                'allow_anonymous': False,
                'custom_field': 'custom_value',
            },
        }
        response = self._post(payload)
        data = response.json()
        assert data['plugin_configuration'] == DEFAULT_LEGACY_CONFIGURATION

        course = self.store.get_course(self.course.id)
        # Only configuration fields not stored in the course, or
        # directly in the model should be stored here.
        assert course.discussions_settings['piazza'] == {'custom_field': 'custom_value'}

    @ddt.data(
        {'enabled': 3},
    )
    def test_configuration_invalid(self, payload):
        """
        Test that invalid data raises validation error.
        """
        response = self._post(payload)
        assert status.is_client_error(response.status_code)

        errors = response.json()
        assert 'enabled' in errors
        self.get_and_assert_defaults()

    @ddt.data(
        *DATA_LTI_CONFIGURATION.items()
    )
    @ddt.unpack
    def test_post_lti_valid(self, key, value):
        """
        Test that we can set & retrieve LTI configuration.
        """
        provider_type = 'piazza'
        payload = {
            'enabled': True,
            'provider_type': provider_type,
            'lti_configuration': {
                key: value,
            }
        }
        self._post(payload)
        data = self.get()
        assert data['enabled']
        assert data['provider_type'] == provider_type
        assert data['lti_configuration'][key] == value

    def test_post_lti_invalid(self):
        """
        Check validation of LTI configuration ignores unsupported values.

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
            assert response.status_code == status.HTTP_200_OK
            data = self.get()
            assert data['enabled']
            assert data['provider_type'] == provider_type
            assert data['lti_configuration'][key] == value
            assert 'ignored-key' not in data['lti_configuration']

    def test_post_legacy_valid(self):
        """
        Test that we can set & retrieve edx provider configuration.
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
            data = self.get()
            assert data['enabled']
            assert data['provider_type'] == provider_type
            assert data['plugin_configuration'][key] == value

    @ddt.data(
        {'allow_anonymous': 3},
        {'allow_anonymous_to_peers': 3},
        {'discussion_blackouts': 3},
        {'discussion_topics': 3},
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
        self.get_and_assert_defaults()

    @ddt.data(*DATA_LEGACY_COHORTS.items())
    @ddt.unpack
    def test_post_cohorts_valid(self, key, value):
        """
        Test that we can set & retrieve legacy cohorts configuration.
        """
        provider_type = 'legacy'
        payload = {
            'enabled': True,
            'provider_type': provider_type,
            'plugin_configuration': {
                key: value,
            }
        }
        self._post(payload)
        data = self.get()
        assert data['enabled']
        assert data['provider_type'] == provider_type
        assert data['plugin_configuration'][key] == value

    @ddt.data(*DATA_LEGACY_COHORTS.items())
    @ddt.unpack
    def test_post_cohorts_invalid(self, key, value):
        """
        Check validation of legacy cohorts configuration
        """
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
        self.get_and_assert_defaults()

    def test_change_to_lti(self):
        """
        Test that switching to an LTI-backed provider from a default provider works as expected.

        When switching provider to LTI, the API should return both LTI & legacy data.
        """
        payload = {
            'enabled': True,
            'provider_type': 'legacy',
            'plugin_configuration': {
                'allow_anonymous': False,
            },
        }
        self._post(payload)
        self._configure_lti_discussion_provider(provider=Provider.ED_DISCUSS)
        data = self.get()

        assert data['enabled']
        assert data['provider_type'] == Provider.ED_DISCUSS
        assert data['plugin_configuration'] == {
            **DEFAULT_LEGACY_CONFIGURATION,
            'allow_anonymous': False,
        }
        assert data['lti_configuration'] == DATA_LTI_CONFIGURATION

    def test_change_from_lti(self):
        """
        Test that switching from an LTI-backed provider to a non-LTI provider works as expected.

        When switching provider to LTI, the API should return both LTI & legacy data.
        """
        self._configure_lti_discussion_provider()
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

    @ddt.data(
        *itertools.product(
            ["enable_in_context", "enable_graded_units", "unit_level_visibility"],
            [True, False],
        ),
        ("provider_type", "piazza"),
    )
    @ddt.unpack
    def test_change_course_fields(self, field, value):
        """
        Test changing fields that are saved to the course
        """
        payload = {
            field: value
        }
        response = self._post(payload)
        data = response.json()
        assert data[field] == value
        course = self.store.get_course(self.course.id)
        assert course.discussions_settings[field] == value

    @ddt.data(*[
        user_type.name for user_type in CourseUserType
        if user_type not in {  # pylint: disable=undefined-variable
            CourseUserType.ANONYMOUS,
            CourseUserType.GLOBAL_STAFF
        }
    ])
    def test_unable_to_change_provider_for_running_course(self, user_type):
        """
        Ensure that certain users cannot change provider for a running course.
        """
        self.course.start = datetime.now(timezone.utc) - timedelta(days=5)
        self.course = self.update_course(self.course, self.user.id)

        # use the global staff user to do the initial config
        # so we're sure to not get permissions errors
        response = self._post({
            'enabled': True,
            'provider_type': 'legacy',
        })
        assert response.status_code == status.HTTP_200_OK

        self.create_user_for_course(self.course, CourseUserType[user_type])

        response = self._post({
            'enabled': True,
            'provider_type': 'piazza',
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_global_staff_can_change_provider_for_running_course(self):
        """
        Ensure that global staff can change provider for a running course.
        """
        self.course.start = datetime.now(timezone.utc) - timedelta(days=5)
        self.course = self.update_course(self.course, self.user.id)

        # use the global staff user to do the initial config
        # so we're sure to not get permissions errors
        response = self._post({
            'enabled': True,
            'provider_type': 'legacy',
        })
        assert response.status_code == status.HTTP_200_OK

        response = self._post({
            'enabled': True,
            'provider_type': 'piazza',
        })
        assert response.status_code == status.HTTP_200_OK
