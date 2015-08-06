"""
...
"""

# TODO 8874: Test graph_traversals more comprehensively.

from collections import defaultdict
from unittest import TestCase

from ..graph_traversals import (
    traverse_depth_first, traverse_topologically
)


class GraphTraversalsTestCase(TestCase):
    """
    ...
    """

    def setUp(self):
        """
        ...
        """
        super(GraphTraversalsTestCase, self).setUp()
        self.graph_1 = {
            'a1': ['b1'],
            'a2': ['b2'],
            'b1': ['c1', 'c2'],
            'b2': [],
            'c1': ['d1', 'd2'],
            'c2': [],
            'd1': ['e1'],
            'd2': ['e1', 'e2'],
            'e1': [],
            'e2': [],
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

    def test_depth_first(self):
        """
        ...
        """
        self.assertEqual(
            list(traverse_depth_first(
                start_node='b1',
                get_children=(lambda node: self.graph_1[node]),
                get_result=(lambda node: node + '_'),
                predicate=(lambda node: node != 'e2'),
            )),
            ['b1_', 'c1_', 'd1_', 'e1_', 'd2_', 'c2_']
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
            )),
            ['b1', 'c1', 'd1', 'd2', 'e1', 'e2', 'c2']
        )
