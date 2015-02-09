"""Test of models for embargo middleware app"""
from django.test import TestCase
from django.db.utils import IntegrityError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from embargo.models import (
    EmbargoedCourse, EmbargoedState, IPFilter, RestrictedCourse,
    Country, CountryAccessRule, WHITE_LIST, BLACK_LIST
)


class EmbargoModelsTest(TestCase):
    """Test each of the 3 models in embargo.models"""
    def test_course_embargo(self):
        course_id = SlashSeparatedCourseKey('abc', '123', 'doremi')
        # Test that course is not authorized by default
        self.assertFalse(EmbargoedCourse.is_embargoed(course_id))

        # Authorize
        cauth = EmbargoedCourse(course_id=course_id, embargoed=True)
        cauth.save()

        # Now, course should be embargoed
        self.assertTrue(EmbargoedCourse.is_embargoed(course_id))
        self.assertEquals(
            cauth.__unicode__(),
            "Course 'abc/123/doremi' is Embargoed"
        )

        # Unauthorize by explicitly setting email_enabled to False
        cauth.embargoed = False
        cauth.save()
        # Test that course is now unauthorized
        self.assertFalse(EmbargoedCourse.is_embargoed(course_id))
        self.assertEquals(
            cauth.__unicode__(),
            "Course 'abc/123/doremi' is Not Embargoed"
        )

    def test_state_embargo(self):
        # Azerbaijan and France should not be blocked
        good_states = ['AZ', 'FR']
        # Gah block USA and Antartica
        blocked_states = ['US', 'AQ']
        currently_blocked = EmbargoedState.current().embargoed_countries_list

        for state in blocked_states + good_states:
            self.assertFalse(state in currently_blocked)

        # Block
        cauth = EmbargoedState(embargoed_countries='US, AQ')
        cauth.save()
        currently_blocked = EmbargoedState.current().embargoed_countries_list

        for state in good_states:
            self.assertFalse(state in currently_blocked)
        for state in blocked_states:
            self.assertTrue(state in currently_blocked)

        # Change embargo - block Isle of Man too
        blocked_states.append('IM')
        cauth.embargoed_countries = 'US, AQ, IM'
        cauth.save()
        currently_blocked = EmbargoedState.current().embargoed_countries_list

        for state in good_states:
            self.assertFalse(state in currently_blocked)
        for state in blocked_states:
            self.assertTrue(state in currently_blocked)

    def test_ip_blocking(self):
        whitelist = '127.0.0.1'
        blacklist = '18.244.51.3'

        cwhitelist = IPFilter.current().whitelist_ips
        self.assertFalse(whitelist in cwhitelist)
        cblacklist = IPFilter.current().blacklist_ips
        self.assertFalse(blacklist in cblacklist)

        IPFilter(whitelist=whitelist, blacklist=blacklist).save()

        cwhitelist = IPFilter.current().whitelist_ips
        self.assertTrue(whitelist in cwhitelist)
        cblacklist = IPFilter.current().blacklist_ips
        self.assertTrue(blacklist in cblacklist)

    def test_ip_network_blocking(self):
        whitelist = '1.0.0.0/24'
        blacklist = '1.1.0.0/16'

        IPFilter(whitelist=whitelist, blacklist=blacklist).save()

        cwhitelist = IPFilter.current().whitelist_ips
        self.assertTrue('1.0.0.100' in cwhitelist)
        self.assertTrue('1.0.0.10' in cwhitelist)
        self.assertFalse('1.0.1.0' in cwhitelist)
        cblacklist = IPFilter.current().blacklist_ips
        self.assertTrue('1.1.0.0' in cblacklist)
        self.assertTrue('1.1.0.1' in cblacklist)
        self.assertTrue('1.1.1.0' in cblacklist)
        self.assertFalse('1.2.0.0' in cblacklist)


