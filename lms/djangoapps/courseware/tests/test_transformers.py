"""
Test the behavior of the GradesTransformer
"""

from student.tests.factories import UserFactory

from lms.djangoapps.course_blocks.api import get_course_blocks
from ..transformers import GradesBlockTransformer
from lms.djangoapps.course_blocks.transformers.tests.helpers import CourseStructureTestCase


class GradesBlockTransformerTestCase(CourseStructureTestCase):
    """
    Verify behavior of the GradesBlockTransformer
    """

    course_dict = [
        {
            u'org': u'GradesBlockTestOrg',
            u'course': u'GB101',
            u'run': u'cannonball',
            u'#type': u'course',
            u'#ref': u'course',
            u'#children': [
                {
                    u'metadata': {
                        u'graded': True,
                        u'weight': 1,
                        u'has_score': True,
                        u'due': u'2099-03-15T12:30:00+00:00',
                    },
                    u'#type': u'problem',
                    u'#ref': u'problem_1',
                    u'data': u'''
                        <problem>
                            <numericalresponse answer="2">
                                <textline label="1+1" trailing_text="%" />
                            </numericalresponse>
                        </problem>''',
                },
                {
                    u'metadata': {
                        u'graded': False,
                        u'weight': 2,
                        u'has_score': True,
                        u'due': u'2099-10-31T23:59:59+00:00',
                        u'visible_to_staff_only': True,
                    },
                    u'#type': u'problem',
                    u'#ref': u'problem_2',
                    u'data': u'''
                        <problem>
                            <numericalresponse answer="27">
                                <textline label="3^3" />
                            </numericalresponse>
                            <numericalresponse answer="13.5">
                                <textline label="and then half of that?" />
                            </numericalresponse>
                        </problem>''',
                },
            ],
        },
    ]

    expected_max_score = {
        u'problem_1': 1,
        u'problem_2': 2,
    }
    TRANSFORMER_CLASS_TO_TEST = GradesBlockTransformer

    def setUp(self):
        super(GradesBlockTransformerTestCase, self).setUp()
        self.blocks = self.build_course(self.course_dict)
        self.course = self.blocks[u'course']

    def test_grades_collected(self):
        password = u'test'
        student = UserFactory.create(is_staff=False, username=u'test_student', password=password)
        self.client.login(username=student.username, password=password)
        block_structure = get_course_blocks(student, self.course.location, self.transformers)

        problem_expectations = self.course_dict[0][u'#children']
        for problem, expected_result in [
                (self.blocks[u'problem_1'], problem_expectations[0]),
                (self.blocks[u'problem_2'], problem_expectations[1]),
        ]:
            for field in [u'weight', u'graded', u'has_score']:
                self.assertEqual(
                    expected_result[u'metadata'].get(field),
                    block_structure.get_xblock_field(problem.location, field),
                )
            self.assertEqual(
                expected_result[u'metadata'].get(u'due'),
                block_structure.get_xblock_field(problem.location, u'due').isoformat(),
            )
            max_score = block_structure.get_transformer_block_field(
                problem.location,
                GradesBlockTransformer,
                'max_score'
            )
            self.assertEqual(self.expected_max_score[expected_result[u'#ref']], max_score)
