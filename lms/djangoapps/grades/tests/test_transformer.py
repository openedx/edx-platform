"""
Test the behavior of the GradesTransformer
"""

import datetime
import pytz
import random

from student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import check_mongo_calls

from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.course_blocks.transformers.tests.helpers import CourseStructureTestCase, BlockParentsMapTestCase
from openedx.core.djangoapps.content.block_structure.api import get_cache
from ..transformer import GradesTransformer


class GradesTransformerTestCase(CourseStructureTestCase):
    """
    Verify behavior of the GradesTransformer
    """

    TRANSFORMER_CLASS_TO_TEST = GradesTransformer

    problem_metadata = {
        u'graded': True,
        u'weight': 1,
        u'due': datetime.datetime(2099, 3, 15, 12, 30, 0, tzinfo=pytz.utc),
    }

    def setUp(self):
        super(GradesTransformerTestCase, self).setUp()
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
            # Append our custom message to the default assertEqual error message
            self.longMessage = True  # pylint: disable=invalid-name
            self.assertEqual(
                expectations[field],
                block_structure.get_xblock_field(usage_key, field),
                msg=u'in field {},'.format(repr(field)),
            )
        self.assertIsNotNone(
            block_structure.get_xblock_field(usage_key, u'subtree_edited_on'),
        )

    def assert_collected_transformer_block_fields(self, block_structure, usage_key, transformer_class, **expectations):
        """
        Given a block structure, a block usage key, a transformer, and a list
        of keyword arguments representing transformer block fields, verify that
        the block structure has the specified values for each transformer block
        field.
        """
        self.assertGreater(len(expectations), 0)
        # Append our custom message to the default assertEqual error message
        self.longMessage = True  # pylint: disable=invalid-name
        for field in expectations:
            self.assertEqual(
                expectations[field],
                block_structure.get_transformer_block_field(usage_key, transformer_class, field),
                msg=u'in {} and field {}'.format(transformer_class, repr(field)),
            )

    def build_course_with_problems(self, data='<problem></problem>', metadata=None):
        """
        Create a test course with the requested problem `data` and `metadata` values.

        Appropriate defaults are provided when either argument is omitted.
        """
        metadata = metadata or self.problem_metadata

        # Special structure-related keys start with '#'.  The rest get passed as
        # kwargs to Factory.create.  See docstring at
        # `CourseStructureTestCase.build_course` for details.
        return self.build_course([
            {
                u'org': u'GradesTestOrg',
                u'course': u'GB101',
                u'run': u'cannonball',
                u'metadata': {u'format': u'homework'},
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

    def build_complicated_hypothetical_course(self):
        """
        Create a test course with a very odd structure as a stress-test for various methods.

        Current design is to test containing_subsection logic in collect_unioned_set_field.
        I can't reasonably draw this in ascii art (due to intentional complexities), so here's an overview:
            We have 1 course, containing 1 chapter, containing 2 subsections.

            From here, it starts to get hairy. Call our subsections A and B.
            Subsection A contains 3 verticals (call them 1, 2, and 3), and another subsection (C)
            Subsection B contains vertical 3 and subsection C
            Subsection C contains 1 problem (b)
            Vertical 1 contains 1 vertical (11)
            Vertical 2 contains no children
            Vertical 3 contains no children
            Vertical 11 contains 1 problem (aa) and vertical 2
            Problem b contains no children
        """
        return self.build_course([
            {
                u'org': u'GradesTestOrg',
                u'course': u'GB101',
                u'run': u'cannonball',
                u'metadata': {u'format': u'homework'},
                u'#type': u'course',
                u'#ref': u'course',
                u'#children': [
                    {
                        u'#type': u'chapter',
                        u'#ref': u'chapter',
                        u'#children': [
                            {
                                u'#type': u'sequential',
                                u'#ref': 'sub_A',
                                u'#children': [
                                    {
                                        u'#type': u'vertical',
                                        u'#ref': 'vert_1',
                                        u'#children': [
                                            {
                                                u'#type': u'vertical',
                                                u'#ref': u'vert_A11',
                                                u'#children': [{u'#type': u'problem', u'#ref': u'prob_A1aa'}]
                                            },
                                        ]
                                    },
                                    {u'#type': u'vertical', u'#ref': 'vert_2', '#parents': [u'vert_A11']},
                                ]
                            },
                            {
                                u'#type': u'sequential',
                                u'#ref': u'sub_B',
                                u'#children': [
                                    {u'#type': u'vertical', u'#ref': 'vert_3', '#parents': ['sub_A']},
                                    {
                                        u'#type': u'sequential',
                                        u'#ref': 'sub_C',
                                        '#parents': ['sub_A'],
                                        u'#children': [{u'#type': u'problem', u'#ref': u'prob_BCb'}]
                                    },
                                ]
                            },
                        ]
                    }
                ]
            }
        ])

    def test_collect_containing_subsection(self):
        blocks = self.build_complicated_hypothetical_course()

    def test_ungraded_block_collection(self):
        blocks = self.build_course_with_problems()
        block_structure = get_course_blocks(self.student, blocks[u'course'].location, self.transformers)
        self.assert_collected_xblock_fields(
            block_structure,
            blocks[u'course'].location,
            weight=None,
            graded=False,
            has_score=False,
            due=None,
            format=u'homework',
        )
        self.assert_collected_transformer_block_fields(
            block_structure,
            blocks[u'course'].location,
            self.TRANSFORMER_CLASS_TO_TEST,
            max_score=None,
        )

    def test_grades_collected_basic(self):

        blocks = self.build_course_with_problems()
        block_structure = get_course_blocks(self.student, blocks[u'course'].location, self.transformers)

        self.assert_collected_xblock_fields(
            block_structure,
            blocks[u'problem'].location,
            weight=self.problem_metadata[u'weight'],
            graded=self.problem_metadata[u'graded'],
            has_score=True,
            due=self.problem_metadata[u'due'],
            format=None,
        )

    def test_collecting_staff_only_problem(self):
        # Demonstrate that the problem data can by collected by the SystemUser
        # even if the block has access restrictions placed on it.
        problem_metadata = {
            u'graded': True,
            u'weight': 1,
            u'due': datetime.datetime(2016, 10, 16, 0, 4, 0, tzinfo=pytz.utc),
            u'visible_to_staff_only': True,
        }

        blocks = self.build_course_with_problems(metadata=problem_metadata)
        block_structure = get_course_blocks(self.student, blocks[u'course'].location, self.transformers)

        self.assert_collected_xblock_fields(
            block_structure,
            blocks[u'problem'].location,
            weight=problem_metadata[u'weight'],
            graded=problem_metadata[u'graded'],
            has_score=True,
            due=problem_metadata[u'due'],
            format=None,
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

    def test_course_version_not_collected_in_old_mongo(self):
        blocks = self.build_course_with_problems()
        block_structure = get_course_blocks(self.student, blocks[u'course'].location, self.transformers)
        self.assertIsNone(block_structure.get_xblock_field(blocks[u'course'].location, u'course_version'))

    def test_course_version_collected_in_split(self):
        with self.store.default_store(ModuleStoreEnum.Type.split):
            blocks = self.build_course_with_problems()
        block_structure = get_course_blocks(self.student, blocks[u'course'].location, self.transformers)
        self.assertIsNotNone(block_structure.get_xblock_field(blocks[u'course'].location, u'course_version'))


class MultiProblemModulestoreAccessTestCase(CourseStructureTestCase, SharedModuleStoreTestCase):
    """
    Test mongo usage in GradesTransformer.
    """

    TRANSFORMER_CLASS_TO_TEST = GradesTransformer

    def setUp(self):
        super(MultiProblemModulestoreAccessTestCase, self).setUp()
        password = u'test'
        self.student = UserFactory.create(is_staff=False, username=u'test_student', password=password)
        self.client.login(username=self.student.username, password=password)

    def test_modulestore_performance(self):
        """
        Test that a constant number of mongo calls are made regardless of how
        many grade-related blocks are in the course.
        """
        course = [
            {
                u'org': u'GradesTestOrg',
                u'course': u'GB101',
                u'run': u'cannonball',
                u'metadata': {u'format': u'homework'},
                u'#type': u'course',
                u'#ref': u'course',
                u'#children': [],
            },
        ]
        for problem_number in xrange(random.randrange(10, 20)):
            course[0][u'#children'].append(
                {
                    u'metadata': {
                        u'graded': True,
                        u'weight': 1,
                        u'due': datetime.datetime(2099, 3, 15, 12, 30, 0, tzinfo=pytz.utc),
                    },
                    u'#type': u'problem',
                    u'#ref': u'problem_{}'.format(problem_number),
                    u'data': u'''
                        <problem>
                            <numericalresponse answer="{number}">
                                <textline label="1*{number}" />
                            </numericalresponse>
                        </problem>'''.format(number=problem_number),
                }
            )
        blocks = self.build_course(course)
        get_cache().clear()
        with check_mongo_calls(2):
            get_course_blocks(self.student, blocks[u'course'].location, self.transformers)
