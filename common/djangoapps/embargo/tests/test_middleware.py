"""
Tests for EmbargoMiddleware
"""

import mock
import pygeoip
import unittest

from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import connection, transaction
from django.test.utils import override_settings
import ddt

from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase, mixed_store_config
)

# Explicitly import the cache from ConfigurationModel so we can reset it after each test
from config_models.models import cache
from embargo.models import EmbargoedCourse, EmbargoedState, IPFilter


# Since we don't need any XML course fixtures, use a modulestore configuration
# that disables the XML modulestore.
MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)

@ddt.ddt
@override_settings(MODULESTORE=MODULESTORE_CONFIG)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EmbargoMiddlewareTests(ModuleStoreTestCase):
    """
    Tests of EmbargoMiddleware
    """
    def setUp(self):
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

    @ddt.data(
        (None, False),
        ("", False),
        ("us", False),
        ("CU", True),
        ("Ir", True),
        ("sy", True),
        ("sd", True)
    )
    @ddt.unpack
    def test_embargo_profile_country(self, profile_country, is_embargoed):
        # Set the country in the user's profile
        profile = self.user.profile
        profile.country = profile_country
        profile.save()

        # Attempt to access an embargoed course
        response = self.client.get(self.embargoed_page)

        # If the user is from an embargoed country, verify that
        # they are redirected to the embargo page.
        if is_embargoed:
            embargo_url = reverse('embargo')
            self.assertRedirects(response, embargo_url)

        # Otherwise, verify that the student can access the page
        else:
            self.assertEqual(response.status_code, 200)

        # For non-embargoed courses, the student should be able to access
        # the page, even if he/she is from an embargoed country.
        response = self.client.get(self.regular_page)
        self.assertEqual(response.status_code, 200)

    def test_embargo_profile_country_cache(self):
        # Set the country in the user's profile
        profile = self.user.profile
        profile.country = "us"
        profile.save()

        # Warm the cache
        with self.assertNumQueries(16):
            self.client.get(self.embargoed_page)

        # Access the page multiple times, but expect that we hit
        # the database to check the user's profile only once
        with self.assertNumQueries(10):
            self.client.get(self.embargoed_page)

    def test_embargo_profile_country_db_null(self):
        # Django country fields treat NULL values inconsistently.
        # When saving a profile with country set to None, Django saves an empty string to the database.
        # However, when the country field loads a NULL value from the database, it sets
        # `country.code` to `None`.  This caused a bug in which country values created by
        # the original South schema migration -- which defaulted to NULL -- caused a runtime
        # exception when the embargo middleware treated the value as a string.
        # In order to simulate this behavior, we can't simply set `profile.country = None`.
        # (because when we save it, it will set the database field to an empty string instead of NULL)
        query = "UPDATE auth_userprofile SET country = NULL WHERE id = %s"
        connection.cursor().execute(query, [str(self.user.profile.id)])
        transaction.commit_unless_managed()

        # Attempt to access an embargoed course
        # Verify that the student can access the page without an error
        response = self.client.get(self.embargoed_page)
        self.assertEqual(response.status_code, 200)

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

    @mock.patch.dict(settings.FEATURES, {'EMBARGO': False, 'SITE_EMBARGOED': True})
    def test_embargo_off_embargo_site_on(self):
        # When the middleware is turned on with SITE, main site access should be restricted
        # Accessing a regular page from a blocked IP is denied.
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
        self.assertEqual(response.status_code, 403)

        # Accessing a regular page from a non blocked IP should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='5.0.0.0', REMOTE_ADDR='5.0.0.0')
        self.assertEqual(response.status_code, 200)

    @mock.patch.dict(settings.FEATURES, {'EMBARGO': False, 'SITE_EMBARGOED': True})
    @override_settings(EMBARGO_SITE_REDIRECT_URL='https://www.edx.org/')
    def test_embargo_off_embargo_site_on_with_redirect_url(self):
        # When the middleware is turned on with SITE_EMBARGOED, main site access
        # should be restricted. Accessing a regular page from a blocked IP is
        # denied, and redirected to EMBARGO_SITE_REDIRECT_URL rather than returning a 403.
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
        self.assertEqual(response.status_code, 302)
