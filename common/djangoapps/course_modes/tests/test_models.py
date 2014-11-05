"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from datetime import datetime, timedelta
import pytz
import ddt

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from django.test import TestCase
from course_modes.models import CourseMode, Mode


@ddt.ddt
class CourseModeModelTest(TestCase):
    """
    Tests for the CourseMode model
    """

    def setUp(self):
        self.course_key = SlashSeparatedCourseKey('Test', 'TestCourse', 'TestCourseRun')
        CourseMode.objects.all().delete()

    def create_mode(self, mode_slug, mode_name, min_price=0, suggested_prices='', currency='usd'):
        """
        Create a new course mode
        """
        return CourseMode.objects.get_or_create(
            course_id=self.course_key,
            mode_display_name=mode_name,
            mode_slug=mode_slug,
            min_price=min_price,
            suggested_prices=suggested_prices,
            currency=currency,
        )

    def test_modes_for_course_empty(self):
        """
        If we can't find any modes, we should get back the default mode
        """
        # shouldn't be able to find a corresponding course
        modes = CourseMode.modes_for_course(self.course_key)
        self.assertEqual([CourseMode.DEFAULT_MODE], modes)

    def test_nodes_for_course_single(self):
        """
        Find the modes for a course with only one mode
        """

        self.create_mode('verified', 'Verified Certificate')
        modes = CourseMode.modes_for_course(self.course_key)
        mode = Mode(u'verified', u'Verified Certificate', 0, '', 'usd', None, None)
        self.assertEqual([mode], modes)

        modes_dict = CourseMode.modes_for_course_dict(self.course_key)
        self.assertEqual(modes_dict['verified'], mode)
        self.assertEqual(CourseMode.mode_for_course(self.course_key, 'verified'),
                         mode)

    def test_modes_for_course_multiple(self):
        """
        Finding the modes when there's multiple modes
        """
        mode1 = Mode(u'honor', u'Honor Code Certificate', 0, '', 'usd', None, None)
        mode2 = Mode(u'verified', u'Verified Certificate', 0, '', 'usd', None, None)
        set_modes = [mode1, mode2]
        for mode in set_modes:
            self.create_mode(mode.slug, mode.name, mode.min_price, mode.suggested_prices)

        modes = CourseMode.modes_for_course(self.course_key)
        self.assertEqual(modes, set_modes)
        self.assertEqual(mode1, CourseMode.mode_for_course(self.course_key, u'honor'))
        self.assertEqual(mode2, CourseMode.mode_for_course(self.course_key, u'verified'))
        self.assertIsNone(CourseMode.mode_for_course(self.course_key, 'DNE'))

    def test_min_course_price_for_currency(self):
        """
        Get the min course price for a course according to currency
        """
        # no modes, should get 0
        self.assertEqual(0, CourseMode.min_course_price_for_currency(self.course_key, 'usd'))

        # create some modes
        mode1 = Mode(u'honor', u'Honor Code Certificate', 10, '', 'usd', None, None)
        mode2 = Mode(u'verified', u'Verified Certificate', 20, '', 'usd', None, None)
        mode3 = Mode(u'honor', u'Honor Code Certificate', 80, '', 'cny', None, None)
        set_modes = [mode1, mode2, mode3]
        for mode in set_modes:
            self.create_mode(mode.slug, mode.name, mode.min_price, mode.suggested_prices, mode.currency)

        self.assertEqual(10, CourseMode.min_course_price_for_currency(self.course_key, 'usd'))
        self.assertEqual(80, CourseMode.min_course_price_for_currency(self.course_key, 'cny'))

    def test_modes_for_course_expired(self):
        expired_mode, _status = self.create_mode('verified', 'Verified Certificate')
        expired_mode.expiration_datetime = datetime.now(pytz.UTC) + timedelta(days=-1)
        expired_mode.save()
        modes = CourseMode.modes_for_course(self.course_key)
        self.assertEqual([CourseMode.DEFAULT_MODE], modes)

        mode1 = Mode(u'honor', u'Honor Code Certificate', 0, '', 'usd', None, None)
        self.create_mode(mode1.slug, mode1.name, mode1.min_price, mode1.suggested_prices)
        modes = CourseMode.modes_for_course(self.course_key)
        self.assertEqual([mode1], modes)

        expiration_datetime = datetime.now(pytz.UTC) + timedelta(days=1)
        expired_mode.expiration_datetime = expiration_datetime
        expired_mode.save()
        expired_mode_value = Mode(u'verified', u'Verified Certificate', 0, '', 'usd', expiration_datetime, None)
        modes = CourseMode.modes_for_course(self.course_key)
        self.assertEqual([expired_mode_value, mode1], modes)

        modes = CourseMode.modes_for_course(SlashSeparatedCourseKey('TestOrg', 'TestCourse', 'TestRun'))
        self.assertEqual([CourseMode.DEFAULT_MODE], modes)

    def test_verified_mode_for_course(self):
        self.create_mode('verified', 'Verified Certificate')

        mode = CourseMode.verified_mode_for_course(self.course_key)

        self.assertEqual(mode.slug, 'verified')

        # verify that the professional mode is preferred
        self.create_mode('professional', 'Professional Education Verified Certificate')

        mode = CourseMode.verified_mode_for_course(self.course_key)

        self.assertEqual(mode.slug, 'professional')

    def test_course_has_payment_options(self):
        # Has no payment options.
        honor, _ = self.create_mode('honor', 'Honor')
        self.assertFalse(CourseMode.has_payment_options(self.course_key))

        # Now we do have a payment option.
        verified, _ = self.create_mode('verified', 'Verified', min_price=5)
        self.assertTrue(CourseMode.has_payment_options(self.course_key))

        # Unset verified's minimum price.
        verified.min_price = 0
        verified.save()
        self.assertFalse(CourseMode.has_payment_options(self.course_key))

        # Finally, give the honor mode payment options
        honor.suggested_prices = '5, 10, 15'
        honor.save()
        self.assertTrue(CourseMode.has_payment_options(self.course_key))

    @ddt.data(
        ([], True),
        ([("honor", 0), ("audit", 0), ("verified", 100)], True),
        ([("honor", 100)], False),
        ([("professional", 100)], False),
    )
    @ddt.unpack
    def test_can_auto_enroll(self, modes_and_prices, can_auto_enroll):
        # Create the modes and min prices
        for mode_slug, min_price in modes_and_prices:
            self.create_mode(mode_slug, mode_slug.capitalize(), min_price=min_price)

        # Verify that we can or cannot auto enroll
        self.assertEqual(CourseMode.can_auto_enroll(self.course_key), can_auto_enroll)
