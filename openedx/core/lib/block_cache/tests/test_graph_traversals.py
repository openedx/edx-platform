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
        self.assertEqual(
            list(traverse_topologically(
                start_node='b1',
                get_children=(lambda node: self.graph_1[node]),
                get_parents=(lambda node: self.graph_1_parents[node]),
                predicate=(lambda node: node != 'd3'),
            )),
            ['b1', 'c1', 'd1', 'd2', 'e1', 'e2', 'f1', 'c2']
        )

    def test_topological_yield_descendants(self):
        self.assertEqual(
            list(traverse_topologically(
                start_node='b1',
                get_children=(lambda node: self.graph_1[node]),
                get_parents=(lambda node: self.graph_1_parents[node]),
                predicate=(lambda node: node != 'd2'),
                yield_descendants_of_unyielded=True,
            )),
            ['b1', 'c1', 'd1', 'e1', 'e2', 'f1', 'c2', 'd3']
        )

    def test_topological_not_yield_descendants(self):
        self.assertEqual(
            list(traverse_topologically(
                start_node='b1',
                get_children=(lambda node: self.graph_1[node]),
                get_parents=(lambda node: self.graph_1_parents[node]),
                predicate=(lambda node: node != 'd2'),
                yield_descendants_of_unyielded=False,
            )),
            ['b1', 'c1', 'd1', 'e1', 'c2', 'd3']
        )

    def test_topological_yield_single_node(self):
        self.assertEqual(
            list(traverse_topologically(
                start_node='b1',
                get_children=(lambda node: self.graph_1[node]),
                get_parents=(lambda node: self.graph_1_parents[node]),
                predicate=(lambda node: node == 'c2'),
                yield_descendants_of_unyielded=True,
            )),
            ['c2']
        )

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
        graph = {
            'root': ['A', 'B', 'C', 'E', 'F', 'K', 'O'], # has additional links than what is drawn above
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
        graph_parents = self.get_parent_map(graph)
        for _ in range(2): # should get the same result twice
            self.assertEqual(
                list(traverse_topologically(
                    start_node='root',
                    get_children=(lambda node: graph[node]),
                    get_parents=(lambda node: graph_parents[node]),
                )),
                ['root', 'A', 'D', 'B', 'E', 'F', 'J', 'K', 'M', 'N', 'G', 'C', 'H', 'L', 'O', 'P', 'I'],
            )
