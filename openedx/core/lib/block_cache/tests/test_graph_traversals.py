"""
...
"""

# TODO 8874: Test graph_traversals more comprehensively.

from collections import defaultdict
from unittest import TestCase

from ..graph_traversals import (
    traverse_pre_order, traverse_post_order, traverse_topologically
)


class GraphTraversalsTestCase(TestCase):
    """
    ...
    """

    def setUp(self):
        """
        ...
        """
        #       b1
        #      /  \
        #     c1  c2
        #    /  \   \
        #  d1  d2   d3
        #  \  / \
        #   e1  e2
        #       |
        #       f1
        super(GraphTraversalsTestCase, self).setUp()
        self.graph_1 = {
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
        self.graph_1_parents = self.get_parent_map(self.graph_1)

    @staticmethod
    def get_parent_map(graph):
        """
        ...
        """
        result = defaultdict(list)
        for parent, children in graph.iteritems():
            for child in children:
                result[child].append(parent)
        return result

    def test_pre_order(self):
        """
        ...
        """
        self.assertEqual(
            list(traverse_pre_order(
                start_node='b1',
                get_children=(lambda node: self.graph_1[node]),
                get_result=(lambda node: node + '_'),
                predicate=(lambda node: node != 'd3'),
            )),
            ['b1_', 'c1_', 'd1_', 'e1_', 'd2_', 'e2_', 'f1_', 'c2_']
        )

    def test_post_order(self):
        """
        ...
        """
        self.assertEqual(
            list(traverse_post_order(
                start_node='b1',
                get_children=(lambda node: self.graph_1[node]),
                get_result=(lambda node: node + '_'),
                predicate=(lambda node: node != 'd3'),
            )),
            ['e1_', 'd1_', 'f1_', 'e2_', 'd2_', 'c1_', 'c2_', 'b1_']
        )

    def test_topological(self):
        """
        ...
        """
        self.assertEqual(
            list(traverse_topologically(
                start_node='b1',
                get_children=(lambda node: self.graph_1[node]),
                get_parents=(lambda node: self.graph_1_parents[node]),
                predicate=(lambda node: node != 'd3'),
            )),
            ['b1', 'c1', 'd1', 'd2', 'e1', 'e2', 'f1', 'c2']
        )

    def test_topological_with_predicate(self):
        """
        ...
        """
        self.assertEqual(
            list(traverse_topologically(
                start_node='b1',
                get_children=(lambda node: self.graph_1[node]),
                get_parents=(lambda node: self.graph_1_parents[node]),
                predicate=(lambda node: node != 'd2')
            )),
            ['b1', 'c1', 'd1', 'e1', 'c2', 'd3']
        )
