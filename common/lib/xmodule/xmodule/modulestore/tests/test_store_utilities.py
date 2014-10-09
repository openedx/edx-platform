"""
Tests for store_utilities.py
"""
import unittest
from mock import Mock
import ddt

from xmodule.modulestore.store_utilities import (
    get_draft_subtree_roots, draft_node_constructor
)


@ddt.ddt
class TestUtils(unittest.TestCase):
    """
    Tests for store_utilities

    ASCII trees for ONLY_ROOTS and SOME_TREES:

    ONLY_ROOTS:
    1)
        vertical (not draft)
          |
        url1

    2)
        sequential (not draft)
          |
        url2

    SOME_TREES:

    1)
            sequential_1 (not draft)
                 |
            vertical_1
              /     \
             /       \
        child_1    child_2


    2)
        great_grandparent_vertical (not draft)
                    |
            grandparent_vertical
                    |
                vertical_2
                 /      \
                /        \
            child_3    child_4
    """

    ONLY_ROOTS = [
        draft_node_constructor(Mock(), 'url1', 'vertical'),
        draft_node_constructor(Mock(), 'url2', 'sequential'),
    ]
    ONLY_ROOTS_URLS = ['url1', 'url2']

    SOME_TREES = [
        draft_node_constructor(Mock(), 'child_1', 'vertical_1'),
        draft_node_constructor(Mock(), 'child_2', 'vertical_1'),
        draft_node_constructor(Mock(), 'vertical_1', 'sequential_1'),

        draft_node_constructor(Mock(), 'child_3', 'vertical_2'),
        draft_node_constructor(Mock(), 'child_4', 'vertical_2'),
        draft_node_constructor(Mock(), 'vertical_2', 'grandparent_vertical'),
        draft_node_constructor(Mock(), 'grandparent_vertical', 'great_grandparent_vertical'),
    ]

    SOME_TREES_ROOTS_URLS = ['vertical_1', 'grandparent_vertical']

    @ddt.data(
        (ONLY_ROOTS, ONLY_ROOTS_URLS),
        (SOME_TREES, SOME_TREES_ROOTS_URLS),
    )
    @ddt.unpack
    def test_get_draft_subtree_roots(self, module_nodes, expected_roots_urls):
        """tests for get_draft_subtree_roots"""
        subtree_roots_urls = [root.url for root in get_draft_subtree_roots(module_nodes)]
        # check that we return the expected urls
        self.assertEqual(set(subtree_roots_urls), set(expected_roots_urls))
