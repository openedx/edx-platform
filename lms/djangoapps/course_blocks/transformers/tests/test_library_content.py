"""
Tests for ContentLibraryTransformer.
"""
import mock
from student.tests.factories import CourseEnrollmentFactory

from openedx.core.lib.block_structure.transformers import BlockStructureTransformers

from ...api import get_course_blocks, clear_course_from_cache
from ..library_content import ContentLibraryTransformer
from .helpers import CourseStructureTestCase


class MockedModule(object):
    """
    Object with mocked selected modules for user.
    """
    def __init__(self, state):
        """
        Set state attribute on initialize.
        """
        self.state = state


class ContentLibraryTransformerTestCase(CourseStructureTestCase):
    """
    ContentLibraryTransformer Test
    """
    TRANSFORMER_CLASS_TO_TEST = ContentLibraryTransformer

    def setUp(self):
        """
        Setup course structure and create user for content library transformer test.
        """
        super(ContentLibraryTransformerTestCase, self).setUp()

        # Build course.
        self.course_hierarchy = self.get_course_hierarchy()
        self.blocks = self.build_course(self.course_hierarchy)
        self.course = self.blocks['course']
        clear_course_from_cache(self.course.id)

        # Enroll user in course.
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, is_active=True)

    def get_course_hierarchy(self):
        """
        Get a course hierarchy to test with.
        """
        return [{
            'org': 'ContentLibraryTransformer',
            'course': 'CL101F',
            'run': 'test_run',
            '#type': 'course',
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
                                            'metadata': {'category': 'library_content'},
                                            '#type': 'library_content',
                                            '#ref': 'library_content1',
                                            '#children': [
                                                {
                                                    'metadata': {'display_name': "CL Vertical 2"},
                                                    '#type': 'vertical',
                                                    '#ref': 'vertical2',
                                                    '#children': [
                                                        {
                                                            'metadata': {'display_name': "HTML1"},
                                                            '#type': 'html',
                                                            '#ref': 'html1',
                                                        }
                                                    ]
                                                },
                                                {
                                                    'metadata': {'display_name': "CL Vertical 3"},
                                                    '#type': 'vertical',
                                                    '#ref': 'vertical3',
                                                    '#children': [
                                                        {
                                                            'metadata': {'display_name': "HTML2"},
                                                            '#type': 'html',
                                                            '#ref': 'html2',
                                                        }
                                                    ]
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
        }]

    def test_content_library(self):
        """
        Test when course has content library section.
        First test user can't see any content library section,
        and after that mock response from MySQL db.
        Check user can see mocked sections in content library.
        """
        raw_block_structure = get_course_blocks(
            self.user,
            self.course.location,
            transformers=BlockStructureTransformers(),
        )
        self.assertEqual(len(list(raw_block_structure.get_block_keys())), len(self.blocks))

        clear_course_from_cache(self.course.id)
        trans_block_structure = get_course_blocks(
            self.user,
            self.course.location,
            self.transformers,
        )

        # Should dynamically assign a block to student
        trans_keys = set(trans_block_structure.get_block_keys())
        block_key_set = self.get_block_key_set(
            self.blocks, 'course', 'chapter1', 'lesson1', 'vertical1', 'library_content1'
        )
        for key in block_key_set:
            self.assertIn(key, trans_keys)

        vertical2_selected = self.get_block_key_set(self.blocks, 'vertical2').pop() in trans_keys
        vertical3_selected = self.get_block_key_set(self.blocks, 'vertical3').pop() in trans_keys
        self.assertTrue(vertical2_selected or vertical3_selected)

        # Check course structure again, with mocked selected modules for a user.
        with mock.patch(
            'lms.djangoapps.course_blocks.transformers.library_content.ContentLibraryTransformer._get_student_module',
            return_value=MockedModule('{"selected": [["vertical", "vertical_vertical2"]]}'),
        ):
            clear_course_from_cache(self.course.id)
            trans_block_structure = get_course_blocks(
                self.user,
                self.course.location,
                self.transformers,
            )
            self.assertEqual(
                set(trans_block_structure.get_block_keys()),
                self.get_block_key_set(
                    self.blocks,
                    'course',
                    'chapter1',
                    'lesson1',
                    'vertical1',
                    'library_content1',
                    'vertical2',
                    'html1'
                )
            )
