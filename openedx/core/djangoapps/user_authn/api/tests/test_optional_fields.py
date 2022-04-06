"""
Tests for OptionalFieldsData View
"""
from django.conf import settings
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration
from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory


@skip_unless_lms
class OptionalFieldsDataViewTest(APITestCase):
    """
    Tests for the end-point that returns optional fields.
    """

    def setUp(self):
        super().setUp()

        self.user = UserFactory.create(username='test_user', password='password123')
        self.client.force_authenticate(user=self.user)
        self.url = reverse('optional_fields')

    def test_unauthenticated_request_is_forbidden(self):
        """
        Test that unauthenticated user should not be able to access the endpoint.
        """
        self.client.logout()
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @override_settings(REGISTRATION_EXTRA_FIELDS={"goals": "required", "level_of_education": "required"})
    def test_optional_fields_not_configured(self):
        """
        Test that when no optional fields are configured in REGISTRATION_EXTRA_FIELDS
        settings, then API returns proper response.
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get('error_code') == 'optional_fields_configured_incorrectly'

    @override_settings(REGISTRATION_EXTRA_FIELDS={"new_field_with_no_description": "optional", "goals": "optional"})
    def test_optional_field_has_no_description(self):
        """
        Test that if a new optional field is added to REGISTRATION_EXTRA_FIELDS without
        adding field description then that field is omitted from the final response.
        """
        expected_response = {
            'goals': {
                'name': 'goals',
                'type': 'textarea',
                'label': "Tell us why you're interested in {platform_name}".format(
                    platform_name=settings.PLATFORM_NAME
                ),
                'error_message': '',
            }
        }
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('fields') == expected_response

    @with_site_configuration(
        configuration={
            'EXTRA_FIELD_OPTIONS': {'profession': ['Software Engineer', 'Teacher', 'Other']}
        }
    )
    @override_settings(REGISTRATION_EXTRA_FIELDS={'profession': 'optional', 'specialty': 'optional'})
    def test_configurable_select_option_fields(self):
        """
        Test that if optional fields have configurable options present in EXTRA_FIELD_OPTIONS,
        they are returned in response as "select" fields otherwise as "text" field.
        """
        expected_response = {
            'profession': {
                'name': 'profession',
                'label': 'Profession',
                'error_message': '',
                'type': 'select',
                'options': [('software engineer', 'Software Engineer'), ('teacher', 'Teacher'), ('other', 'Other')],
            },
            'specialty': {
                'name': 'specialty',
                'label': 'Specialty',
                'error_message': '',
                'type': 'text',
            }
        }
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('fields') == expected_response

    @override_settings(
        REGISTRATION_EXTRA_FIELDS={'goals': 'optional', 'specialty': 'optional'},
        REGISTRATION_FIELD_ORDER=['specialty', 'goals'],
    )
    def test_field_order(self):
        """
        Test that order of fields
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert list(response.data['fields'].keys()) == ['specialty', 'goals']
