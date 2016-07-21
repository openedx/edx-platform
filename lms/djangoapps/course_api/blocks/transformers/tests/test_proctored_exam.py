"""
Tests for ProctoredExamTransformer.
"""
from mock import patch
from nose.plugins.attrib import attr

import ddt
from edx_proctoring.api import (
    create_exam,
    create_exam_attempt,
    update_attempt_status
)
from edx_proctoring.models import ProctoredExamStudentAttemptStatus
from edx_proctoring.runtime import set_runtime_service
from edx_proctoring.tests.test_services import MockCreditService
from lms.djangoapps.course_blocks.transformers.tests.helpers import CourseStructureTestCase
from student.tests.factories import CourseEnrollmentFactory

from ..proctored_exam import ProctoredExamTransformer
from ...api import get_course_blocks


@attr('shard_3')
@ddt.ddt
@patch.dict('django.conf.settings.FEATURES', {'ENABLE_PROCTORED_EXAMS': True})
class ProctoredExamTransformerTestCase(CourseStructureTestCase):
    """
    Test behavior of ProctoredExamTransformer
    """
    TRANSFORMER_CLASS_TO_TEST = ProctoredExamTransformer

    def setUp(self):
        """
        Setup course structure and create user for split test transformer test.
        """
        super(ProctoredExamTransformerTestCase, self).setUp()

        # Set up proctored exam

        # Build course.
        self.course_hierarchy = self.get_course_hierarchy()
        self.blocks = self.build_course(self.course_hierarchy)
        self.course = self.blocks['course']

        # Enroll user in course.
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, is_active=True)

    def setup_proctored_exam(self, block, attempt_status, user_id):
        """
        Test helper to configure the given block as a proctored exam.
        """
        exam_id = create_exam(
            course_id=unicode(block.location.course_key),
            content_id=unicode(block.location),
            exam_name='foo',
            time_limit_mins=10,
            is_proctored=True,
            is_practice_exam=block.is_practice_exam,
        )

        set_runtime_service(
            'credit',
            MockCreditService(enrollment_mode='verified')
        )

        create_exam_attempt(exam_id, user_id, taking_as_proctored=True)
        update_attempt_status(exam_id, user_id, attempt_status)

    ALL_BLOCKS = ('course', 'A', 'B', 'C', 'TimedExam', 'D', 'E', 'PracticeExam', 'F', 'G')

    def get_course_hierarchy(self):
        """
        Get a course hierarchy to test with.
        """

        #                  course
        #               /    |    \
        #              /     |     \
        #            A     Exam1   Exam2
        #          /  \     / \      / \
        #         /   \    /   \    /   \
        #        B    C   D     E  F    G
        #
        return [
            {
                'org': 'ProctoredExamTransformer',
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
                '#ref': 'TimedExam',
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
        ]

    def test_exam_not_created(self):
        block_structure = get_course_blocks(
            self.user,
            self.course.location,
            self.transformers,
        )
        self.assertEqual(
            set(block_structure.get_block_keys()),
            set(self.get_block_key_set(self.blocks, *self.ALL_BLOCKS)),
        )

    @ddt.data(
        (
            'TimedExam',
            ProctoredExamStudentAttemptStatus.declined,
            ALL_BLOCKS,
        ),
        (
            'TimedExam',
            ProctoredExamStudentAttemptStatus.submitted,
            ('course', 'A', 'B', 'C', 'PracticeExam', 'F', 'G'),
        ),
        (
            'TimedExam',
            ProctoredExamStudentAttemptStatus.rejected,
            ('course', 'A', 'B', 'C', 'PracticeExam', 'F', 'G'),
        ),
        (
            'PracticeExam',
            ProctoredExamStudentAttemptStatus.declined,
            ALL_BLOCKS,
        ),
        (
            'PracticeExam',
            ProctoredExamStudentAttemptStatus.rejected,
            ('course', 'A', 'B', 'C', 'TimedExam', 'D', 'E'),
        ),
    )
    @ddt.unpack
    def test_exam_created(self, exam_ref, attempt_status, expected_blocks):
        self.setup_proctored_exam(self.blocks[exam_ref], attempt_status, self.user.id)
        block_structure = get_course_blocks(
            self.user,
            self.course.location,
            self.transformers,
        )
        self.assertEqual(
            set(block_structure.get_block_keys()),
            set(self.get_block_key_set(self.blocks, *expected_blocks)),
        )
