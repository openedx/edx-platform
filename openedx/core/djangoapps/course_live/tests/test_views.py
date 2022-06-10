"""
Test for course live app views
"""
import json

from django.urls import reverse
from lti_consumer.models import CourseAllowPIISharingInLTIFlag
from rest_framework.test import APITestCase
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import CourseUserType, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..models import AVAILABLE_PROVIDERS, CourseLiveConfiguration


class TestCourseLiveConfigurationView(ModuleStoreTestCase, APITestCase):
    """
    Unit tests for the CourseLiveConfigurationView.
    """
    password = 'test'

    def setUp(self):
        super().setUp()
        store = ModuleStoreEnum.Type.split
        self.course = CourseFactory.create(default_store=store)
        self.user = self.create_user_for_course(self.course, user_type=CourseUserType.GLOBAL_STAFF)

    @property
    def url(self):
        """Returns the course live API url. """
        return reverse(
            'course_live', kwargs={'course_id': str(self.course.id)}
        )

    def _get(self):
        return self.client.get(self.url)

    def _post(self, data):
        return self.client.post(self.url, data, format='json')

    def create_course_live_config(self):
        """
        creates a courseLiveConfiguration
        """
        CourseAllowPIISharingInLTIFlag.objects.create(course_id=self.course.id, enabled=True)
        lti_config = {
            'lti_1p1_client_key': 'this_is_key',
            'lti_1p1_client_secret': 'this_is_secret',
            'lti_1p1_launch_url': 'example.com',
            'lti_config': {
                'additional_parameters': {
                    'custom_instructor_email': "email@example.com"
                }
            },
        }
        course_live_config_data = {
            'enabled': True,
            'provider_type': 'zoom',
            'lti_configuration': lti_config
        }
        response = self._post(course_live_config_data)
        return lti_config, course_live_config_data, response

    def test_pii_sharing_not_allowed(self):
        """
        Test response if PII sharing is not allowed
        """
        response = self._get()
        self.assertEqual(response.status_code, 200)
        expected_data = {'pii_sharing_allowed': False, 'message': 'PII sharing is not allowed on this course'}
        self.assertEqual(response.data, expected_data)

    def test_pii_sharing_is_allowed(self):
        """
        Test response if PII sharing is  allowed
        """
        CourseAllowPIISharingInLTIFlag.objects.create(course_id=self.course.id, enabled=True)
        response = self._get()
        self.assertEqual(response.status_code, 200)
        expected_data = {
            'enabled': True,
            'course_key': None,
            'pii_sharing_allowed': True,
            'lti_configuration': {
                'lti_1p1_client_key': '',
                'lti_1p1_client_secret': '',
                'lti_1p1_launch_url': '',
                'lti_config': {},
                'version': 'lti_1p1'
            },
            'provider_type': ''
        }
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content, expected_data)

    def test_create_configurations_data(self):
        """
        Create and test courseLiveConfiguration data in database
        """
        lti_config, data, response = self.create_course_live_config()
        course_live_configurations = CourseLiveConfiguration.get(self.course.id)
        lti_configuration = CourseLiveConfiguration.get(self.course.id).lti_configuration

        self.assertEqual(self.course.id, course_live_configurations.course_key)
        self.assertEqual(data['enabled'], course_live_configurations.enabled)
        self.assertEqual(data['provider_type'], course_live_configurations.provider_type)

        self.assertEqual(lti_config['lti_1p1_client_key'], lti_configuration.lti_1p1_client_key)
        self.assertEqual(lti_config['lti_1p1_client_secret'], lti_configuration.lti_1p1_client_secret)
        self.assertEqual(lti_config['lti_1p1_launch_url'], lti_configuration.lti_1p1_launch_url)
        self.assertEqual({
            'pii_share_username': True,
            'pii_share_email': True,
            'additional_parameters': {'custom_instructor_email': 'email@example.com'}
        }, lti_configuration.lti_config)

        self.assertEqual(response.status_code, 200)

    def test_create_configurations_response(self):
        """
        Create and test POST request response data
        """
        lti_config, course_live_config_data, response = self.create_course_live_config()
        expected_data = {
            'course_key': str(self.course.id),
            'enabled': True,
            'pii_sharing_allowed': True,
            'provider_type': 'zoom',
            'lti_configuration': {
                'lti_1p1_client_key': 'this_is_key',
                'lti_1p1_client_secret': 'this_is_secret',
                'lti_1p1_launch_url': 'example.com',
                'version': 'lti_1p1',
                'lti_config': {
                    'pii_share_email': True,
                    'pii_share_username': True,
                    'additional_parameters': {
                        'custom_instructor_email': 'email@example.com'
                    },
                },
            },
        }
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(content, expected_data)

    def test_post_error_messages(self):
        """
        Test all related validation messages are recived
        """
        CourseAllowPIISharingInLTIFlag.objects.create(course_id=self.course.id, enabled=True)
        response = self._post({})
        content = json.loads(response.content.decode('utf-8'))
        expected_data = {
            'provider_type': ['This field is required.'],
            'lti_configuration': ['This field is required.']
        }
        self.assertEqual(content, expected_data)
        self.assertEqual(response.status_code, 400)


class TestCourseLiveProvidersView(ModuleStoreTestCase, APITestCase):
    """
    Tests for course live provider view
    """

    def setUp(self):
        super().setUp()
        store = ModuleStoreEnum.Type.split
        self.course = CourseFactory.create(default_store=store)
        self.user = self.create_user_for_course(self.course, user_type=CourseUserType.GLOBAL_STAFF)

    @property
    def url(self):
        """
        Returns the live providers API url.
        """
        return reverse(
            'live_providers', kwargs={'course_id': str(self.course.id)}
        )

    def test_response_has_correct_data(self):
        expected_data = {
            'providers': {
                'active': '',
                'available': AVAILABLE_PROVIDERS
            }
        }
        response = self.client.get(self.url)
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content, expected_data)
