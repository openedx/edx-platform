"""
Tests for self-paced course due date overrides.
"""

from datetime import datetime
from dateutil.tz import tzutc
from django.test.utils import override_settings

from student.tests.factories import UserFactory
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
        self.due_date = datetime(2015, 5, 26, 8, 30, 00).replace(tzinfo=tzutc())

    def tearDown(self):
        super(SelfPacedDateOverrideTest, self).tearDown()
        OverrideFieldData.provider_classes = None

    def setup_course(self, display_name, self_paced):
        """Set up a course with `display_name` and `self_paced` attributes.

        Creates a child block with a due date, and ensures that field
        overrides are correctly applied for both blocks.
        """
        course = CourseFactory.create(display_name=display_name, self_paced=self_paced)
        section = ItemFactory.create(parent=course, due=self.due_date)
        inject_field_overrides((course, section), course, UserFactory.create())
        return (course, section)

    def test_instructor_paced(self):
        __, ip_section = self.setup_course("Instructor Paced Course", False)
        self.assertEqual(self.due_date, ip_section.due)

    def test_self_paced(self):
        __, sp_section = self.setup_course("Self-Paced Course", True)
        self.assertIsNone(sp_section.due)

    def test_self_paced_disabled(self):
        SelfPacedConfiguration(enabled=False).save()
        __, sp_section = self.setup_course("Self-Paced Course", True)
        self.assertEqual(self.due_date, sp_section.due)
