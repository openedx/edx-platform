"""
Test the behavior of the GradesTransformer
"""

import datetime
import pytz

from student.tests.factories import UserFactory
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.course_blocks.transformers.tests.helpers import CourseStructureTestCase
from ..transformers import GradesBlockTransformer


class GradesBlockTransformerTestCase(CourseStructureTestCase):
    """
    Verify behavior of the GradesBlockTransformer
    """

    TRANSFORMER_CLASS_TO_TEST = GradesBlockTransformer

    problem_metadata = {
        u'graded': True,
        u'weight': 1,
        u'due': datetime.datetime(2099, 03, 15, 12, 30, 00, tzinfo=pytz.utc),
    }

    def setUp(self):
        super(GradesBlockTransformerTestCase, self).setUp()
        password = u'test'
        self.student = UserFactory.create(is_staff=False, username=u'test_student', password=password)
        self.client.login(username=self.student.username, password=password)

    def assert_collected_xblock_fields(self, block_structure, usage_key, **expectations):
        """
        Given a block structure, a block usage key, and a list of keyword
        arguments representing XBlock fields, verify that the block structure
        has the specified values for each XBlock field.
        """
        self.assertGreater(len(expectations), 0)
        for field in expectations:
            self.assertEqual(
                expectations[field],
                block_structure.get_xblock_field(usage_key, field),
            )

    def assert_collected_transformer_block_fields(self, block_structure, usage_key, transformer_class, **expectations):
        """
        Given a block structure, a block usage key, a transformer, and a list
        of keyword arguments representing transformer block fields, verify that
        the block structure has the specified values for each transformer block
        field.
        """
        self.assertGreater(len(expectations), 0)
        for field in expectations:
            self.assertEqual(
                expectations[field],
                block_structure.get_transformer_block_field(usage_key, transformer_class, field),
            )

    def build_course_with_problems(self, data='<problem></problem>', metadata=None):
        """
        Create a test course with the requested problem `data` and `metadata` values.

        Appropriate defaults are provided when either argument is omitted.
        """
        metadata = metadata or self.problem_metadata
        return self.build_course([
            {
                u'org': u'GradesBlockTestOrg',
                u'course': u'GB101',
                u'run': u'cannonball',
                u'#type': u'course',
                u'#ref': u'course',
                u'#children': [
                    {
                        u'metadata': metadata,
                        u'#type': u'problem',
                        u'#ref': u'problem',
                        u'data': data,
                    }
                ]
            }
        ])

    def test_grades_collected_basic(self):

        blocks = self.build_course_with_problems()
        block_structure = get_course_blocks(self.student, blocks[u'course'].location, self.transformers)

        self.assert_collected_xblock_fields(
            block_structure,
            blocks['problem'].location,
            weight=self.problem_metadata[u'weight'],
            graded=self.problem_metadata[u'graded'],
            has_score=True,
            due=self.problem_metadata[u'due'],
        )

    def test_collecting_staff_only_problem(self):
        problem_metadata = {
            u'graded': True,
            u'weight': 1,
            u'due': datetime.datetime(2016, 10, 16, 00, 04, 00, tzinfo=pytz.utc),
            u'visible_to_staff_only': True,
        }

        blocks = self.build_course_with_problems(metadata=problem_metadata)
        block_structure = get_course_blocks(self.student, blocks[u'course'].location, self.transformers)

        self.assert_collected_xblock_fields(
            block_structure,
            blocks['problem'].location,
            weight=problem_metadata[u'weight'],
            graded=problem_metadata[u'graded'],
            has_score=True,
            due=problem_metadata[u'due'],
        )

    def test_max_score_collection(self):
        problem_data = u'''
            <problem>
                <numericalresponse answer="2">
                    <textline label="1+1" trailing_text="%" />
                </numericalresponse>
            </problem>
        '''

        blocks = self.build_course_with_problems(data=problem_data)
        block_structure = get_course_blocks(self.student, blocks[u'course'].location, self.transformers)

        self.assert_collected_transformer_block_fields(
            block_structure,
            blocks[u'problem'].location,
            self.TRANSFORMER_CLASS_TO_TEST,
            max_score=1,
        )

    def test_max_score_for_multiresponse_problem(self):
        problem_data = u'''
            <problem>
                <numericalresponse answer="27">
                    <textline label="3^3" />
                </numericalresponse>
                <numericalresponse answer="13.5">
                    <textline label="and then half of that?" />
                </numericalresponse>
            </problem>
        '''

        blocks = self.build_course_with_problems(problem_data)
        block_structure = get_course_blocks(self.student, blocks[u'course'].location, self.transformers)

        self.assert_collected_transformer_block_fields(
            block_structure,
            blocks[u'problem'].location,
            self.TRANSFORMER_CLASS_TO_TEST,
            max_score=2,
        )
