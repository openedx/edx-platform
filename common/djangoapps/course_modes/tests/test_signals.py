"""
Unit tests for the course_mode signals
"""

from datetime import datetime, timedelta
from mock import patch

import ddt
from pytz import UTC
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from course_modes.models import CourseMode
from course_modes.signals import _listen_for_course_publish


@ddt.ddt
class CourseModeSignalTest(ModuleStoreTestCase):
    """
    Tests for the course_mode course_published signal.
    """

    def setUp(self):
        super(CourseModeSignalTest, self).setUp()
        self.end = datetime.now(tz=UTC).replace(microsecond=0) + timedelta(days=7)
        self.course = CourseFactory.create(end=self.end)
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
            course_id=self.course.id,
            mode_display_name=mode_name,
            mode_slug=mode_slug,
            min_price=min_price,
            suggested_prices=suggested_prices,
            currency=currency,
            _expiration_datetime=expiration_datetime,
        )

    def test_no_verified_mode(self):
        """ Verify expiration not updated by signal for non-verified mode. """
        course_mode, __ = self.create_mode('honor', 'honor')

        _listen_for_course_publish('store', self.course.id)
        course_mode.refresh_from_db()

        self.assertIsNone(course_mode.expiration_datetime)

    @ddt.data(1, 14, 30)
    def test_verified_mode(self, verification_window):
        """ Verify signal updates expiration to configured time period before course end for verified mode. """
        course_mode, __ = self.create_mode('verified', 'verified')
        self.assertIsNone(course_mode.expiration_datetime)

        with patch('course_modes.models.CourseModeExpirationConfig.current') as config:
            instance = config.return_value
            instance.verification_window = timedelta(days=verification_window)

            _listen_for_course_publish('store', self.course.id)
            course_mode.refresh_from_db()

            self.assertEqual(course_mode.expiration_datetime, self.end - timedelta(days=verification_window))

    @ddt.data(1, 14, 30)
    def test_verified_mode_explicitly_set(self, verification_window):
        """ Verify signal does not update expiration for verified mode with explicitly set expiration. """
        course_mode, __ = self.create_mode('verified', 'verified')
        course_mode.expiration_datetime_is_explicit = True
        self.assertIsNone(course_mode.expiration_datetime)

        with patch('course_modes.models.CourseModeExpirationConfig.current') as config:
            instance = config.return_value
            instance.verification_window = timedelta(days=verification_window)

            _listen_for_course_publish('store', self.course.id)
            course_mode.refresh_from_db()

            self.assertEqual(course_mode.expiration_datetime, self.end - timedelta(days=verification_window))
