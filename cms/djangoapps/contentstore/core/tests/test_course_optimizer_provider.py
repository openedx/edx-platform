"""
Tests for course optimizer
"""
from unittest.mock import Mock

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.core.course_optimizer_provider import (
    _update_node_tree_and_dictionary,
    _create_dto_recursive
)


class TestLinkCheckProvider(CourseTestCase):
    """
    Tests for functions that generate a json structure of locked and broken links
    to send to the frontend.
    """
    def setUp(self):
        """Setup course blocks for tests"""
        super().setUp()
        self.mock_course = Mock()
        self.mock_section = Mock(
            location=Mock(block_id='chapter_1'),
            display_name='Section Name',
            category='chapter'
        )
        self.mock_subsection = Mock(
            location=Mock(block_id='sequential_1'),
            display_name='Subsection Name',
            category='sequential'
        )
        self.mock_unit = Mock(
            location=Mock(block_id='vertical_1'),
            display_name='Unit Name',
            category='vertical'
        )
        self.mock_block = Mock(
            location=Mock(block_id='block_1'),
            display_name='Block Name',
            course_id=self.course.id,
            category='html'
        )
        self.mock_course.get_parent.return_value = None
        self.mock_section.get_parent.return_value = self.mock_course
        self.mock_subsection.get_parent.return_value = self.mock_section
        self.mock_unit.get_parent.return_value = self.mock_subsection
        self.mock_block.get_parent.return_value = self.mock_unit

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
            self.mock_block, 'example_link', True, {}, {}
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
                'url': f'/course/{self.course.id}/editor/html/{self.mock_block.location}',
                'locked_links': ['example_link']
            }
        }
        result_tree, result_dictionary = _update_node_tree_and_dictionary(
            self.mock_block, 'example_link', True, {}, {}
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
