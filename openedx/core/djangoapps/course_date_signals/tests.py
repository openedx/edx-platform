# lint-amnesty, pylint: disable=missing-module-docstring
from datetime import timedelta
import ddt
from unittest.mock import patch  # lint-amnesty, pylint: disable=wrong-import-order

from openedx.core.djangoapps.course_date_signals.handlers import _gather_graded_items, _has_assignment_blocks
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from . import utils


@ddt.ddt
class SelfPacedDueDatesTests(ModuleStoreTestCase):  # lint-amnesty, pylint: disable=missing-class-docstring
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
            actual = [(idx, section.display_name, offset) for (idx, section, offset) in utils.spaced_out_sections(self.course)]  # lint-amnesty, pylint: disable=line-too-long

        assert actual == expected_sections

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
            actual = [(idx, section.display_name, offset) for (idx, section, offset) in utils.spaced_out_sections(self.course)]  # lint-amnesty, pylint: disable=line-too-long

        assert actual == expected_sections

    def test_dates_for_ungraded_assignments(self):
        """
        _has_assignment_blocks should return true if the argument block
        children leaf nodes include an assignment that is graded and scored
        """
        with modulestore().bulk_operations(self.course.id):
            sequence = ItemFactory(parent=self.course, category="sequential")
            vertical = ItemFactory(parent=sequence, category="vertical")
            sequence = modulestore().get_item(sequence.location)
            assert _has_assignment_blocks(sequence) is False

            # Ungraded problems do not count as assignment blocks
            ItemFactory.create(
                parent=vertical,
                category='problem',
                graded=True,
                weight=0,
            )
            sequence = modulestore().get_item(sequence.location)
            assert _has_assignment_blocks(sequence) is False
            ItemFactory.create(
                parent=vertical,
                category='problem',
                graded=False,
                weight=1,
            )
            sequence = modulestore().get_item(sequence.location)
            assert _has_assignment_blocks(sequence) is False

            # Method will return true after adding a graded, scored assignment block
            ItemFactory.create(
                parent=vertical,
                category='problem',
                graded=True,
                weight=1,
            )
            sequence = modulestore().get_item(sequence.location)
            assert _has_assignment_blocks(sequence) is True

    def test_sequence_with_graded_and_ungraded_assignments(self):
        """
        _gather_graded_items should set a due date of None on ungraded problem blocks
        even if the block has graded siblings in the sequence
        """
        with modulestore().bulk_operations(self.course.id):
            sequence = ItemFactory(parent=self.course, category="sequential")
            vertical = ItemFactory(parent=sequence, category="vertical")
            sequence = modulestore().get_item(sequence.location)
            ItemFactory.create(
                parent=vertical,
                category='problem',
                graded=False,
                weight=1,
            )
            ungraded_problem_2 = ItemFactory.create(
                parent=vertical,
                category='problem',
                graded=True,
                weight=0,
            )
            graded_problem_1 = ItemFactory.create(
                parent=vertical,
                category='problem',
                graded=True,
                weight=1,
            )
            expected_graded_items = [
                (ungraded_problem_2.location, {'due': None}),
                (graded_problem_1.location, {'due': 5}),
            ]
            sequence = modulestore().get_item(sequence.location)
            self.assertCountEqual(_gather_graded_items(sequence, 5), expected_graded_items)