class RestrictedCourseTest(TestCase):
    """Test unicode values tests and cache functionality"""

    def test_unicode_values(self):
        course_id = SlashSeparatedCourseKey('abc', '123', 'doremi')
        restricted_course = RestrictedCourse.objects.create(course_key=course_id)
        self.assertEquals(
            restricted_course.__unicode__(),
            "abc/123/doremi"
        )

    def test_restricted_course_cache_with_save_delete(self):
        course_id = SlashSeparatedCourseKey('abc', '123', 'doremi')
        RestrictedCourse.objects.create(course_key=course_id)

        # Warm the cache
        with self.assertNumQueries(1):
            RestrictedCourse.is_restricted_course(course_id)

        # it should come from cache
        with self.assertNumQueries(0):
            RestrictedCourse.is_restricted_course(course_id)

        # add new the course so the cache must get delete and again hit the db
        new_course_id = SlashSeparatedCourseKey('def', '123', 'doremi')
        RestrictedCourse.objects.create(course_key=new_course_id)
        with self.assertNumQueries(1):
            RestrictedCourse.is_restricted_course(new_course_id)

        # it should come from cache
        with self.assertNumQueries(0):
            RestrictedCourse.is_restricted_course(new_course_id)

        # deleting an object will delete cache also.and hit db on
        # get the is_restricted course
        abc = RestrictedCourse.objects.get(course_key=new_course_id)
        abc.delete()
        with self.assertNumQueries(1):
            RestrictedCourse.is_restricted_course(new_course_id)

        # it should come from cache
        with self.assertNumQueries(0):
            RestrictedCourse.is_restricted_course(new_course_id)


class CountryTest(TestCase):
    """Test unicode values test"""

    def test_unicode_values(self):
        country = Country.objects.create(country='NZ')
        self.assertEquals(
            country.__unicode__(),
            "New Zealand (NZ)"
        )


class CountryAccessRuleTest(TestCase):
    """Test unicode values tests and unique-together contraint"""

    def test_unicode_values(self):
        course_id = SlashSeparatedCourseKey('abc', '123', 'doremi')
        country = Country.objects.create(country='NZ')
        restricted_course1 = RestrictedCourse.objects.create(course_key=course_id)
        access_rule = CountryAccessRule.objects.create(
            restricted_course=restricted_course1,
            rule_type=WHITE_LIST,
            country=country
        )

        self.assertEquals(
            access_rule.__unicode__(),
            "Whitelist New Zealand (NZ) for abc/123/doremi"
        )

        course_id = SlashSeparatedCourseKey('def', '123', 'doremi')
        restricted_course1 = RestrictedCourse.objects.create(course_key=course_id)
        access_rule = CountryAccessRule.objects.create(
            restricted_course=restricted_course1,
            rule_type=BLACK_LIST,
            country=country
        )

        self.assertEquals(
            access_rule.__unicode__(),
            "Blacklist New Zealand (NZ) for def/123/doremi"
        )

    def test_unique_together_constraint(self):
        """
         Course with specific country can be added either as whitelist or blacklist
         trying to add with both types will raise error
        """
        course_id = SlashSeparatedCourseKey('abc', '123', 'doremi')
        country = Country.objects.create(country='NZ')
        restricted_course1 = RestrictedCourse.objects.create(course_key=course_id)

        CountryAccessRule.objects.create(
            restricted_course=restricted_course1,
            rule_type=WHITE_LIST,
            country=country
        )

        with self.assertRaises(IntegrityError):
            CountryAccessRule.objects.create(
                restricted_course=restricted_course1,
                rule_type=BLACK_LIST,
                country=country
            )

    def test_country_access_list_cache_with_save_delete(self):
        course_id = SlashSeparatedCourseKey('abc', '123', 'doremi')
        country = Country.objects.create(country='NZ')
        restricted_course1 = RestrictedCourse.objects.create(course_key=course_id)

        course = CountryAccessRule.objects.create(
            restricted_course=restricted_course1,
            rule_type=WHITE_LIST,
            country=country
        )

        # Warm the cache
        with self.assertNumQueries(1):
            CountryAccessRule.check_country_access(course_id, 'NZ')

        with self.assertNumQueries(0):
            CountryAccessRule.check_country_access(course_id, 'NZ')

        # deleting an object will delete cache also.and hit db on
        # get the country access lists for course
        course.delete()
        with self.assertNumQueries(1):
            CountryAccessRule.check_country_access(course_id, 'NZ')
