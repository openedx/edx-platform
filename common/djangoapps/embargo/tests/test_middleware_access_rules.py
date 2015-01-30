"""
Tests for EmbargoMiddleware with CountryAccessRules
"""

import mock
import pygeoip
import unittest

from django.db import connection, transaction
from django.core.urlresolvers import reverse
from django.conf import settings
import ddt

from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase, mixed_store_config
)

# Explicitly import the cache from ConfigurationModel so we can reset it after each test
from config_models.models import cache
from embargo.models import (
    RestrictedCourse, Country, CountryAccessRule, WHITE_LIST, BLACK_LIST
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

        # Text from lms/templates/static_templates/embargo.html
        self.embargo_text = "Unfortunately, at this time edX must comply with export controls, and we cannot allow you to access this course."  # pylint: disable=line-too-long
        self.patcher = mock.patch.object(pygeoip.GeoIP, 'country_code_by_addr', self.mock_country_code_by_addr)
        self.patcher.start()

    def tearDown(self):
        # Explicitly clear ConfigurationModel's cache so tests have a clear cache
        # and don't interfere with each other
        cache.clear()
        self.patcher.stop()

    def mock_country_code_by_addr(self, ip_addr):
        """
        making a lists of countries which will be use in country access rules.
        if incoming request's ip belongs to this dict then related country will return.
        for one course CU and IR added as blacklist in course access rules.
        for one course US and NZ added as whitelist in course access rules.
        """
        ip_dict = {
            '1.0.0.0': 'CU',
            '2.0.0.0': 'IR',
            '3.0.0.0': 'US',
            '4.0.0.0': 'NZ'
        }
        return ip_dict.get(ip_addr, 'FR')

    @mock.patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
    @ddt.data('1.0.0.0', '2.0.0.0')
    def test_course_access_rules_with_black_rule_country_by_user_ip(self, ip_address):
        # Accessing an embargoed page from a user ip whose origin is added as
        # blacklist in course access rules should be redirected.
        # any other IP should be success

        # Following the redirect should give us the embargo page
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR=ip_address,
            REMOTE_ADDR=ip_address
        )
        self.assertEqual(response.status_code, 302)

        # Following the redirect should give us the embargo page
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR=ip_address,
            REMOTE_ADDR=ip_address,
            follow=True
        )
        self.assertIn(self.embargo_text, response.content)

        # accesssing blacklist course from any other country ip should be success
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR='5.0.0.1',
            REMOTE_ADDR='5.0.0.1'
        )
        self.assertEqual(response.status_code, 200)

        # accesssing whitelist course from these should give us the embargo page
        response = self.client.get(
            self.embargoed_course_whitelisted,
            HTTP_X_FORWARDED_FOR=ip_address,
            REMOTE_ADDR=ip_address
        )
        self.assertEqual(response.status_code, 302)

        # Accessing a regular page from these IP should be success
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR=ip_address, REMOTE_ADDR=ip_address)
        self.assertEqual(response.status_code, 200)

    @mock.patch.dict(settings.FEATURES, {'ENABLE_COUNTRY_ACCESS': True})
    @ddt.data('3.0.0.0', '4.0.0.0', "7.0.0.1", "2001:250::")
    def test_course_access_rules_with_white_rule_country_by_user_ip(self, ip_address):
        # Accessing an embargoed page from a user ip whose origin is added as
        # white in course access rules should succeed. any other ip should be fail

        response = self.client.get(
            self.embargoed_course_whitelisted,
            HTTP_X_FORWARDED_FOR=ip_address,
            REMOTE_ADDR=ip_address
        )
        if ip_address in ['3.0.0.0', '4.0.0.0']:
            self.assertEqual(response.status_code, 200)
        else:
            self.assertEqual(response.status_code, 302)

        # access the blacklisted course should give success
        response = self.client.get(
            self.embargoed_course_blacklisted,
            HTTP_X_FORWARDED_FOR=ip_address,
            REMOTE_ADDR=ip_address
        )
        self.assertEqual(response.status_code, 200)

        # Accessing a regular page should success
        response = self.client.get(self.regular_page, HTTP_X_FORWARDED_FOR=ip_address, REMOTE_ADDR=ip_address)
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
        # course is emabargoed and has white list countries.
        # but user ip belongs to US  but profile country is blacklist
        # only white list country can access the course.

        profile = self.user.profile
        profile.country = profile_country
        profile.save()

        # adding the US IP so the _country_code_from_ip() get passed
        response = self.client.get(
            self.embargoed_course_whitelisted,
            HTTP_X_FORWARDED_FOR='3.0.0.0',
            REMOTE_ADDR='3.0.0.0'
        )
        # Course is whitelisted against US,NZ so all other countries will be disallowed
        if profile_country in ["CA", "AF", "IR"]:
            self.assertRedirects(response, reverse('embargo'))
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
    def test_embargo_course_without_any_rules_list(self, profile_country):
        # if course is emabargoed but without whitelist and blacklist
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
    def test_embargo_profile_country_cache(self):
        # Warm the cache
        with self.assertNumQueries(24):
            self.client.get(self.embargoed_course_blacklisted)

        # Access the page multiple times, but expect that we hit
        # the database to check the user's profile only once
        with self.assertNumQueries(9):
            self.client.get(self.embargoed_course_blacklisted)
