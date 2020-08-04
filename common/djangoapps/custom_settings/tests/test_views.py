from datetime import datetime
from json import dumps

from django.http import HttpResponse
from django.urls import reverse
from mock import Mock, patch
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_405_METHOD_NOT_ALLOWED

from custom_settings.models import CustomSettings
from custom_settings.tests.factories import CustomSettingsFactory
from openedx.features.philu_utils.tests.mixins import PhiluThemeMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class CustomSettingsTestCase(PhiluThemeMixin, ModuleStoreTestCase):

    def setUp(self):
        super(CustomSettingsTestCase, self).setUp()
        self.client.login(username=self.user.username, password=self.user_password)
        self.course = CourseFactory.create(
            org='test',
            course='mth',
            run='101',
            enrollment_start=datetime(2013, 1, 1),
            enrollment_end=datetime(2014, 1, 1),
            start=datetime(2013, 1, 1),
            end=datetime(2030, 1, 1),
            emit_signals=True,
        )
        course_id = 'course-v1:test+mth+101'
        self.course_key = CourseKey.from_string(course_id)
        self.url = reverse('custom_settings', kwargs={'course_key_string': course_id})
        CustomSettingsFactory(id=self.course_key, tags='tag1, tag2', course_short_id=200)

    @patch('custom_settings.views.get_course_and_check_access', Mock())
    def test_course_custom_settings_course_settings_dose_not_exist(self):
        """Assert that view throws 400 status code when settings are fetched for a course which does not exist"""
        url = reverse('custom_settings', kwargs={'course_key_string': 'course-v1:test+test+123'})
        self.assertEqual(self.client.get(url, HTTP_ACCEPT='text/html').status_code, HTTP_400_BAD_REQUEST)

    @patch('custom_settings.views.render_to_response')
    @patch('custom_settings.views.get_course_and_check_access')
    @patch('custom_settings.views.get_course_open_date_from_settings')
    def test_course_custom_settings_get_request(self, mock_get_course_open_date_from_settings,
                                                mock_get_course_and_check_access,
                                                mock_render_to_response):
        """Assert that page shows custom settings successfully"""
        mock_get_course_open_date_from_settings.return_value = '01/01/2020'
        mock_get_course_and_check_access.return_value = 'test_value'
        mock_render_to_response.return_value = HttpResponse()
        self.client.get(self.url, HTTP_ACCEPT='text/html')

        expected_context = {
            'custom_settings_url': self.url,
            'custom_dict': {
                'enable_enrollment_email': True,
                'tags': u'tag1, tag2',
                'is_featured': False,
                'show_grades': True,
                'auto_enroll': False,
                'seo_tags': {u'description': u'test', u'title': u'test'},
                'course_open_date': '01/01/2020'
            },
            'context_course': 'test_value',
            'course_short_id': 200
        }

        mock_render_to_response.assert_called_once_with('custom_settings.html', expected_context)

    @patch('custom_settings.views.validate_course_open_date')
    @patch('custom_settings.views.get_course_and_check_access', Mock())
    def test_course_custom_settings_post_request(self, mock_validate_course_open_date):
        """Assert that page accepts custom settings from user and saves them successfully"""
        mock_validate_course_open_date.return_value = datetime(2020, 02, 02, tzinfo=UTC)
        custom_settings_data = {
            'tags': u'tag2, tag3',
            'is_featured': True,
            'show_grades': False,
            'course_open_date': '01/01/2020',
            'seo_tags': {u'description': u'test', u'title': u'test'},
            'auto_enroll': True,
            'enable_enrollment_email': True,
        }
        response = self.client.post(
            self.url,
            data=dumps(custom_settings_data),
            content_type='application/json',
            HTTP_ACCEPT='application/json'
        )

        custom_settings = CustomSettings.objects.get(id=self.course_key)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(custom_settings.tags, 'tag2, tag3')
        self.assertEqual(custom_settings.is_featured, True)
        self.assertEqual(custom_settings.show_grades, False)
        self.assertEqual(custom_settings.course_open_date, datetime(2020, 02, 02, tzinfo=UTC))
        self.assertEqual(custom_settings.seo_tags, '{"description": "test", "title": "test"}')
        self.assertEqual(custom_settings.auto_enroll, True)
        self.assertEqual(custom_settings.enable_enrollment_email, True)

    @patch('custom_settings.views.get_course_and_check_access', Mock())
    def test_course_custom_settings_delete_request(self):
        """Assert that http delete request is not allowed"""
        response = self.client.delete(self.url, content_type='application/json', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
