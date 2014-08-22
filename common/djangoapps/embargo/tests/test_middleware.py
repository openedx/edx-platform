"""
Tests for EmbargoMiddleware
"""

import mock
import pygeoip
import unittest

from django.conf import settings
from django.test import TestCase, Client
from django.test.utils import override_settings
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory

# Explicitly import the cache from ConfigurationModel so we can reset it after each test
from config_models.models import cache
from embargo.models import EmbargoedCourse, EmbargoedState, IPFilter


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
        self.embargoed_page = '/courses/' + self.embargo_course.id.to_deprecated_string() + '/info'
        self.regular_page = '/courses/' + self.regular_course.id.to_deprecated_string() + '/info'
        EmbargoedCourse(course_id=self.embargo_course.id, embargoed=True).save()
        EmbargoedState(
            embargoed_countries="cu, ir, Sy, SD",
            changed_by=self.user,
            enabled=True
        ).save()
        CourseEnrollment.enroll(self.user, self.regular_course.id)
        CourseEnrollment.enroll(self.user, self.embargo_course.id)
        # Text from lms/templates/static_templates/embargo.html
        self.embargo_text = "Unfortunately, at this time edX must comply with export controls, and we cannot allow you to access this particular course."

        self.patcher = mock.patch.object(pygeoip.GeoIP, 'country_code_by_addr', self.mock_country_code_by_addr)
        self.patcher.start()

    def tearDown(self):
        # Explicitly clear ConfigurationModel's cache so tests have a clear cache
        # and don't interfere with each other
        cache.clear()
        self.patcher.stop()

    def mock_country_code_by_addr(self, ip_addr):
        """
        Gives us a fake set of IPs
        """
        ip_dict = {
            '1.0.0.0': 'CU',
            '2.0.0.0': 'IR',
            '3.0.0.0': 'SY',
            '4.0.0.0': 'SD',
            '5.0.0.0': 'AQ',  # Antartica
            '2001:250::': 'CN',
            '2001:1340::': 'CU',
        }
        return ip_dict.get(ip_addr, 'US')

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_countries(self):
        # Accessing an embargoed page from a blocked IP should cause a redirect
        response = self.client.get(self.embargoed_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
        self.assertEqual(response.status_code, 302)
        # Following the redirect should give us the embargo page
        response = self.client.get(
            self.embargoed_page,
            HTTP_X_FORWARDED_FOR='1.0.0.0',
            REMOTE_ADDR='1.0.0.0',
            follow=True
        )
        self.assertIn(self.embargo_text, response.content)

        # Accessing a regular page from a blocked IP should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
        self.assertEqual(response.status_code, 200)

        # Accessing an embargoed page from a non-embargoed IP should succeed
        response = self.client.get(self.embargoed_page, HTTP_X_FORWARDED_FOR='5.0.0.0', REMOTE_ADDR='5.0.0.0')
        self.assertEqual(response.status_code, 200)

        # Accessing a regular page from a non-embargoed IP should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='5.0.0.0', REMOTE_ADDR='5.0.0.0')
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_countries_ipv6(self):
        # Accessing an embargoed page from a blocked IP should cause a redirect
        response = self.client.get(self.embargoed_page, HTTP_X_FORWARDED_FOR='2001:1340::', REMOTE_ADDR='2001:1340::')
        self.assertEqual(response.status_code, 302)
        # Following the redirect should give us the embargo page
        response = self.client.get(
            self.embargoed_page,
            HTTP_X_FORWARDED_FOR='2001:1340::',
            REMOTE_ADDR='2001:1340::',
            follow=True
        )
        self.assertIn(self.embargo_text, response.content)

        # Accessing a regular page from a blocked IP should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='2001:1340::', REMOTE_ADDR='2001:1340::')
        self.assertEqual(response.status_code, 200)

        # Accessing an embargoed page from a non-embargoed IP should succeed
        response = self.client.get(self.embargoed_page, HTTP_X_FORWARDED_FOR='2001:250::', REMOTE_ADDR='2001:250::')
        self.assertEqual(response.status_code, 200)

        # Accessing a regular page from a non-embargoed IP should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='2001:250::', REMOTE_ADDR='2001:250::')
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_ip_exceptions(self):
        # Explicitly whitelist/blacklist some IPs
        IPFilter(
            whitelist='1.0.0.0',
            blacklist='5.0.0.0',
            changed_by=self.user,
            enabled=True
        ).save()

        # Accessing an embargoed page from a blocked IP that's been whitelisted
        #  should succeed
        response = self.client.get(self.embargoed_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
        self.assertEqual(response.status_code, 200)

        # Accessing a regular course from a blocked IP that's been whitelisted should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
        self.assertEqual(response.status_code, 200)

        # Accessing an embargoed course from non-embargoed IP that's been blacklisted
        #  should cause a redirect
        response = self.client.get(self.embargoed_page, HTTP_X_FORWARDED_FOR='5.0.0.0', REMOTE_ADDR='5.0.0.0')
        self.assertEqual(response.status_code, 302)
        # Following the redirect should give us the embargo page
        response = self.client.get(
            self.embargoed_page,
            HTTP_X_FORWARDED_FOR='5.0.0.0',
            REMOTE_ADDR='1.0.0.0',
            follow=True
        )
        self.assertIn(self.embargo_text, response.content)

        # Accessing a regular course from a non-embargoed IP that's been blacklisted should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='5.0.0.0', REMOTE_ADDR='5.0.0.0')
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_ip_network_exceptions(self):
        # Explicitly whitelist/blacklist some IP networks
        IPFilter(
            whitelist='1.0.0.1/24',
            blacklist='5.0.0.0/16,1.1.0.0/24',
            changed_by=self.user,
            enabled=True
        ).save()

        # Accessing an embargoed page from a blocked IP that's been whitelisted with a network
        # should succeed
        response = self.client.get(self.embargoed_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
        self.assertEqual(response.status_code, 200)

        # Accessing a regular course from a blocked IP that's been whitelisted with a network
        # should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
        self.assertEqual(response.status_code, 200)

        # Accessing an embargoed course from non-embargoed IP that's been blacklisted with a network
        #  should cause a redirect
        response = self.client.get(self.embargoed_page, HTTP_X_FORWARDED_FOR='5.0.0.100', REMOTE_ADDR='5.0.0.100')
        self.assertEqual(response.status_code, 302)
        # Following the redirect should give us the embargo page
        response = self.client.get(
            self.embargoed_page,
            HTTP_X_FORWARDED_FOR='5.0.0.100',
            REMOTE_ADDR='5.0.0.100',
            follow=True
        )
        self.assertIn(self.embargo_text, response.content)

        # Accessing an embargoed course from non-embargoed IP that's been blaclisted with a network
        # should cause a redirect
        response = self.client.get(self.embargoed_page, HTTP_X_FORWARDED_FOR='1.1.0.1', REMOTE_ADDR='1.1.0.1')
        self.assertEqual(response.status_code, 302)
        # Following the redirect should give us the embargo page
        response = self.client.get(
            self.embargoed_page,
            HTTP_X_FORWARDED_FOR='1.1.0.0',
            REMOTE_ADDR='1.1.0.0',
            follow=True
        )
        self.assertIn(self.embargo_text, response.content)

        # Accessing an embargoed from a blocked IP that's not blacklisted by the network rule.
        # should succeed
        response = self.client.get(self.embargoed_page, HTTP_X_FORWARDED_FOR='1.1.1.0', REMOTE_ADDR='1.1.1.0')
        self.assertEqual(response.status_code, 200)

        # Accessing a regular course from a non-embargoed IP that's been blacklisted
        # should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='5.0.0.0', REMOTE_ADDR='5.0.0.0')
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @mock.patch.dict(settings.FEATURES, {'EMBARGO': False})
    def test_countries_embargo_off(self):
        # When the middleware is turned off, all requests should go through
        # Accessing an embargoed page from a blocked IP OK
        response = self.client.get(self.embargoed_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
        self.assertEqual(response.status_code, 200)

        # Accessing a regular page from a blocked IP should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
        self.assertEqual(response.status_code, 200)

        # Explicitly whitelist/blacklist some IPs
        IPFilter(
            whitelist='1.0.0.0',
            blacklist='5.0.0.0',
            changed_by=self.user,
            enabled=True
        ).save()

        # Accessing an embargoed course from non-embargoed IP that's been blacklisted
        #  should be OK
        response = self.client.get(self.embargoed_page, HTTP_X_FORWARDED_FOR='5.0.0.0', REMOTE_ADDR='5.0.0.0')
        self.assertEqual(response.status_code, 200)

        # Accessing a regular course from a non-embargoed IP that's been blacklisted should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='5.0.0.0', REMOTE_ADDR='5.0.0.0')
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @mock.patch.dict(settings.FEATURES, {'EMBARGO': False, 'SITE_EMBARGOED': True})
    def test_embargo_off_embargo_site_on(self):
        # When the middleware is turned on with SITE, main site access should be restricted
        # Accessing a regular page from a blocked IP is denied.
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
        self.assertEqual(response.status_code, 403)

        # Accessing a regular page from a non blocked IP should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='5.0.0.0', REMOTE_ADDR='5.0.0.0')
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @mock.patch.dict(settings.FEATURES, {'EMBARGO': False, 'SITE_EMBARGOED': True})
    @override_settings(EMBARGO_SITE_REDIRECT_URL='https://www.edx.org/')
    def test_embargo_off_embargo_site_on_with_redirect_url(self):
        # When the middleware is turned on with SITE_EMBARGOED, main site access
        # should be restricted. Accessing a regular page from a blocked IP is
        # denied, and redirected to EMBARGO_SITE_REDIRECT_URL rather than returning a 403.
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
        self.assertEqual(response.status_code, 302)
