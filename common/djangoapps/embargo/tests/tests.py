"""
Tests for EmbargoMiddleware
"""

from django.contrib.auth.models import User
from xmodule.modulestore.tests.factories import CourseFactory
from django.test import RequestFactory
from django.test import TestCase
from django.test.utils import override_settings
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from embargo.models import EmbargoConfig
from courseware.views import course_info
from django.test import Client
import mock
import pygeoip


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class EmbargoMiddlewareTests(TestCase):
    """
    Tests of EmbargoMiddleware
    """
    def setUp(self):
        self.client = Client()
        self.user = User()
        self.client.login(username='fred', password='secret')
        self.course = CourseFactory.create()
        self.course.save()
        self.page = '/courses/' + self.course.id + '/info'
        EmbargoConfig(
            embargoed_countries="CU, IR, SY,SD",
            embargoed_courses=self.course.id,
            changed_by=self.user,
            enabled=True
        ).save()


    def test_countries(self):
        def mock_country_code_by_addr(ip):
            ip_dict = {
                '1.0.0.0': 'CU',
                '2.0.0.0': 'IR',
                '3.0.0.0': 'SY',
                '4.0.0.0': 'SD',
            }
            return ip_dict.get(ip, 'US')

        with mock.patch.object(pygeoip.GeoIP, 'country_code_by_addr') as mocked_method:
            mocked_method.side_effect = mock_country_code_by_addr
            response = self.client.get(self.page, HTTP_X_FORWADED_FOR='0.0.0.0')
            self.assertEqual(response.status_code, 200)
