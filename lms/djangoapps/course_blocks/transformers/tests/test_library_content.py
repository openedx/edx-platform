"""
Tests for ContentLibraryTransformer and AdaptiveContentLibraryTransformer.
"""

from openedx.core.djangoapps.content.block_structure.api import clear_course_from_cache
from openedx.core.djangoapps.content.block_structure.transformers import BlockStructureTransformers
from student.tests.factories import CourseEnrollmentFactory

from ...api import get_course_blocks
from ..library_content import ContentLibraryTransformer, AdaptiveContentLibraryTransformer
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
    CATEGORY = 'library_content'

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

    @classmethod
    def get_content_library_ref(cls):
        """
        Return string to use as #ref for content library block in course hierarchy.
        """
        return '{category}1'.format(category=cls.CATEGORY)

    def get_course_hierarchy(self):
        """
        Get a course hierarchy to test with.
        """
        return [{
            'org': self.TRANSFORMER_CLASS_TO_TEST.__name__,
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
                                            'metadata': {'category': self.CATEGORY},
                                            '#type': self.CATEGORY,
                                            '#ref': self.get_content_library_ref(),
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

    def _assert_default_selection(self, *verticals_selected):
        """
        Assert that at least one of the blocks in `verticals` is selected.
        """
        self.assertTrue(any(vertical_selected for vertical_selected in verticals_selected))

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
            self.blocks, 'course', 'chapter1', 'lesson1', 'vertical1', self.get_content_library_ref()
        )
        for key in block_key_set:
            self.assertIn(key, trans_keys)

        vertical2_selected = self.get_block_key_set(self.blocks, 'vertical2').pop() in trans_keys
        vertical3_selected = self.get_block_key_set(self.blocks, 'vertical3').pop() in trans_keys
        self._assert_default_selection(vertical2_selected, vertical3_selected)

        selected_vertical = 'vertical2' if vertical2_selected else 'vertical3'
        selected_child = 'html1' if vertical2_selected else 'html2'

        # Check course structure again.
        clear_course_from_cache(self.course.id)
        for i in range(5):
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
                    self.get_content_library_ref(),
                    selected_vertical,
                    selected_child,
                ),
                "Expected 'selected' equality failed in iteration {}.".format(i)
            )


class AdaptiveContentLibraryTransformerTestCase(ContentLibraryTransformerTestCase):  # pylint: disable=test-inherits-tests
    """
    AdaptiveContentLibraryTransformer Test
    """
    TRANSFORMER_CLASS = AdaptiveContentLibraryTransformer
    CATEGORY = 'adaptive_library_content'

    def _assert_default_selection(self, *verticals_selected):
        """
        Assert that none of the blocks in `verticals_selected` are selected.
        """
        self.assertTrue(not any(vertical_selected for vertical_selected in verticals_selected))
