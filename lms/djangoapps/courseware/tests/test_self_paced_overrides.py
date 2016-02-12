"""
Tests for self-paced course due date overrides.
"""

import datetime
import pytz

from dateutil.tz import tzutc
from django.test.utils import override_settings
from mock import patch

from courseware.tests.factories import BetaTesterFactory
from courseware.access import has_access

from lms.djangoapps.ccx.tests.test_overrides import inject_field_overrides
from lms.djangoapps.courseware.field_overrides import OverrideFieldData
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@override_settings(
    FIELD_OVERRIDE_PROVIDERS=('courseware.self_paced_overrides.SelfPacedDateOverrideProvider',)
)
class SelfPacedDateOverrideTest(ModuleStoreTestCase):
    """
    Tests for self-paced due date overrides.
    """

    def setUp(self):
        SelfPacedConfiguration(enabled=True).save()
        super(SelfPacedDateOverrideTest, self).setUp()
        self.due_date = datetime.datetime(2015, 5, 26, 8, 30, 00).replace(tzinfo=tzutc())
        self.non_staff_user, __ = self.create_non_staff_user()

    def tearDown(self):
        super(SelfPacedDateOverrideTest, self).tearDown()
        OverrideFieldData.provider_classes = None

    def setup_course(self, **course_kwargs):
        """Set up a course with provided course attributes.

        Creates a child block with a due date, and ensures that field
        overrides are correctly applied for both blocks.
        """
        course = CourseFactory.create(**course_kwargs)
        section = ItemFactory.create(parent=course, due=self.due_date)
        inject_field_overrides((course, section), course, self.user)
        return (course, section)

    def test_instructor_paced(self):
        __, ip_section = self.setup_course(display_name="Instructor Paced Course", self_paced=False)
        self.assertEqual(self.due_date, ip_section.due)

    def test_self_paced(self):
        __, sp_section = self.setup_course(display_name="Self-Paced Course", self_paced=True)
        self.assertIsNone(sp_section.due)

    def test_self_paced_disabled(self):
        SelfPacedConfiguration(enabled=False).save()
        __, sp_section = self.setup_course(display_name="Self-Paced Course", self_paced=True)
        self.assertEqual(self.due_date, sp_section.due)

    @patch.dict('courseware.access.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_course_access_to_beta_users(self):
        """
        Test that beta testers can access `self_paced` course prior to start date.
        """
        now = datetime.datetime.now(pytz.UTC)
        one_month_from_now = now + datetime.timedelta(days=30)
        course_options = {
            'days_early_for_beta': 100,
            'self_paced': True,
            'start': one_month_from_now,
        }
        # Create a `self_paced` course and add a beta tester in it
        self_paced_course, self_paced_section = self.setup_course(**course_options)
        beta_tester = BetaTesterFactory(course_key=self_paced_course.id)

        # Verify course is `self_paced` and course has start date but not section.
        self.assertTrue(self_paced_course.self_paced, "Course is self_paced")
        self.assertEqual(self_paced_course.start, one_month_from_now, "Course has start date")
        self.assertIsNone(self_paced_section.start, "Section start date is None")

        # Verify that non-staff user do not have access to the course
        self.assertFalse(has_access(self.non_staff_user, 'load', self_paced_course))

        # Verify beta tester can access the course as well as the course sections
        self.assertTrue(has_access(beta_tester, 'load', self_paced_course))
        self.assertTrue(has_access(beta_tester, 'load', self_paced_section, self_paced_course.id))
