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
        """Setup for tests"""
        global MOCK_TREE
        global MOCK_XBLOCK_DICTIONARY
        global MOCK_COURSE
        global MOCK_SECTION
        global MOCK_SUBSECTION
        global MOCK_UNIT
        global MOCK_BLOCK

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
                'display_name': 'Section Name',
                'category': 'chapter'
            },
            'sequential_1': {
                'display_name': 'Subsection Name',
                'category': 'sequential'
            },
            'vertical_1': {
                'display_name': 'Unit Name',
                'category': 'vertical'
            },
            'block_1': {
                'display_name': 'Block Name',
                'url': '/block/1',
                'broken_links': ['broken_link_1', 'broken_link_2'],
                'locked_links': ['locked_link']
            }
        }

        MOCK_COURSE = Mock()
        MOCK_SECTION = Mock(
            location=Mock(block_id='chapter_1'),
            display_name='Section Name',
            category='chapter'
        )
        MOCK_SUBSECTION = Mock(
            location=Mock(block_id='sequential_1'),
            display_name='Subsection Name',
            category='sequential'
        )
        MOCK_UNIT = Mock(
            location=Mock(block_id='vertical_1'),
            display_name='Unit Name',
            category='vertical'
        )
        MOCK_BLOCK = Mock(
            location=Mock(block_id='block_1'),
            display_name='Block Name',
            course_id='course-v1:test+course',
            category='html'
        )
        # MOCK_BLOCK.location.__str__.return_value = 'block_location_str'
        MOCK_COURSE.get_parent.return_value = None
        MOCK_SECTION.get_parent.return_value = MOCK_COURSE
        MOCK_SUBSECTION.get_parent.return_value = MOCK_SECTION
        MOCK_UNIT.get_parent.return_value = MOCK_SUBSECTION
        MOCK_BLOCK.get_parent.return_value = MOCK_UNIT


    def test_update_node_tree_and_dictionary(self):
        """Test _update_node_tree_and_dictionary"""
        expected_tree = MOCK_TREE
        expected_dictionary = {
            'chapter_1': {
                'display_name': 'Section Name',
                'category': 'chapter'
            },
            'sequential_1': {
                'display_name': 'Subsection Name',
                'category': 'sequential'
            },
            'vertical_1': {
                'display_name': 'Unit Name',
                'category': 'vertical'
            },
            'block_1': {
                'display_name': 'Block Name',
                'category': 'html',
                'url': f'/course/{MOCK_BLOCK.course_id}/editor/html/{MOCK_BLOCK.location}',
                'locked_links': ['example_link']
            }
        }

        result_tree, result_dictionary = _update_node_tree_and_dictionary(
            MOCK_BLOCK, 'example_link', True, {}, {}
        )

        self.assertEqual(expected_tree, result_tree)
        self.assertEqual(expected_dictionary, result_dictionary)


    def test_get_node_path(self):
        """Tests _get_node_path"""
        expected_result = [MOCK_SECTION, MOCK_SUBSECTION, MOCK_UNIT, MOCK_BLOCK]
        result = _get_node_path(MOCK_BLOCK)
        self.assertEqual(expected_result, result)


    def test_create_dto_recursive_empty(self):
        """Tests _create_dto_from_node_tree_recursive"""
        expected = _create_dto_from_node_tree_recursive({}, {})
        self.assertEqual(None, expected)


    def test_create_dto_recursive_leaf_node(self):
        """Tests _create_dto_from_node_tree_recursive"""
        expected_result = {
            'blocks': [
                {
                    'id': 'block_1',
                    'displayName': 'Block Name',
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


    def test_create_dto_recursive_full_tree(self):
        """Tests _create_dto_from_node_tree_recursive"""
        expected_result = {
            'sections': [
                {
                    'id': 'chapter_1',
                    'displayName': 'Section Name',
                    'subsections': [
                        {
                            'id': 'sequential_1',
                            'displayName': 'Subsection Name',
                            'units': [
                                {
                                    'id': 'vertical_1',
                                    'displayName': 'Unit Name',
                                    'blocks': [
                                        {
                                            'id': 'block_1',
                                            'displayName': 'Block Name',
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
        