"""
Tests for course optimizer
"""

import unittest
from unittest.mock import Mock, patch

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.core.course_optimizer_provider import (
    generate_broken_links_descriptor,
    _update_node_tree_and_dictionary,
    _get_node_path,
    _create_dto_from_node_tree_recursive
)

class TestLinkCheck(CourseTestCase):
    """
    Tests for the link check functionality
    """
    def setUp(self):
        global MOCK_TREE
        global MOCK_XBLOCK_DICTIONARY
        MOCK_TREE = {
            'chapter_1': {
                'sequential_1': {
                    'vertical_1': {
                        'block_1': {}
                    }
                }
            }
        }
        MOCK_XBLOCK_DICTIONARY = {
            'chapter_1': {
                'display_name': 'Chapter 1',
                'category': 'chapter'
            },
            'sequential_1': {
                'display_name': 'Sequential 1',
                'category': 'sequential'
            },
            'vertical_1': {
                'display_name': 'Vertical 1',
                'category': 'vertical'
            },
            'block_1': {
                'display_name': 'Block 1',
                'url': '/block/1',
                'broken_links': ['broken_link_1', 'broken_link_2'],
                'locked_links': ['locked_link']
            }
        }


    def test_recursive_empty(self):
        expected = _create_dto_from_node_tree_recursive({}, {})
        self.assertEqual(None, expected)


    def test_recursive_leaf_node(self):
        expected_result = {
            'blocks': [
                {
                    'id': 'block_1',
                    'displayName': 'Block 1',
                    'url': '/block/1',
                    'brokenLinks': ['broken_link_1', 'broken_link_2'],
                    'lockedLinks': ['locked_link']
                }
            ]
        }
        expected = _create_dto_from_node_tree_recursive(
            MOCK_TREE['chapter_1']['sequential_1']['vertical_1'],
            MOCK_XBLOCK_DICTIONARY
        )
        self.assertEqual(expected_result, expected)


    def test_recursive_full_tree(self):
        expected_result = {
            'sections': [
                {
                    'id': 'chapter_1',
                    'displayName': 'Chapter 1',
                    'subsections': [
                        {
                            'id': 'sequential_1',
                            'displayName': 'Sequential 1',
                            'units': [
                                {
                                    'id': 'vertical_1',
                                    'displayName': 'Vertical 1',
                                    'blocks': [
                                        {
                                            'id': 'block_1',
                                            'displayName': 'Block 1',
                                            'url': '/block/1',
                                            'brokenLinks': ['broken_link_1', 'broken_link_2'],
                                            'lockedLinks': ['locked_link']
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        expected = _create_dto_from_node_tree_recursive(MOCK_TREE, MOCK_XBLOCK_DICTIONARY)
        self.assertEqual(expected_result, expected)


    def test_get_node_path(self):
        mock_course = Mock()
        mock_section = Mock(
            location=Mock(block_id='section_id'),
            display_name='Section Name'
        )
        mock_subsection = Mock(
            location=Mock(block_id='subsection_id'),
            display_name='Subsection Name'
        )
        mock_unit = Mock(
            location=Mock(block_id='unit_id'),
            display_name='Unit Name'
        )
        mock_block = Mock(
            course_id='course-v1:test+course+2024',
            location=Mock(block_id='block_id'),
            display_name='Block Name',
            category='html'
        )
        mock_course.get_parent.return_value = None
        mock_section.get_parent.return_value = mock_course
        mock_subsection.get_parent.return_value = mock_section
        mock_unit.get_parent.return_value = mock_subsection
        mock_block.get_parent.return_value = mock_unit

        expected_result = [mock_course, mock_section, mock_subsection, mock_unit, mock_block]

        result = _get_node_path(mock_unit)
        self.assertEqual(expected_result, result)
        

    # @patch('cms.djangoapps.contentstore.core.course_optimizer_provider._create_dto_from_node_tree_recursive')
    @patch('cms.djangoapps.contentstore.core.course_optimizer_provider._update_node_tree_and_dictionary')
    @patch('cms.djangoapps.contentstore.core.course_optimizer_provider.get_xblock')
    @patch('cms.djangoapps.contentstore.core.course_optimizer_provider.usage_key_with_run')
    def test_generate_broken_links_descriptor_returns_correct_result(
        self,
        mock_usage_key_with_run,
        mock_get_xblock,
        mock_update_node_tree_and_dictionary,
        # mock_create_dto_from_node_tree_recursive
    ):
        """
        Test generate_broken_links_descriptor to return expected dto
        """
        # Mock data
        mock_course = Mock()
        mock_section = Mock(
            location=Mock(block_id='section_id'),
            display_name='Section Name'
        )
        mock_section.get_parent.side_effect = mock_course
        mock_subsection = Mock(
            location=Mock(block_id='subsection_id'),
            display_name='Subsection Name'
        )
        mock_subsection.get_parent.side_effect = mock_section
        mock_unit = Mock(
            location=Mock(block_id='unit_id'),
            display_name='Unit Name'
        )
        mock_unit.get_parent.side_effect = mock_subsection
        mock_block = Mock(
            course_id='course-v1:test+course+2024',
            location=Mock(block_id='block_id'),
            display_name='Block Name'
        )
        mock_block.get_parent.side_effect = mock_unit
        mock_block.category = 'html'
        # mock_block.get_parent.side_effect = [
        #     Mock(location=Mock(block_id="unit_id"), display_name="Unit Name"),
        #     Mock(location=Mock(block_id="subsection_id"), display_name="Subsection Name"),
        #     Mock(location=Mock(block_id="section_id"), display_name="Section Name"),
        #     None,
        # ]

        # Mock functions
        mock_usage_key_with_run.return_value = "mock_usage_key"
        mock_get_xblock.return_value = mock_block
        mock_update_node_tree_and_dictionary.return_value = Mock()
        # mock_create_dto_from_node_tree_recursive.return_value = 'test'

        # Mock input
        mock_json_content = [
            ["block_id", "http://example.com/broken-link1", False],
            ["block_id", "http://example.com/locked-link1", True],
            ["block_id", "http://example.com/broken-link2", False],
        ]
        request_user = Mock()

        # Expected output
        expected_result = {
            'sections': [
                {
                    'id': 'section_id',
                    'displayName': 'Section Name',
                    'subsections': [
                        {
                            'id': 'subsection_id',
                            'displayName': 'Subsection Name',
                            'units': [
                                {
                                    'id': 'unit_id',
                                    'displayName': 'Unit Name',
                                    'blocks': [
                                        {
                                            'id': 'block_id',
                                            'displayName': 'Block Name',
                                            'url': '/course/course-v1:test+course+2024/editor/html/mock_usage_key',
                                            'brokenLinks': [
                                                "http://example.com/broken-link1",
                                                "http://example.com/broken-link2",
                                            ],
                                            'lockedLinks': ["http://example.com/broken-link1"],
                                        },
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        # Call the function
        result = generate_broken_links_descriptor(mock_json_content, request_user)

        self.assertEqual(result, expected_result)
