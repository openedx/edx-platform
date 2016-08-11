"""Tests for self-paced course due date overrides."""
# pylint: disable=missing-docstring
import datetime
import pytz

from django.test.utils import override_settings
from mock import patch

from courseware.tests.factories import BetaTesterFactory
from courseware.access import has_access
from lms.djangoapps.ccx.tests.test_overrides import inject_field_overrides
from lms.djangoapps.django_comment_client.utils import get_accessible_discussion_xblocks
from lms.djangoapps.courseware.field_overrides import OverrideFieldData, OverrideModulestoreFieldData
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@override_settings(
    XBLOCK_FIELD_DATA_WRAPPERS=['lms.djangoapps.courseware.field_overrides:OverrideModulestoreFieldData.wrap'],
    MODULESTORE_FIELD_OVERRIDE_PROVIDERS=['courseware.self_paced_overrides.SelfPacedDateOverrideProvider'],
)
class SelfPacedDateOverrideTest(ModuleStoreTestCase):
    """
    Tests for self-paced due date overrides.
    """

    def setUp(self):
        self.reset_setting_cache_variables()
        super(SelfPacedDateOverrideTest, self).setUp()

        SelfPacedConfiguration(enabled=True).save()

        self.non_staff_user, __ = self.create_non_staff_user()
        self.now = datetime.datetime.now(pytz.UTC).replace(microsecond=0)
        self.future = self.now + datetime.timedelta(days=30)

    def tearDown(self):
        self.reset_setting_cache_variables()
        super(SelfPacedDateOverrideTest, self).tearDown()

    def reset_setting_cache_variables(self):
        """
        The overridden settings for this class get cached on class variables.
        Reset those to None before and after running the test to ensure clean
        behavior.
        """
        OverrideFieldData.provider_classes = None
        OverrideModulestoreFieldData.provider_classes = None

    def setup_course(self, **course_kwargs):
        """Set up a course with provided course attributes.

        Creates a child block with a due date, and ensures that field
        overrides are correctly applied for both blocks.
        """
        course = CourseFactory.create(**course_kwargs)
        section = ItemFactory.create(parent=course, due=self.now)
        inject_field_overrides((course, section), course, self.user)
        return (course, section)

    def create_discussion_xblocks(self, parent):
        # Create a released discussion xblock
        ItemFactory.create(
            parent=parent,
            category='discussion',
            display_name='released',
            start=self.now,
        )

        # Create a scheduled discussion xblock
        ItemFactory.create(
            parent=parent,
            category='discussion',
            display_name='scheduled',
            start=self.future,
        )

    def test_instructor_paced_due_date(self):
        __, ip_section = self.setup_course(display_name="Instructor Paced Course", self_paced=False)
        self.assertEqual(ip_section.due, self.now)

    def test_self_paced_due_date(self):
        __, sp_section = self.setup_course(display_name="Self-Paced Course", self_paced=True)
        self.assertIsNone(sp_section.due)

    def test_self_paced_disabled_due_date(self):
        SelfPacedConfiguration(enabled=False).save()
        __, sp_section = self.setup_course(display_name="Self-Paced Course", self_paced=True)
        self.assertEqual(sp_section.due, self.now)

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
        self.assertTrue(self_paced_course.self_paced)
        self.assertEqual(self_paced_course.start, one_month_from_now)
        self.assertIsNone(self_paced_section.start)

        # Verify that non-staff user do not have access to the course
        self.assertFalse(has_access(self.non_staff_user, 'load', self_paced_course))

        # Verify beta tester can access the course as well as the course sections
        self.assertTrue(has_access(beta_tester, 'load', self_paced_course))
        self.assertTrue(has_access(beta_tester, 'load', self_paced_section, self_paced_course.id))

    @patch.dict('courseware.access.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_instructor_paced_discussion_xblock_visibility(self):
        """
        Verify that discussion xblocks scheduled for release in the future are
        not visible to students in an instructor-paced course.
        """
        course, section = self.setup_course(start=self.now, self_paced=False)
        self.create_discussion_xblocks(section)

        # Only the released xblocks should be visible when the course is instructor-paced.
        xblocks = get_accessible_discussion_xblocks(course, self.non_staff_user)
        self.assertTrue(
            all(xblock.display_name == 'released' for xblock in xblocks)
        )

    @patch.dict('courseware.access.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_self_paced_discussion_xblock_visibility(self):
        """
        Regression test. Verify that discussion xblocks scheduled for release
        in the future are visible to students in a self-paced course.
        """
        course, section = self.setup_course(start=self.now, self_paced=True)
        self.create_discussion_xblocks(section)

        # The scheduled xblocks should be visible when the course is self-paced.
        xblocks = get_accessible_discussion_xblocks(course, self.non_staff_user)
        self.assertEqual(len(xblocks), 2)
        self.assertTrue(
            any(xblock.display_name == 'scheduled' for xblock in xblocks)
        )
