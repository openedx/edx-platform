"""
Tests for RandomizeTransformer.
"""
import mock
from student.tests.factories import UserFactory
from student.tests.factories import CourseEnrollmentFactory

from course_blocks.transformers.randomize import RandomizeTransformer
from course_blocks.api import get_course_blocks, clear_course_from_cache
from lms.djangoapps.course_blocks.transformers.tests.test_helpers import CourseStructureTestCase


class MockedModules(object):
    """
    Object with mocked chosen module for user.
    """
    def __init__(self, state):
        """
        Set state attribute on initialize.
        """
        self.state = state


class RandomizeTransformerTestCase(CourseStructureTestCase):
    """
    RandomizeTransformer Test
    """

    def setUp(self):
        """
        Setup course structure and create user for randomize transformer test.
        """
        super(RandomizeTransformerTestCase, self).setUp()

        # Build course.
        self.course_hierarchy = self.get_test_course_hierarchy()
        self.blocks = self.build_course(self.course_hierarchy)
        self.course = self.blocks['course']
        clear_course_from_cache(self.course.id)

        # Set up user and enroll in course.
        self.password = 'test'
        self.user = UserFactory.create(password=self.password)
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, is_active=True)

        self.chosen_module = [MockedModules('{"choice": 1}')]
        self.transformer = []

    def get_test_course_hierarchy(self):
        """
        Get a course hierarchy to test with.
        """
        return {
            'org': 'RandomizeTransformer',
            'course': 'RT101F',
            'run': 'test_run',
            '#ref': 'course',
            '#children': [
                {
                    '#type': 'chapter',
                    '#ref': 'chapter1',
                    '#children': [
                        {
                            '#type': 'sequential',
                            '#ref': 'lesson1',
                            '#children': [
                                {
                                    '#type': 'vertical',
                                    '#ref': 'vertical1',
                                    '#children': [
                                        {
                                            'metadata': {'category': 'randomize'},
                                            '#type': 'randomize',
                                            '#ref': 'randomize1',
                                            '#children': [
                                                {
                                                    'metadata': {'display_name': "HTML1"},
                                                    '#type': 'html',
                                                    '#ref': 'html1',
                                                },
                                                {
                                                    'metadata': {'display_name': "HTML2"},
                                                    '#type': 'html',
                                                    '#ref': 'html2',
                                                }
                                            ]
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ]
        }

    def test_course_structure_with_user_randomize(self):
        """
        Test course structure integrity if course has randomize block section.
        First test user can't see any randomize block section,
        and after that mock response from MySQL db.
        Check user can see mocked section in randomize block.
        """
        self.transformer = RandomizeTransformer()

        raw_block_structure = get_course_blocks(
            self.user,
            self.course.id,
            self.course.location,
            transformers={}
        )
        self.assertEqual(len(list(raw_block_structure.get_block_keys())), len(self.blocks))

        clear_course_from_cache(self.course.id)
        trans_block_structure = get_course_blocks(
            self.user,
            self.course.id,
            self.course.location,
            transformers={self.transformer}
        )

        self.assertEqual(
            set(trans_block_structure.get_block_keys()),
            self.get_block_key_set('course', 'chapter1', 'lesson1', 'vertical1', 'randomize1')
        )

        # Check course structure again, with mocked selected modules for a user.
        with mock.patch(
            'course_blocks.transformers.randomize.RandomizeTransformer._get_chosen_modules',
            return_value=self.chosen_module
        ):
            clear_course_from_cache(self.course.id)
            trans_block_structure = get_course_blocks(
                self.user,
                self.course.id,
                self.course.location,
                transformers={self.transformer}
            )
            self.assertEqual(
                set(trans_block_structure.get_block_keys()),
                self.get_block_key_set(
                    'course',
                    'chapter1',
                    'lesson1',
                    'vertical1',
                    'randomize1',
                    'html2'
                )
            )
