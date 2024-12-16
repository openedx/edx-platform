"""
Tests for course optimizer
"""

import unittest
from unittest.mock import Mock, patch

from cms.djangoapps.contentstore.core.course_optimizer_provider import generate_broken_links_descriptor
# from ..course_optimizer_provider import generate_broken_links_descriptor

class TestLinkCheck(ModuleStoreTestCase):
    """
    Tests for the link check functionality
    """
    @patch('cms.djangoapps.contentstore.xblock_storage_handlers.view_handlers.get_xblock')
    @patch('cms.djangoapps.contentstore.xblock_storage_handlers.xblock_helpers.usage_key_with_run')
    def test_success(self):
        # Mock data
        mock_block = Mock()
        mock_block.location.block_id = "block_id"
        mock_block.display_name = "Block Name"
        mock_block.course_id = "course-v1:test+course+2024"
        mock_block.category = "html"
        mock_block.get_parent.side_effect = [
            Mock(location=Mock(block_id="unit_id"), display_name="Unit Name"),
            Mock(location=Mock(block_id="subsection_id"), display_name="Subsection Name"),
            Mock(location=Mock(block_id="section_id"), display_name="Section Name"),
            None,
        ]

        # Mocking
        mock_usage_key_with_run.return_value = "mock_usage_key"
        mock_get_xblock.return_value = mock_block

        # Test input
        mock_json_content = [
            ["block_id", "http://example.com/broken-link1", False],
            ["block_id", "http://example.com/locked-link1", True],
            ["block_id", "http://example.com/broken-link2", False],
        ]
        request_user = Mock()

        # Call the function
        result = generate_broken_links_descriptor(mock_json_content, request_user)

        # Expected structure
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

        self.assertEqual(result, expected_result)


    # def test_exception(self):

# if __name__ == '__main__':
#     unittest.main()
