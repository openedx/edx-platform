"""
Tests for graph traversal generator functions.
"""


from collections import defaultdict
from unittest import TestCase

from ..graph_traversals import traverse_post_order, traverse_pre_order, traverse_topologically


class TestGraphTraversals(TestCase):
    """
    Test Class for graph traversal generator functions.
    """

    def setUp(self):
        # Creates a test graph with the following disconnected
        # structures.
        #
        #       a1         a2
        #       |          |
        #       b1         b2
        #      /  \
        #     c1  c2
        #    /  \   \
        #  d1  d2   d3
        #  \  / \
        #   e1  e2
        #       |
        #       f1
        super().setUp()
        self.parent_to_children_map = {
            'a1': ['b1'],
            'a2': ['b2'],
            'b1': ['c1', 'c2'],
            'b2': [],
            'c1': ['d1', 'd2'],
            'c2': ['d3'],
            'd1': ['e1'],
            'd2': ['e1', 'e2'],
            'd3': [],
            'e1': [],
            'e2': ['f1'],
            'f1': [],
        }
        self.child_to_parents_map = self.get_child_to_parents_map(self.parent_to_children_map)

    @staticmethod
    def get_child_to_parents_map(parent_to_children_map):
        """
        Constructs and returns a child-to-parents map for the given
        parent-to-children map.

        Arguments:
            parent_to_children_map ({parent:[children]}) - A
                dictionary of parent to a list of its children.  If a
                node does not have any children, its value should be [].

        Returns:
            {child:[parents]} - A dictionary of child to a list of its
                parents. If a node does not have any parents, its value
                will be [].
        """
        result = defaultdict(list)
        for parent, children in parent_to_children_map.items():
            for child in children:
                result[child].append(parent)
        return result

    def test_pre_order(self):
        assert list(
            traverse_pre_order(start_node='b1',
                               get_children=(lambda node: self.parent_to_children_map[node]),
                               filter_func=(lambda node: (node != 'd3')))
        ) == ['b1', 'c1', 'd1', 'e1', 'd2', 'e2', 'f1', 'c2']

    def test_post_order(self):
        assert list(
            traverse_post_order(
                start_node='b1',
                get_children=(lambda node: self.parent_to_children_map[node]),
                filter_func=(lambda node: (node != 'd3')))
        ) == ['e1', 'd1', 'f1', 'e2', 'd2', 'c1', 'c2', 'b1']

    def test_topological(self):
        assert list(
            traverse_topologically(
                start_node='b1',
                get_children=(lambda node: self.parent_to_children_map[node]),
                get_parents=(lambda node: self.child_to_parents_map[node]),
                filter_func=(lambda node: (node != 'd3')))
        ) == ['b1', 'c1', 'd1', 'd2', 'e1', 'e2', 'f1', 'c2']

    def test_topological_yield_descendants(self):
        assert list(
            traverse_topologically(
                start_node='b1',
                get_children=(lambda node: self.parent_to_children_map[node]),
                get_parents=(lambda node: self.child_to_parents_map[node]),
                filter_func=(lambda node: (node != 'd2')),
                yield_descendants_of_unyielded=True)
        ) == ['b1', 'c1', 'd1', 'e1', 'e2', 'f1', 'c2', 'd3']

    def test_topological_not_yield_descendants(self):
        assert list(
            traverse_topologically(
                start_node='b1',
                get_children=(lambda node: self.parent_to_children_map[node]),
                get_parents=(lambda node: self.child_to_parents_map[node]),
                filter_func=(lambda node: (node != 'd2')),
                yield_descendants_of_unyielded=False)
        ) == ['b1', 'c1', 'd1', 'e1', 'c2', 'd3']

    def test_topological_yield_single_node(self):
        assert list(
            traverse_topologically(
                start_node='b1',
                get_children=(lambda node: self.parent_to_children_map[node]),
                get_parents=(lambda node: self.child_to_parents_map[node]),
                filter_func=(lambda node: (node == 'c2')),
                yield_descendants_of_unyielded=True)
        ) == ['c2']

    def test_topological_complex(self):
        """
        Test a more complex DAG
        """
        #                 root
        #              /    |           \
        #             /     |            \
        #           A       B              C
        #          / \   /  |   \         |   \
        #         /   \ /   |    \        |    \
        #        D     E    F    G        H    I
        #                  / \    \      |
        #                 /   \    \     |
        #                J    K     \    L
        #                   /  |    \   / \
        #                  /   |    \  /   \
        #                 M    N     O     P
        parent_to_children = {
            # Note: root has additional links than what is drawn above.
            'root': ['A', 'B', 'C', 'E', 'F', 'K', 'O'],
            'A': ['D', 'E'],
            'B': ['E', 'F', 'G'],
            'C': ['H', 'I'],
            'D': [],
            'E': [],
            'F': ['J', 'K'],
            'G': ['O'],
            'H': ['L'],
            'I': [],
            'J': [],
            'K': ['M', 'N'],
            'L': ['O', 'P'],
            'M': [],
            'N': [],
            'O': [],
            'P': [],
        }
        child_to_parents = self.get_child_to_parents_map(parent_to_children)
        for _ in range(2):  # should get the same result twice
            assert list(
                traverse_topologically(
                    start_node='root',
                    get_children=(lambda node: parent_to_children[node]),
                    get_parents=(lambda node: child_to_parents[node]))
            ) == ['root', 'A', 'D', 'B', 'E', 'F', 'J', 'K', 'M', 'N', 'G', 'C', 'H', 'L', 'O', 'P', 'I']
