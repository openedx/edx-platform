"""
Tests for Reverification models
"""
from datetime import timedelta, datetime
import pytz

from django.core.exceptions import ValidationError
from django.test.utils import override_settings

from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from reverification.models import MidcourseReverificationWindow
from reverification.tests.factories import MidcourseReverificationWindowFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestMidcourseReverificationWindow(ModuleStoreTestCase):
    """ Tests for MidcourseReverificationWindow objects """

    def setUp(self, **kwargs):
        super(TestMidcourseReverificationWindow, self).setUp()
        self.course_id = CourseFactory.create().id

    def test_window_open_for_course(self):
        # Should return False if no windows exist for a course
        self.assertFalse(MidcourseReverificationWindow.window_open_for_course(self.course_id))

        # Should return False if a window exists, but it's not in the current timeframe
        MidcourseReverificationWindowFactory(
            course_id=self.course_id,
            start_date=datetime.now(pytz.utc) - timedelta(days=10),
            end_date=datetime.now(pytz.utc) - timedelta(days=5)
        )
        self.assertFalse(MidcourseReverificationWindow.window_open_for_course(self.course_id))

        # Should return True if a non-expired window exists
        MidcourseReverificationWindowFactory(
            course_id=self.course_id,
            start_date=datetime.now(pytz.utc) - timedelta(days=3),
            end_date=datetime.now(pytz.utc) + timedelta(days=3)
        )
        self.assertTrue(MidcourseReverificationWindow.window_open_for_course(self.course_id))

    def test_get_window(self):
        # if no window exists, returns None
        self.assertIsNone(MidcourseReverificationWindow.get_window(self.course_id, datetime.now(pytz.utc)))

        # we should get the expected window otherwise
        window_valid = MidcourseReverificationWindowFactory(
            course_id=self.course_id,
            start_date=datetime.now(pytz.utc) - timedelta(days=3),
            end_date=datetime.now(pytz.utc) + timedelta(days=3)
        )
        self.assertEquals(
            window_valid,
            MidcourseReverificationWindow.get_window(self.course_id, datetime.now(pytz.utc))
        )

    def test_no_overlapping_windows(self):
        window_valid = MidcourseReverificationWindow(
            course_id=self.course_id,
            start_date=datetime.now(pytz.utc) - timedelta(days=3),
            end_date=datetime.now(pytz.utc) + timedelta(days=3)
        )
        window_valid.save()

        with self.assertRaises(ValidationError):
            window_invalid = MidcourseReverificationWindow(
                course_id=self.course_id,
                start_date=datetime.now(pytz.utc) - timedelta(days=2),
                end_date=datetime.now(pytz.utc) + timedelta(days=4)
            )
            window_invalid.save()
