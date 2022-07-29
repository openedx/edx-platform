"""
Save for later tests
"""

from unittest.mock import patch, MagicMock

import ddt
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from django.test.utils import override_settings
from rest_framework.test import APITestCase
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.third_party_auth.tests.testutil import ThirdPartyAuthTestMixin
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.catalog.tests.factories import ProgramFactory


@skip_unless_lms
@ddt.ddt
class CourseSaveForLaterApiViewTest(ThirdPartyAuthTestMixin, APITestCase):
    """
    Tests for CourseSaveForLaterApiView
    """

    def setUp(self):  # pylint: disable=arguments-differ
        """
        Test Setup
        """
        super().setUp()

        self.api_url = reverse('api:v1:save_course')
        self.email = 'test@edx.org'
        self.invalid_email = 'test@edx'
        self.course_id = 'course-v1:TestX+ProEnroll+P'
        self.org_img_url = '/path/logo.png'
        self.course_key = CourseKey.from_string(self.course_id)
        CourseOverviewFactory.create(id=self.course_key)

    @override_settings(
        EDX_BRAZE_API_KEY='test-key',
        EDX_BRAZE_API_SERVER='http://test.url'
    )
    @patch('lms.djangoapps.utils.BrazeClient', MagicMock())
    def test_save_course_using_email(self):
        """
        Test successfully email sent
        """
        request_payload = {
            'email': self.email,
            'course_id': self.course_id,
            'marketing_url': 'http://google.com',
            'org_img_url': self.org_img_url,
        }
        response = self.client.post(self.api_url, data=request_payload)
        assert response.status_code == 200

    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'registration_proxy',
            }
        }
    )
    def test_save_course_api_rate_limiting(self):
        """
        Test api rate limit
        """
        request_payload = {
            'email': self.email,
            'course_id': self.course_id,
            'marketing_url': 'http://google.com',
            'org_img_url': self.org_img_url,
        }
        for _ in range(int(settings.SAVE_FOR_LATER_EMAIL_RATE_LIMIT.split('/')[0])):
            response = self.client.post(self.api_url, data=request_payload)
            assert response.status_code != 403

        response = self.client.post(self.api_url, data=request_payload)
        assert response.status_code == 403
        cache.clear()

        for _ in range(int(settings.SAVE_FOR_LATER_IP_RATE_LIMIT.split('/')[0])):
            request_payload['email'] = 'test${_}@edx.org'.format(_=_)
            response = self.client.post(self.api_url, data=request_payload)
            assert response.status_code != 403

        response = self.client.post(self.api_url, data=request_payload)
        assert response.status_code == 403
        cache.clear()

    def test_invalid_email_address(self):
        """
        Test email validation
        """
        request_payload = {'email': self.invalid_email, 'course_id': self.course_id}
        response = self.client.post(self.api_url, data=request_payload)
        assert response.status_code == 400


@skip_unless_lms
@ddt.ddt
class ProgramSaveForLaterApiViewTest(ThirdPartyAuthTestMixin, APITestCase):
    """
    Tests for ProgramSaveForLaterApiView
    """

    def setUp(self):  # pylint: disable=arguments-differ
        """
        Test Setup
        """
        super().setUp()

        self.api_url = reverse('api:v1:save_program')
        self.email = 'test@edx.org'
        self.invalid_email = 'test@edx'
        self.uuid = '587f6abe-bfa4-4125-9fbe-4789bf3f97f1'
        self.program = ProgramFactory(uuid=self.uuid)

    @override_settings(
        EDX_BRAZE_API_KEY='test-key',
        EDX_BRAZE_API_SERVER='http://test.url'
    )
    @patch('lms.djangoapps.utils.BrazeClient', MagicMock())
    @patch('lms.djangoapps.save_for_later.api.v1.views.get_programs')
    def test_save_program_using_email(self, mock_get_programs):
        """
        Test successfully email sent
        """
        mock_get_programs.return_value = self.program
        request_payload = {
            'email': self.email,
            'program_uuid': self.uuid,
        }
        response = self.client.post(self.api_url, data=request_payload)
        assert response.status_code == 200

    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'registration_proxy',
            }
        }
    )
    def test_save_program_api_rate_limiting(self):
        """
        Test api rate limit
        """
        request_payload = {
            'email': self.email,
            'program_uuid': self.uuid,
        }
        for _ in range(int(settings.SAVE_FOR_LATER_EMAIL_RATE_LIMIT.split('/')[0])):
            response = self.client.post(self.api_url, data=request_payload)
            assert response.status_code != 403

        response = self.client.post(self.api_url, data=request_payload)
        assert response.status_code == 403
        cache.clear()

        for _ in range(int(settings.SAVE_FOR_LATER_IP_RATE_LIMIT.split('/')[0])):
            request_payload['email'] = 'test${_}@edx.org'.format(_=_)
            response = self.client.post(self.api_url, data=request_payload)
            assert response.status_code != 403

        response = self.client.post(self.api_url, data=request_payload)
        assert response.status_code == 403
        cache.clear()

    def test_invalid_email_address(self):
        """
        Test email validation
        """
        request_payload = {'email': self.invalid_email, 'program_uuid': self.uuid}
        response = self.client.post(self.api_url, data=request_payload)
        assert response.status_code == 400
