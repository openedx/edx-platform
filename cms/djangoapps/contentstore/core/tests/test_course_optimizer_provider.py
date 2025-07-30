"""
Tests for course optimizer
"""
from unittest import mock
from unittest.mock import Mock

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.core.course_optimizer_provider import (
    _update_node_tree_and_dictionary,
    _create_dto_recursive,
    sort_course_sections
)
from cms.djangoapps.contentstore.tasks import LinkState


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
            self.mock_block, 'example_link', LinkState.LOCKED, {}, {}
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
            self.mock_block, 'example_link', LinkState.LOCKED, {}, {}
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
                    'lockedLinks': ['locked_link'],
                    'externalForbiddenLinks': ['forbidden_link_1'],
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
                'locked_links': ['locked_link'],
                'external_forbidden_links': ['forbidden_link_1'],
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
                                            'lockedLinks': ['locked_link'],
                                            'externalForbiddenLinks': ['forbidden_link_1'],
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
                'locked_links': ['locked_link'],
                'external_forbidden_links': ['forbidden_link_1'],
            }
        }
        expected = _create_dto_recursive(mock_node_tree, mock_dictionary)

        self.assertEqual(expected_result, expected)

    @mock.patch('cms.djangoapps.contentstore.core.course_optimizer_provider.modulestore', autospec=True)
    def test_returns_unchanged_data_if_no_course_blocks(self, mock_modulestore):
        """Test that the function returns unchanged data if no course blocks exist."""
        mock_modulestore_instance = Mock()
        mock_modulestore.return_value = mock_modulestore_instance
        mock_modulestore_instance.get_items.return_value = []

        data = {}
        result = sort_course_sections("course-v1:Test+Course", data)
        assert result == data  # Should return the original data

    @mock.patch('cms.djangoapps.contentstore.core.course_optimizer_provider.modulestore', autospec=True)
    def test_returns_unchanged_data_if_linkcheckoutput_missing(self, mock_modulestore):
        """Test that the function returns unchanged data if 'LinkCheckOutput' is missing."""

        mock_modulestore_instance = Mock()
        mock_modulestore.return_value = mock_modulestore_instance

        data = {'LinkCheckStatus': 'Uninitiated'}  # No 'LinkCheckOutput'
        mock_modulestore_instance.get_items.return_value = data

        result = sort_course_sections("course-v1:Test+Course", data)
        assert result == data

    @mock.patch('cms.djangoapps.contentstore.core.course_optimizer_provider.modulestore', autospec=True)
    def test_returns_unchanged_data_if_sections_missing(self, mock_modulestore):
        """Test that the function returns unchanged data if 'sections' is missing."""

        mock_modulestore_instance = Mock()
        mock_modulestore.return_value = mock_modulestore_instance

        data = {'LinkCheckStatus': 'Success', 'LinkCheckOutput': {}}  # No 'LinkCheckOutput'
        mock_modulestore_instance.get_items.return_value = data

        result = sort_course_sections("course-v1:Test+Course", data)
        assert result == data

    @mock.patch('cms.djangoapps.contentstore.core.course_optimizer_provider.modulestore', autospec=True)
    def test_sorts_sections_correctly(self, mock_modulestore):
        """Test that the function correctly sorts sections based on published course structure."""

        mock_course_block = Mock()
        mock_course_block.get_children.return_value = [
            Mock(location=Mock(block_id="section2")),
            Mock(location=Mock(block_id="section3")),
            Mock(location=Mock(block_id="section1")),
        ]

        mock_modulestore_instance = Mock()
        mock_modulestore.return_value = mock_modulestore_instance
        mock_modulestore_instance.get_items.return_value = [mock_course_block]

        data = {
            "LinkCheckOutput": {
                "sections": [
                    {"id": "section1", "name": "Intro"},
                    {"id": "section2", "name": "Advanced"},
                    {"id": "section3", "name": "Bonus"},  # Not in course structure
                ]
            }
        }

        result = sort_course_sections("course-v1:Test+Course", data)
        expected_sections = [
            {"id": "section2", "name": "Advanced"},
            {"id": "section3", "name": "Bonus"},
            {"id": "section1", "name": "Intro"},
        ]

        assert result["LinkCheckOutput"]["sections"] == expected_sections
