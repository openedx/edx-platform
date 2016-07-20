"""
Tests for ProctoredExamTransformer.
"""
from mock import patch, Mock
from nose.plugins.attrib import attr

import ddt
from gating import api as lms_gating_api
from lms.djangoapps.course_blocks.transformers.tests.helpers import CourseStructureTestCase
from milestones.tests.utils import MilestonesTestCaseMixin
from opaque_keys.edx.keys import UsageKey
from openedx.core.lib.gating import api as gating_api
from student.tests.factories import CourseEnrollmentFactory

from ..milestones import MilestonesTransformer
from ...api import get_course_blocks


@attr('shard_3')
@ddt.ddt
@patch.dict('django.conf.settings.FEATURES', {'ENABLE_SPECIAL_EXAMS': True, 'MILESTONES_APP': True})
class MilestonesTransformerTestCase(CourseStructureTestCase, MilestonesTestCaseMixin):
    """
    Test behavior of ProctoredExamTransformer
    """
    TRANSFORMER_CLASS_TO_TEST = MilestonesTransformer

    def setUp(self):
        """
        Setup course structure and create user for split test transformer test.
        """
        super(MilestonesTransformerTestCase, self).setUp()

        # Build course.
        self.course_hierarchy = self.get_course_hierarchy()
        self.blocks = self.build_course(self.course_hierarchy)
        self.course = self.blocks['course']

        # Enroll user in course.
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, is_active=True)

    def setup_gated_section(self, gated_block, gating_block):
        """
        Test helper to create a gating requirement.
        Args:
            gated_block: The block that should be inaccessible until gating_block is completed
            gating_block: The block that must be completed before access is granted
        """
        gating_api.add_prerequisite(self.course.id, unicode(gating_block.location))
        gating_api.set_required_content(self.course.id, gated_block.location, gating_block.location, 100)

    ALL_BLOCKS = (
        'course', 'A', 'B', 'C', 'ProctoredExam', 'D', 'E', 'PracticeExam', 'F', 'G', 'H', 'I', 'TimedExam', 'J', 'K'
    )

    # The special exams (proctored, practice, timed) should never be visible to students
    ALL_BLOCKS_EXCEPT_SPECIAL = ('course', 'A', 'B', 'C', 'H', 'I')

    def get_course_hierarchy(self):
        """
        Get a course hierarchy to test with.
        """

        #                                course
        #               /       /             \         \   \
        #              /       /               \         \   \
        #            A     ProctoredExam   PracticeExam   H  TimedExam
        #          /  \     / \            / \            |     /  \
        #         /   \    /   \          /   \           |    /    \
        #        B    C   D     E        F    G           I    J     K
        #
        return [
            {
                'org': 'MilestonesTransformer',
                'course': 'PE101F',
                'run': 'test_run',
                '#type': 'course',
                '#ref': 'course',
            },
            {
                '#type': 'sequential',
                '#ref': 'A',
                '#children': [
                    {'#type': 'vertical', '#ref': 'B'},
                    {'#type': 'vertical', '#ref': 'C'},
                ],
            },
            {
                '#type': 'sequential',
                '#ref': 'ProctoredExam',
                'is_time_limited': True,
                'is_proctored_enabled': True,
                'is_practice_exam': False,
                '#children': [
                    {'#type': 'vertical', '#ref': 'D'},
                    {'#type': 'vertical', '#ref': 'E'},
                ],
            },
            {
                '#type': 'sequential',
                '#ref': 'PracticeExam',
                'is_time_limited': True,
                'is_proctored_enabled': True,
                'is_practice_exam': True,
                '#children': [
                    {'#type': 'vertical', '#ref': 'F'},
                    {'#type': 'vertical', '#ref': 'G'},
                ],
            },
            {
                '#type': 'sequential',
                '#ref': 'H',
                '#children': [
                    {'#type': 'vertical', '#ref': 'I'},
                ],
            },
            {
                '#type': 'sequential',
                '#ref': 'TimedExam',
                'is_time_limited': True,
                'is_proctored_enabled': False,
                'is_practice_exam': False,
                '#children': [
                    {'#type': 'vertical', '#ref': 'J'},
                    {'#type': 'vertical', '#ref': 'K'},
                ],
            },
        ]

    def test_special_exams_not_visible_to_non_staff(self):
        self.get_blocks_and_check_against_expected(self.user, self.ALL_BLOCKS_EXCEPT_SPECIAL)

    @ddt.data(
        (
            'H',
            'A',
            'B',
            ('course', 'A', 'B', 'C',)
        ),
        (
            'H',
            'ProctoredExam',
            'D',
            ('course', 'A', 'B', 'C'),
        ),
    )
    @ddt.unpack
    def test_gated(self, gated_block_ref, gating_block_ref, gating_block_child, expected_blocks_before_completion):
        """
        First, checks that a student cannot see the gated block when it is gated by the gating block and no
        attempt has been made to complete the gating block.
        Then, checks that the student can see the gated block after the gating block has been completed.

        expected_blocks_before_completion is the set of blocks we expect to be visible to the student
        before the student has completed the gating block.

        The test data includes one special exam and one non-special block as the gating blocks.
        """
        self.course.enable_subsection_gating = True
        self.setup_gated_section(self.blocks[gated_block_ref], self.blocks[gating_block_ref])
        self.get_blocks_and_check_against_expected(self.user, expected_blocks_before_completion)

        # mock the api that the lms gating api calls to get the score for each block to always return 1 (ie 100%)
        with patch('courseware.grades.get_module_score', Mock(return_value=1)):

            # this call triggers reevaluation of prerequisites fulfilled by the parent of the
            # block passed in, so we pass in a child of the gating block
            lms_gating_api.evaluate_prerequisite(
                self.course,
                UsageKey.from_string(unicode(self.blocks[gating_block_child].location)),
                self.user.id)

        self.get_blocks_and_check_against_expected(self.user, self.ALL_BLOCKS_EXCEPT_SPECIAL)

    def test_staff_access(self):
        """
        Ensures that staff can always access all blocks in the course,
        regardless of gating or proctoring.
        """
        expected_blocks = self.ALL_BLOCKS
        self.setup_gated_section(self.blocks['H'], self.blocks['A'])
        self.get_blocks_and_check_against_expected(self.staff, expected_blocks)

    def get_blocks_and_check_against_expected(self, user, expected_blocks):
        """
        Calls the course API as the specified user and checks the
        output against a specified set of expected blocks.
        """
        block_structure = get_course_blocks(
            user,
            self.course.location,
            self.transformers,
        )
        self.assertEqual(
            set(block_structure.get_block_keys()),
            set(self.get_block_key_set(self.blocks, *expected_blocks)),
        )
