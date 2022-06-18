"""
Tests of deprecated Locations and SlashSeparatedCourseKeys
"""
import re

from opaque_keys import InvalidKeyError

from opaque_keys.edx.locator import AssetLocator, BlockUsageLocator, CourseLocator
from opaque_keys.edx.locations import AssetLocation, Location, SlashSeparatedCourseKey
from opaque_keys.edx.tests import TestDeprecated
from opaque_keys.edx.keys import CourseKey, UsageKey

# Allow protected method access throughout this test file
# pylint: disable=protected-access


class TestLocationDeprecatedBase(TestDeprecated):
    """Base for all Location Test Classes"""
    def check_deprecated_replace(self, cls):
        """
        Both AssetLocation and Location must implement their own replace method. This helps test them.

        NOTE: This replace function accesses deprecated variables and therefore throws multiple deprecation warnings.
        """
        with self.assertDeprecationWarning(count=4):
            loc = cls("foo", "bar", "baz", "cat", "name")
            loc_boo = loc.replace(org='boo')
            loc_copy = loc.replace()
            loc_course_key_replaced = loc.replace(course_key=loc.course_key)
        self.assertTrue(isinstance(loc_boo, BlockUsageLocator))
        self.assertTrue(loc_boo.deprecated)
        self.assertNotEqual(id(loc), id(loc_boo))
        self.assertNotEqual(id(loc), id(loc_copy))
        self.assertNotEqual(loc, loc_boo)
        self.assertEqual(loc, loc_copy)
        self.assertEqual(loc, loc_course_key_replaced)


class TestSSCK(TestDeprecated):
    """Tests that SSCK raises a deprecation warning and returns a CourseLocator"""
    def test_deprecated_init(self):
        with self.assertDeprecationWarning():
            ssck = SlashSeparatedCourseKey("foo", "bar", "baz")
        self.assertTrue(isinstance(ssck, CourseLocator))
        self.assertTrue(ssck.deprecated)

    def test_deprecated_from_string_bad(self):
        with self.assertDeprecationWarning():
            with self.assertRaises(InvalidKeyError):
                SlashSeparatedCourseKey.from_string("foo+bar")

    def test_deprecated_from_dep_string(self):
        with self.assertDeprecationWarning():
            ssck = SlashSeparatedCourseKey.from_string("foo/bar/baz")
        self.assertTrue(isinstance(ssck, CourseLocator))

    def test_deprecated_from_dep_string_bad(self):
        with self.assertDeprecationWarning():
            with self.assertRaises(InvalidKeyError):
                SlashSeparatedCourseKey.from_string("foo/bar")

    def test_deprecated_replace(self):
        with self.assertDeprecationWarning(count=3):
            ssck = SlashSeparatedCourseKey("foo", "bar", "baz")
            ssck_boo = ssck.replace(org='boo')
            ssck_copy = ssck.replace()
        self.assertTrue(isinstance(ssck_boo, CourseLocator))
        self.assertTrue(ssck_boo.deprecated)
        self.assertNotEqual(id(ssck), id(ssck_boo))
        self.assertNotEqual(id(ssck), id(ssck_copy))
        self.assertNotEqual(ssck, ssck_boo)
        self.assertEqual(ssck, ssck_copy)


class TestV0Strings(TestDeprecated):
    """
    Test that we can parse slashes:org+course+run and locations:org+course+run+type+id
    strings which were short-lived
    """
    def test_parse_slashes(self):
        """
        Test that we can parse slashes:org+course+run strings which were short-lived
        """
        parsed_key = CourseKey.from_string('slashes:DemoUniversity+DM01+2014')
        self.assertEqual(parsed_key.org, 'DemoUniversity')
        self.assertEqual(parsed_key.course, 'DM01')
        self.assertEqual(parsed_key.run, '2014')

    def test_parse_location(self):
        """
        Test that we can parse location:org+course+run+type+id
        """
        parsed_key = UsageKey.from_string(
            'location:GradingUniv+GT101+2014+chapter+4420ef6679b34ee8ba0cfd6d514b1b38'
        )
        self.assertEqual(parsed_key.org, 'GradingUniv')
        self.assertEqual(parsed_key.course, 'GT101')
        self.assertEqual(parsed_key.run, '2014')
        self.assertEqual(parsed_key.block_type, 'chapter')
        self.assertEqual(parsed_key.block_id, '4420ef6679b34ee8ba0cfd6d514b1b38')


class TestLocation(TestLocationDeprecatedBase):
    """Tests that Location raises a deprecation warning and returns a BlockUsageLocator"""
    def test_deprecated_init(self):
        with self.assertDeprecationWarning():
            loc = Location("foo", "bar", "baz", "cat", "name")
        self.assertTrue(isinstance(loc, BlockUsageLocator))
        self.assertTrue(loc.deprecated)

    def test_clean(self):

        with self.assertDeprecationWarning(count=6):
            with self.assertRaises(InvalidKeyError):
                Location._check_location_part('abc123', re.compile(r'\d'))

            self.assertEqual('abc_', Location._clean('abc123', re.compile(r'\d')))
            self.assertEqual('a._%-', Location.clean('a.*:%-'))
            self.assertEqual('a.__%-', Location.clean_keeping_underscores('a.*:%-'))
            self.assertEqual('a._:%-', Location.clean_for_url_name('a.*:%-'))
            self.assertEqual('a_-', Location.clean_for_html('a.*:%-'))

    def test_deprecated_replace(self):
        self.check_deprecated_replace(Location)


class TestAssetLocation(TestLocationDeprecatedBase):
    """Tests that AssetLocation raises a deprecation warning and returns an AssetLocator"""
    def test_deprecated_init(self):
        with self.assertDeprecationWarning():
            loc = AssetLocation("foo", "bar", "baz", "cat", "name")
        self.assertTrue(isinstance(loc, AssetLocator))
        self.assertTrue(loc.deprecated)

    def test_deprecated_replace(self):
        self.check_deprecated_replace(AssetLocation)
