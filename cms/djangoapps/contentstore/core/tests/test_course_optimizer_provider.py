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
    _create_dto_recursive
)

class TestLinkCheckProvider(CourseTestCase):
    """
    Tests for functions that generate a json structure of locked and broken links
    to send to the frontend.
    """
    def setUp(self):
        """Setup course blocks for tests"""
        global MOCK_COURSE
        global MOCK_SECTION
        global MOCK_SUBSECTION
        global MOCK_UNIT
        global MOCK_BLOCK

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
        MOCK_COURSE.get_parent.return_value = None
        MOCK_SECTION.get_parent.return_value = MOCK_COURSE
        MOCK_SUBSECTION.get_parent.return_value = MOCK_SECTION
        MOCK_UNIT.get_parent.return_value = MOCK_SUBSECTION
        MOCK_BLOCK.get_parent.return_value = MOCK_UNIT


    def test_update_node_tree_and_dictionary_returns_node_tree(self):
        """
        Verify _update_node_tree_and_dictionary creates a node tree structure
        when passed a block level xblock.
        """
        expected_tree = {
            'chapter_1': {
                'sequential_1': {
                    'vertical_1': {
                        'block_1': {}
                    }
                }
            }
        }
        result_tree, result_dictionary = _update_node_tree_and_dictionary(
            MOCK_BLOCK, 'example_link', True, {}, {}
        )

        self.assertEqual(expected_tree, result_tree)


    def test_update_node_tree_and_dictionary_returns_dictionary(self):
        """
        Verify _update_node_tree_and_dictionary creates a dictionary of parent xblock entries
        when passed a block level xblock.
        """
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

        self.assertEqual(expected_dictionary, result_dictionary)


    def test_create_dto_recursive_returns_for_empty_node(self):
        """
        Test _create_dto_recursive behavior at the end of recursion.
        Function should return None when given empty node tree and empty dictionary.
        """
        expected = _create_dto_recursive({}, {})
        self.assertEqual(None, expected)


    def test_create_dto_recursive_returns_for_leaf_node(self):
        """
        Test _create_dto_recursive behavior at the step before the end of recursion.
        When evaluating a leaf node in the node tree, the function should return broken links
        and locked links data from the leaf node.
        """
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

        mock_node_tree = {
            'block_1': {}
        }
        mock_dictionary = {
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
        expected = _create_dto_recursive(mock_node_tree, mock_dictionary)
        self.assertEqual(expected_result, expected)


    def test_create_dto_recursive_returns_for_full_tree(self):
        """
        Test _create_dto_recursive behavior when recursing many times.
        When evaluating a fully mocked node tree and dictionary, the function should return
        a full json DTO prepared for frontend.
        """
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

        mock_node_tree = {
            'chapter_1': {
                'sequential_1': {
                    'vertical_1': {
                        'block_1': {}
                    }
                }
            }
        }
        mock_dictionary = {
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
        expected = _create_dto_recursive(mock_node_tree, mock_dictionary)

        self.assertEqual(expected_result, expected)
        