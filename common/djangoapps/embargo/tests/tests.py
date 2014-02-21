"""
Tests for EmbargoMiddleware
"""

from xmodule.modulestore.tests.factories import CourseFactory
from django.test import TestCase
from django.test.utils import override_settings
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from embargo.models import EmbargoConfig
from django.test import Client
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
import mock
import pygeoip


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class EmbargoMiddlewareTests(TestCase):
    """
    Tests of EmbargoMiddleware
    """
    def setUp(self):
        self.client = Client()
        self.user = UserFactory(username='fred', password='secret')
        self.client.login(username='fred', password='secret')
        self.embargo_course = CourseFactory.create()
        self.embargo_course.save()
        self.regular_course = CourseFactory.create(org="Regular")
        self.regular_course.save()
        self.embargoed_page = '/courses/' + self.embargo_course.id + '/info'
        self.regular_page = '/courses/' + self.regular_course.id + '/info'
        EmbargoConfig(
            embargoed_countries="CU, IR, SY,SD",
            embargoed_courses=self.embargo_course.id,
            changed_by=self.user,
            enabled=True
        ).save()

        CourseEnrollment.enroll(self.user, self.regular_course.id)
        CourseEnrollment.enroll(self.user, self.embargo_course.id)

    def test_countries(self):
        def mock_country_code_by_addr(ip):
            """
            Gives us a fake set of IPs
            """
            ip_dict = {
                '1.0.0.0': 'CU',
                '2.0.0.0': 'IR',
                '3.0.0.0': 'SY',
                '4.0.0.0': 'SD',
            }
            return ip_dict.get(ip, 'US')

        with mock.patch.object(pygeoip.GeoIP, 'country_code_by_addr') as mocked_method:
            mocked_method.side_effect = mock_country_code_by_addr

            # Accessing an embargoed page from a blocked IP should cause a redirect
            response = self.client.get(self.embargoed_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
            self.assertEqual(response.status_code, 302)

            # Accessing a regular course from a blocked IP should succeed
            response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
            self.assertEqual(response.status_code, 404)

            # Accessing any course from non-embaroged IPs should succeed
            response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='5.0.0.0', REMOTE_ADDR='5.0.0.0')
            self.assertEqual(response.status_code, 404)

            response = self.client.get(self.embargoed_page, HTTP_X_FORWARDED_FOR='5.0.0.0', REMOTE_ADDR='5.0.0.0')
            self.assertEqual(response.status_code, 404)
