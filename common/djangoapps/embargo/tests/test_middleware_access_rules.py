"""
Tests for EmbargoMiddleware with CountryAccessRules
"""

import mock
import unittest

from django.db import connection, transaction
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test.utils import override_settings
import ddt

from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase, mixed_store_config
)

# Explicitly import the cache from ConfigurationModel so we can reset it after each test
from config_models.models import cache
from embargo.models import (
    IPFilter, RestrictedCourse, Country, CountryAccessRule, WHITE_LIST, BLACK_LIST
)
from django_countries import countries


# Since we don't need any XML course fixtures, use a modulestore configuration
# that disables the XML modulestore.
MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EmbargoCountryAccessRulesTests(ModuleStoreTestCase):
    """
    Tests of EmbargoApi
    """

    def setUp(self):
        super(EmbargoCountryAccessRulesTests, self).setUp()
        self.user = UserFactory(username='fred', password='secret')
        self.client.login(username='fred', password='secret')
        self.embargo_course1 = CourseFactory.create()
        self.embargo_course1.save()
        self.embargo_course2 = CourseFactory.create()
        self.embargo_course2.save()
        self.regular_course = CourseFactory.create(org="Regular")
        self.regular_course.save()
        self.embargoed_course_whitelisted = '/courses/' + self.embargo_course1.id.to_deprecated_string() + '/info'
        self.embargoed_course_blacklisted = '/courses/' + self.embargo_course2.id.to_deprecated_string() + '/info'
        self.regular_page = '/courses/' + self.regular_course.id.to_deprecated_string() + '/info'

        restricted_course_1 = RestrictedCourse.objects.create(course_key=self.embargo_course1.id)
        restricted_course_2 = RestrictedCourse.objects.create(course_key=self.embargo_course2.id)

        all_countries = [Country(country=code[0]) for code in list(countries)]
        Country.objects.bulk_create(all_countries)

        country_access_white_rules = [
            CountryAccessRule(
                restricted_course=restricted_course_1,
                rule_type=WHITE_LIST,
                country=Country.objects.get(country='US')
            ),
            CountryAccessRule(
                restricted_course=restricted_course_1,
                rule_type=WHITE_LIST,
                country=Country.objects.get(country='NZ')
            )
        ]
        CountryAccessRule.objects.bulk_create(country_access_white_rules)

        country_access_black_rules = [
            CountryAccessRule(
                restricted_course=restricted_course_2,
                rule_type=BLACK_LIST,
                country=Country.objects.get(country='CU')
            ),
            CountryAccessRule(
                restricted_course=restricted_course_2,
                rule_type=BLACK_LIST,
                country=Country.objects.get(country='IR')
            )
        ]
        CountryAccessRule.objects.bulk_create(country_access_black_rules)

        IPFilter(
            whitelist='5.0.0.0',
            blacklist='1.0.0.0',
            changed_by=self.user,
            enabled=True
        ).save()

        # Text from lms/templates/static_templates/embargo.html
        self.embargo_text = "Unfortunately, at this time edX must comply with export controls, and we cannot allow you to access this course."  # pylint: disable=line-too-long

    def tearDown(self):
        # Explicitly clear ConfigurationModel's cache so tests have a clear cache
        # and don't interfere with each other
        cache.clear()

    @mock.patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
    def test_countries(self):
        # Accessing an embargoed page from a blocked IP should cause a redirect
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='1.0.0.0',
            REMOTE_ADDR='1.0.0.0'
        )
        self.assertEqual(response.status_code, 302)
        # Following the redirect should give us the embargo page
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='1.0.0.0',
            REMOTE_ADDR='1.0.0.0',
            follow=True
        )
        self.assertIn(self.embargo_text, response.content)

        # Accessing a regular page from a blocked IP should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
        self.assertEqual(response.status_code, 200)

        # Accessing an embargoed page from a non-embargoed IP should succeed
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='5.0.0.0',
            REMOTE_ADDR='5.0.0.0'
        )
        self.assertEqual(response.status_code, 200)

        # Accessing a regular page from a non-embargoed IP should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='5.0.0.0', REMOTE_ADDR='5.0.0.0')
        self.assertEqual(response.status_code, 200)

    @mock.patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
    def test_countries_ipv6(self):
        # Accessing an embargoed page from a blocked IP should cause a redirect
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='2001:1340::',
            REMOTE_ADDR='2001:1340::'
        )
        self.assertEqual(response.status_code, 302)
        # Following the redirect should give us the embargo page
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='2001:1340::',
            REMOTE_ADDR='2001:1340::',
            follow=True
        )
        self.assertIn(self.embargo_text, response.content)

        # Accessing a regular page from a blocked IP should succeed
        response = self.client.get(
            self.regular_page,
            HTTP_X_FORWARDED_FOR='2001:1340::',
            REMOTE_ADDR='2001:1340::'
        )
        self.assertEqual(response.status_code, 200)

        # Accessing an embargoed page from a non-embargoed IP should succeed
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='2001:250::',
            REMOTE_ADDR='2001:250::'
        )
        self.assertEqual(response.status_code, 200)

        # Accessing a regular page from a non-embargoed IP should succeed
        response = self.client.get(
            self.regular_page,
            HTTP_X_FORWARDED_FOR='2001:250::',
            REMOTE_ADDR='2001:250::'
        )
        self.assertEqual(response.status_code, 200)

    @mock.patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
    def test_ip_exceptions(self):
        # Explicitly whitelist/blacklist some IPs
        IPFilter(
            whitelist='1.0.0.0',
            blacklist='5.0.0.0',
            changed_by=self.user,
            enabled=True
        ).save()

        # Accessing an embargoed page from a blocked IP that's been whitelisted
        # should succeed
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='1.0.0.0',
            REMOTE_ADDR='1.0.0.0'
        )
        self.assertEqual(response.status_code, 200)

        # Accessing a regular course from a blocked IP that's been whitelisted should succeed
        response = self.client.get(
            self.regular_page,
            HTTP_X_FORWARDED_FOR='1.0.0.0',
            REMOTE_ADDR='1.0.0.0'
        )
        self.assertEqual(response.status_code, 200)

        # Accessing an embargoed course from non-embargoed IP that's been blacklisted
        #  should cause a redirect
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='5.0.0.0',
            REMOTE_ADDR='5.0.0.0'
        )
        self.assertEqual(response.status_code, 302)
        # Following the redirect should give us the embargo page
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='5.0.0.0',
            REMOTE_ADDR='1.0.0.0',
            follow=True
        )
        self.assertIn(self.embargo_text, response.content)

        # Accessing a regular course from a non-embargoed IP that's been blacklisted should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='5.0.0.0', REMOTE_ADDR='5.0.0.0')
        self.assertEqual(response.status_code, 200)

    @mock.patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
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
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='1.0.0.0',
            REMOTE_ADDR='1.0.0.0'
        )
        self.assertEqual(response.status_code, 200)

        # Accessing a regular course from a blocked IP that's been whitelisted with a network
        # should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
        self.assertEqual(response.status_code, 200)

        # Accessing an embargoed course from non-embargoed IP that's been blacklisted with a network
        # should cause a redirect
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='5.0.0.100',
            REMOTE_ADDR='5.0.0.100'
        )
        self.assertEqual(response.status_code, 302)

        # Following the redirect should give us the embargo page
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='5.0.0.100',
            REMOTE_ADDR='5.0.0.100',
            follow=True
        )
        self.assertIn(self.embargo_text, response.content)

        # Accessing an embargoed course from non-embargoed IP that's been blaclisted with a network
        # should cause a redirect
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='1.1.0.1',
            REMOTE_ADDR='1.1.0.1'
        )
        self.assertEqual(response.status_code, 302)
        # Following the redirect should give us the embargo page
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='1.1.0.0',
            REMOTE_ADDR='1.1.0.0',
            follow=True
        )
        self.assertIn(self.embargo_text, response.content)

        # Accessing an embargoed from a blocked IP that's not blacklisted by the network rule.
        # should succeed
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='1.1.1.0',
            REMOTE_ADDR='1.1.1.0'
        )
        self.assertEqual(response.status_code, 200)

        # Accessing a regular course from a non-embargoed IP that's been blacklisted
        # should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='5.0.0.0', REMOTE_ADDR='5.0.0.0')
        self.assertEqual(response.status_code, 200)

    @mock.patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
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
        response = self.client.get(self.embargoed_course_blacklisted)
        self.assertEqual(response.status_code, 200)

    @mock.patch.dict(settings.FEATURES, {'EMBARGO': False, 'ENABLE_COUNTRY_ACCESS': True})
    def test_countries_embargo_off(self):
        # When the middleware is turned off, all requests should go through
        # Accessing an embargoed page from a blocked IP OK
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='1.0.0.0',
            REMOTE_ADDR='1.0.0.0'
        )
        self.assertEqual(response.status_code, 200)

        # Accessing a regular page from a blocked IP should succeed
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR='1.0.0.0', REMOTE_ADDR='1.0.0.0')
        self.assertEqual(response.status_code, 200)

        # Accessing an embargoed course from non-embargoed IP that's been blacklisted
        # should be OK
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='50.0.0.0',
            REMOTE_ADDR='50.0.0.0'
        )
        self.assertEqual(response.status_code, 200)

        # Accessing a regular course from a non-embargoed IP that's been blacklisted should succeed
        response = self.client.get(
            self.regular_page,
            HTTP_X_FORWARDED_FOR='50.0.0.0',
            REMOTE_ADDR='50.0.0.0'
        )
        self.assertEqual(response.status_code, 200)

    @mock.patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
    @ddt.data("", "US", "CA", "AF", "NZ", "IR")
    def test_regular_course_accessible_from_every_where(self, profile_country):
        # regular course is accessible even when ENABLE_COUNTRY_ACCESS flag is true
        profile = self.user.profile
        profile.country = profile_country
        profile.save()

        response = self.client.get(self.regular_page)
        # Course is accessible from all countries.
        self.assertEqual(response.status_code, 200)

    @mock.patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
    @ddt.data("", "US", "CA", "AF", "NZ", "IR")
    def test_embargo_course_whitelisted_with_profile_country(self, profile_country):
        # if course is emabargoed and has white list countries.
        # then only white list countries can access this course.

        profile = self.user.profile
        profile.country = profile_country
        profile.save()

        response = self.client.get(self.embargoed_course_whitelisted)
        # Course is whitelisted against US,NZ so all other countries will be disallowed
        if profile_country in ["CA", "AF", "IR"]:
            embargo_url = reverse('embargo')
            self.assertRedirects(response, embargo_url)
            self.assertEqual(response.status_code, 302)
        else:
            self.assertEqual(response.status_code, 200)

    @mock.patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
    @ddt.data("", "US", "CA", "NZ", "IR", "CU")
    def test_embargo_course_blacklisted_with_profile_country(self, profile_country):
        # if course is emabargoed and has black list countries ( CU , IR ).
        # then users from these countries can't access this course.
        # any user from other than these countries can access.

        profile = self.user.profile
        profile.country = profile_country
        profile.save()

        response = self.client.get(self.embargoed_course_blacklisted)
        if profile_country in ["", "US", "CA", "NZ"]:
            self.assertEqual(response.status_code, 200)
        else:
            embargo_url = reverse('embargo')
            self.assertRedirects(response, embargo_url)
            self.assertEqual(response.status_code, 302)

    @mock.patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
    @ddt.data("", "US", "CA", "NZ", "IR", "CU")
    def test_embargo_course_without_whitelist(self, profile_country):
        # if course is emabargoed but without black or whitelist
        # then course can be accessible from any where

        profile = self.user.profile
        profile.country = profile_country
        profile.save()

        embargo_course3 = CourseFactory.create()
        embargo_course3.save()
        RestrictedCourse(course_key=embargo_course3.id).save()
        embargoed_course_page = '/courses/' + embargo_course3.id.to_deprecated_string() + '/info'

        response = self.client.get(embargoed_course_page)
        self.assertEqual(response.status_code, 200)

    @mock.patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
    @ddt.data("", "US", "CA", "NZ", "IR", "CU")
    def test_embargo_course_without_blacklist(self, profile_country):
        # if course is emabargoed but without black or whitelist
        # then course can be accessible from any where
        profile = self.user.profile
        profile.country = profile_country
        profile.save()

        embargo_course4 = CourseFactory.create()
        embargo_course4.save()
        RestrictedCourse(course_key=embargo_course4.id).save()
        embargoed_course_page = '/courses/' + embargo_course4.id.to_deprecated_string() + '/info'

        response = self.client.get(embargoed_course_page)
        self.assertEqual(response.status_code, 200)


    @mock.patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
    def test_embargo_profile_country_cache(self):
        # Warm the cache
        with self.assertNumQueries(25):
            self.client.get(self.embargoed_course_blacklisted)

        # Access the page multiple times, but expect that we hit
        # the database to check the user's profile only once
        with self.assertNumQueries(9):
            self.client.get(self.embargoed_course_blacklisted)

