"""
Tests for store_utilities.py
"""


import unittest
from unittest.mock import Mock

import ddt

from xmodule.modulestore.store_utilities import draft_node_constructor, get_draft_subtree_roots


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
        ('url1', 'vertical'),
        ('url2', 'sequential'),
    ]
    ONLY_ROOTS_URLS = ['url1', 'url2']

    SOME_TREES = [
        ('child_1', 'vertical_1'),
        ('child_2', 'vertical_1'),
        ('vertical_1', 'sequential_1'),

        ('child_3', 'vertical_2'),
        ('child_4', 'vertical_2'),
        ('vertical_2', 'grandparent_vertical'),
        ('grandparent_vertical', 'great_grandparent_vertical'),
    ]
    SOME_TREES_ROOTS_URLS = ['vertical_1', 'grandparent_vertical']

    @ddt.data(
        (ONLY_ROOTS, ONLY_ROOTS_URLS),
        (SOME_TREES, SOME_TREES_ROOTS_URLS),
    )
    @ddt.unpack
    def test_get_draft_subtree_roots(self, node_arguments_list, expected_roots_urls):
        """tests for get_draft_subtree_roots"""
        block_nodes = []
        for node_args in node_arguments_list:
            block_nodes.append(draft_node_constructor(Mock(), node_args[0], node_args[1]))
        subtree_roots_urls = [root.url for root in get_draft_subtree_roots(block_nodes)]
        # check that we return the expected urls
        assert set(subtree_roots_urls) == set(expected_roots_urls)
