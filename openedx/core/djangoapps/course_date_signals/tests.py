from datetime import timedelta
import ddt
from unittest.mock import patch

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from . import utils


@ddt.ddt
class SelfPacedDueDatesTests(ModuleStoreTestCase):
    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create()
        for i in range(4):
            ItemFactory(parent=self.course, category="sequential", display_name="Section {}".format(i))

    def test_basic_spacing(self):
        expected_sections = [
            (0, 'Section 0', timedelta(days=7)),
            (1, 'Section 1', timedelta(days=14)),
            (2, 'Section 2', timedelta(days=21)),
            (3, 'Section 3', timedelta(days=28)),
        ]
        with patch.object(utils, 'get_expected_duration', return_value=timedelta(weeks=4)):
            actual = [(idx, section.display_name, offset) for (idx, section, offset) in utils.spaced_out_sections(self.course)]

        self.assertEqual(actual, expected_sections)

    def test_hidden_sections(self):
        for _ in range(2):
            ItemFactory(parent=self.course, category="sequential", visible_to_staff_only=True)
        expected_sections = [
            (0, 'Section 0', timedelta(days=7)),
            (1, 'Section 1', timedelta(days=14)),
            (2, 'Section 2', timedelta(days=21)),
            (3, 'Section 3', timedelta(days=28)),
        ]
        with patch.object(utils, 'get_expected_duration', return_value=timedelta(weeks=4)):
            actual = [(idx, section.display_name, offset) for (idx, section, offset) in utils.spaced_out_sections(self.course)]

        self.assertEqual(actual, expected_sections)
