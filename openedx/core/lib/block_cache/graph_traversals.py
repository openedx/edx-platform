"""
...
"""
from collections import deque


def _traverse_generic(start_node, get_parents, get_children, get_result=None, predicate=None):
    """
    Helper function to avoid duplicating functionality between
    traverse_depth_first and traverse_topologically.

    If get_parents is None, do a depth first traversal.
    Else, do a topological traversal.

    The topological traversal has a worse time complexity than depth-first does,
    as it needs to check whether each node's parents have been visited.

    Arguments:
        start_node - the starting node for the traversal
        get_parents - function that returns a list of parent nodes for the given node
        get_children - function that returns a list of children nodes for the given node
        get_result - function that computes and returns the resulting value to be yielded for the given node
        predicate - function that returns whether or not to yield the given node
    """
    # If get_result or predicate aren't provided, just make them to no-ops.
    get_result = get_result or (lambda node_: node_)
    predicate = predicate or (lambda __: True)

    # For our stack, we use the deque type, which is O(1) for pop and append.
    stack = deque([start_node])
    visited = set()

    # While there are more nodes on the stack...
    while stack:

        # Take a node off the top of the stack.
        curr_node = stack.pop()

        # If we're doing a topological traversal, then make sure all the node's
        # parents have been visited. If they haven't, then skip the node for
        # now; we'll encounter it again later through another one of its
        # parents.
        if get_parents and curr_node != start_node:
            all_parents_visited = all(parent in visited for parent in get_parents(curr_node))
            if not all_parents_visited:
                continue

        visited.add(curr_node)

        # Add its unvisited children to the stack in reverse order so that
        # they are popped off in their original order.
        unvisited_children = list(
            child
            for child in get_children(curr_node)
            if child not in visited
        )
        unvisited_children.reverse()
        stack.extend(unvisited_children)

        # Return the result if it satisfies the predicate.
        # It's important that we do this *after* calling get_children, because the
        # caller may want to modify the yielded value, so calling get_children
        # after that might mess up the traversal.
        if predicate(curr_node):
            yield get_result(curr_node)


def traverse_depth_first(start_node, get_children, get_result=None, predicate=None):
    return _traverse_generic(
        start_node,
        get_parents=None,
        get_children=get_children,
        get_result=get_result,
        predicate=predicate
    )


def traverse_topologically(start_node, get_parents, get_children, get_result=None, predicate=None):
    return _traverse_generic(
        start_node,
        get_parents=get_parents,
        get_children=get_children,
        get_result=get_result,
        predicate=predicate
    )
