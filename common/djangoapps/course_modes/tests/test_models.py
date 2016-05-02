"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from datetime import datetime, timedelta
import itertools

import ddt
from django.core.exceptions import ValidationError
from django.test import TestCase
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys.edx.locator import CourseLocator
import pytz

from course_modes.helpers import enrollment_mode_display
from course_modes.models import CourseMode, Mode


@ddt.ddt
class CourseModeModelTest(TestCase):
    """
    Tests for the CourseMode model
    """

    def setUp(self):
        super(CourseModeModelTest, self).setUp()
        self.course_key = SlashSeparatedCourseKey('Test', 'TestCourse', 'TestCourseRun')
        CourseMode.objects.all().delete()

    def create_mode(
            self,
            mode_slug,
            mode_name,
            min_price=0,
            suggested_prices='',
            currency='usd',
            expiration_datetime=None,
    ):
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
            _expiration_datetime=expiration_datetime,
        )

    def test_save(self):
        """ Verify currency is always lowercase. """
        cm, __ = self.create_mode('honor', 'honor', 0, '', 'USD')
        self.assertEqual(cm.currency, 'usd')

        cm.currency = 'GHS'
        cm.save()
        self.assertEqual(cm.currency, 'ghs')

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
        mode = Mode(u'verified', u'Verified Certificate', 0, '', 'usd', None, None, None)
        self.assertEqual([mode], modes)

        modes_dict = CourseMode.modes_for_course_dict(self.course_key)
        self.assertEqual(modes_dict['verified'], mode)
        self.assertEqual(CourseMode.mode_for_course(self.course_key, 'verified'),
                         mode)

    def test_modes_for_course_multiple(self):
        """
        Finding the modes when there's multiple modes
        """
        mode1 = Mode(u'honor', u'Honor Code Certificate', 0, '', 'usd', None, None, None)
        mode2 = Mode(u'verified', u'Verified Certificate', 0, '', 'usd', None, None, None)
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
        mode1 = Mode(u'honor', u'Honor Code Certificate', 10, '', 'usd', None, None, None)
        mode2 = Mode(u'verified', u'Verified Certificate', 20, '', 'usd', None, None, None)
        mode3 = Mode(u'honor', u'Honor Code Certificate', 80, '', 'cny', None, None, None)
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

        mode1 = Mode(u'honor', u'Honor Code Certificate', 0, '', 'usd', None, None, None)
        self.create_mode(mode1.slug, mode1.name, mode1.min_price, mode1.suggested_prices)
        modes = CourseMode.modes_for_course(self.course_key)
        self.assertEqual([mode1], modes)

        expiration_datetime = datetime.now(pytz.UTC) + timedelta(days=1)
        expired_mode.expiration_datetime = expiration_datetime
        expired_mode.save()
        expired_mode_value = Mode(u'verified', u'Verified Certificate', 0, '', 'usd', expiration_datetime, None, None)
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

    def test_course_has_payment_options_with_no_id_professional(self):
        # Has payment options.
        self.create_mode('no-id-professional', 'no-id-professional', min_price=5)
        self.assertTrue(CourseMode.has_payment_options(self.course_key))

    @ddt.data(
        ([], True),
        ([("honor", 0), ("audit", 0), ("verified", 100)], True),
        ([("honor", 100)], False),
        ([("professional", 100)], False),
        ([("no-id-professional", 100)], False),
    )
    @ddt.unpack
    def test_can_auto_enroll(self, modes_and_prices, can_auto_enroll):
        # Create the modes and min prices
        for mode_slug, min_price in modes_and_prices:
            self.create_mode(mode_slug, mode_slug.capitalize(), min_price=min_price)

        # Verify that we can or cannot auto enroll
        self.assertEqual(CourseMode.can_auto_enroll(self.course_key), can_auto_enroll)

    @ddt.data(
        ([], None),
        (["honor", "audit", "verified"], "honor"),
        (["honor", "audit"], "honor"),
        (["audit", "verified"], "audit"),
        (["professional"], None),
        (["no-id-professional"], None),
        (["credit", "audit", "verified"], "audit"),
        (["credit"], None),
    )
    @ddt.unpack
    def test_auto_enroll_mode(self, modes, result):
        # Verify that the proper auto enroll mode is returned
        self.assertEqual(CourseMode.auto_enroll_mode(self.course_key, modes), result)

    def test_all_modes_for_courses(self):
        now = datetime.now(pytz.UTC)
        future = now + timedelta(days=1)
        past = now - timedelta(days=1)

        # Unexpired, no expiration date
        CourseMode.objects.create(
            course_id=self.course_key,
            mode_display_name="Honor No Expiration",
            mode_slug="honor_no_expiration",
            expiration_datetime=None
        )

        # Unexpired, expiration date in future
        CourseMode.objects.create(
            course_id=self.course_key,
            mode_display_name="Honor Not Expired",
            mode_slug="honor_not_expired",
            expiration_datetime=future
        )

        # Expired
        CourseMode.objects.create(
            course_id=self.course_key,
            mode_display_name="Verified Expired",
            mode_slug="verified_expired",
            expiration_datetime=past
        )

        # We should get all of these back when querying for *all* course modes,
        # including ones that have expired.
        other_course_key = CourseLocator(org="not", course="a", run="course")
        all_modes = CourseMode.all_modes_for_courses([self.course_key, other_course_key])
        self.assertEqual(len(all_modes[self.course_key]), 3)
        self.assertEqual(all_modes[self.course_key][0].name, "Honor No Expiration")
        self.assertEqual(all_modes[self.course_key][1].name, "Honor Not Expired")
        self.assertEqual(all_modes[self.course_key][2].name, "Verified Expired")

        # Check that we get a default mode for when no course mode is available
        self.assertEqual(len(all_modes[other_course_key]), 1)
        self.assertEqual(all_modes[other_course_key][0], CourseMode.DEFAULT_MODE)

    @ddt.data('', 'no-id-professional', 'professional', 'verified')
    def test_course_has_professional_mode(self, mode):
        # check the professional mode.

        self.create_mode(mode, 'course mode', 10)
        modes_dict = CourseMode.modes_for_course_dict(self.course_key)

        if mode in ['professional', 'no-id-professional']:
            self.assertTrue(CourseMode.has_professional_mode(modes_dict))
        else:
            self.assertFalse(CourseMode.has_professional_mode(modes_dict))

    @ddt.data('no-id-professional', 'professional', 'verified')
    def test_course_is_professional_mode(self, mode):
        # check that tuple has professional mode

        course_mode, __ = self.create_mode(mode, 'course mode', 10)
        if mode in ['professional', 'no-id-professional']:
            self.assertTrue(CourseMode.is_professional_mode(course_mode.to_tuple()))
        else:
            self.assertFalse(CourseMode.is_professional_mode(course_mode.to_tuple()))

    def test_course_is_professional_mode_with_invalid_tuple(self):
        # check that tuple has professional mode with None
        self.assertFalse(CourseMode.is_professional_mode(None))

    @ddt.data(
        ('no-id-professional', False),
        ('professional', True),
        ('verified', True),
        ('honor', False),
        ('audit', False)
    )
    @ddt.unpack
    def test_is_verified_slug(self, mode_slug, is_verified):
        # check that mode slug is verified or not
        if is_verified:
            self.assertTrue(CourseMode.is_verified_slug(mode_slug))
        else:
            self.assertFalse(CourseMode.is_verified_slug(mode_slug))

    @ddt.data(*itertools.product(
        (
            CourseMode.HONOR,
            CourseMode.AUDIT,
            CourseMode.VERIFIED,
            CourseMode.PROFESSIONAL,
            CourseMode.NO_ID_PROFESSIONAL_MODE
        ),
        (datetime.now(), None),
    ))
    @ddt.unpack
    def test_invalid_mode_expiration(self, mode_slug, exp_dt):
        is_error_expected = CourseMode.is_professional_slug(mode_slug) and exp_dt is not None
        try:
            self.create_mode(mode_slug=mode_slug, mode_name=mode_slug.title(), expiration_datetime=exp_dt)
            self.assertFalse(is_error_expected, "Expected a ValidationError to be thrown.")
        except ValidationError, exc:
            self.assertTrue(is_error_expected, "Did not expect a ValidationError to be thrown.")
            self.assertEqual(
                exc.messages,
                [u"Professional education modes are not allowed to have expiration_datetime set."],
            )

    @ddt.data(
        ("verified", "verify_need_to_verify"),
        ("verified", "verify_submitted"),
        ("verified", "verify_approved"),
        ("verified", 'dummy'),
        ("verified", None),
        ('honor', None),
        ('honor', 'dummy'),
        ('audit', None),
        ('professional', None),
        ('no-id-professional', None),
        ('no-id-professional', 'dummy')
    )
    @ddt.unpack
    def test_enrollment_mode_display(self, mode, verification_status):
        if mode == "verified":
            self.assertEqual(
                enrollment_mode_display(mode, verification_status, self.course_key),
                self._enrollment_display_modes_dicts(verification_status)
            )
            self.assertEqual(
                enrollment_mode_display(mode, verification_status, self.course_key),
                self._enrollment_display_modes_dicts(verification_status)
            )
            self.assertEqual(
                enrollment_mode_display(mode, verification_status, self.course_key),
                self._enrollment_display_modes_dicts(verification_status)
            )
        elif mode == "honor":
            self.assertEqual(
                enrollment_mode_display(mode, verification_status, self.course_key),
                self._enrollment_display_modes_dicts(mode)
            )
        elif mode == "audit":
            self.assertEqual(
                enrollment_mode_display(mode, verification_status, self.course_key),
                self._enrollment_display_modes_dicts(mode)
            )
        elif mode == "professional":
            self.assertEqual(
                enrollment_mode_display(mode, verification_status, self.course_key),
                self._enrollment_display_modes_dicts(mode)
            )

    @ddt.data(
        (['honor', 'verified', 'credit'], ['honor', 'verified']),
        (['professional', 'credit'], ['professional']),
    )
    @ddt.unpack
    def test_hide_credit_modes(self, available_modes, expected_selectable_modes):
        # Create the course modes
        for mode in available_modes:
            CourseMode.objects.create(
                course_id=self.course_key,
                mode_display_name=mode,
                mode_slug=mode,
            )

        # Check the selectable modes, which should exclude credit
        selectable_modes = CourseMode.modes_for_course_dict(self.course_key)
        self.assertItemsEqual(selectable_modes.keys(), expected_selectable_modes)

        # When we get all unexpired modes, we should see credit as well
        all_modes = CourseMode.modes_for_course_dict(self.course_key, only_selectable=False)
        self.assertItemsEqual(all_modes.keys(), available_modes)

    def _enrollment_display_modes_dicts(self, dict_type):
        """
        Helper function to generate the enrollment display mode dict.
        """
        dict_keys = ['enrollment_title', 'enrollment_value', 'show_image', 'image_alt', 'display_mode']
        display_values = {
            "verify_need_to_verify": ["Your verification is pending", "Verified: Pending Verification", True,
                                      'ID verification pending', 'verified'],
            "verify_approved": ["You're enrolled as a verified student", "Verified", True, 'ID Verified Ribbon/Badge',
                                'verified'],
            "verify_none": ["", "", False, '', 'audit'],
            "honor": ["You're enrolled as an honor code student", "Honor Code", False, '', 'honor'],
            "audit": ["", "", False, '', 'audit'],
            "professional": ["You're enrolled as a professional education student", "Professional Ed", False, '',
                             'professional']
        }
        if dict_type in ['verify_need_to_verify', 'verify_submitted']:
            return dict(zip(dict_keys, display_values.get('verify_need_to_verify')))
        elif dict_type is None or dict_type == 'dummy':
            return dict(zip(dict_keys, display_values.get('verify_none')))
        else:
            return dict(zip(dict_keys, display_values.get(dict_type)))

    def test_expiration_datetime_explicitly_set(self):
        """ Verify that setting the expiration_date property sets the explicit flag. """
        verified_mode, __ = self.create_mode('verified', 'Verified Certificate')
        now = datetime.now()
        verified_mode.expiration_datetime = now

        self.assertTrue(verified_mode.expiration_datetime_is_explicit)
        self.assertEqual(verified_mode.expiration_datetime, now)

    def test_expiration_datetime_not_explicitly_set(self):
        """ Verify that setting the _expiration_date property does not set the explicit flag. """
        verified_mode, __ = self.create_mode('verified', 'Verified Certificate')
        now = datetime.now()
        verified_mode._expiration_datetime = now  # pylint: disable=protected-access

        self.assertFalse(verified_mode.expiration_datetime_is_explicit)
        self.assertEqual(verified_mode.expiration_datetime, now)

    def test_expiration_datetime_explicitly_set_to_none(self):
        """ Verify that setting the _expiration_date property does not set the explicit flag. """
        verified_mode, __ = self.create_mode('verified', 'Verified Certificate')
        self.assertFalse(verified_mode.expiration_datetime_is_explicit)

        verified_mode.expiration_datetime = None
        self.assertFalse(verified_mode.expiration_datetime_is_explicit)
        self.assertIsNone(verified_mode.expiration_datetime)

    @ddt.data(
        (CourseMode.AUDIT, False),
        (CourseMode.HONOR, True),
        (CourseMode.VERIFIED, True),
        (CourseMode.CREDIT_MODE, True),
        (CourseMode.PROFESSIONAL, True),
        (CourseMode.NO_ID_PROFESSIONAL_MODE, True),
    )
    @ddt.unpack
    def test_eligible_for_cert(self, mode_slug, expected_eligibility):
        """Verify that non-audit modes are eligible for a cert."""
        self.assertEqual(CourseMode.is_eligible_for_certificate(mode_slug), expected_eligibility)
