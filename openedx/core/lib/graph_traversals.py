"""
This module contains generic generator functions for traversing tree
(and DAG) structures.  It is agnostic to the underlying data structure
and implementation of the tree object.  It does this through dependency
injection of the tree's accessor functions: get_parents and
get_children.

Additionally, it supports the visitor design pattern by accepting a
get_result function that is called on each visited node.

The following depth-first traversal methods are implemented:

* Pre-order: Parent yielded before children; child with multiple
parents is yielded when first encountered.

* Topological: Parent yielded before children; child with multiple
parents yielded only after all its parents are visited.

* Post-order: Children yielded before its parents.

Note: In-order traversal is not implemented as of yet.  We can do so
if/when needed.

Optimization once DAGs are not supported:
Supporting Directed Acyclic Graphs (DAGs) requires us to use
topological sort, which has the following negative performance
implications:

* For a simple tree, we can immediately skip over traversing
descendants, once it is determined that a parent is not to be yielded
(based on the return value from the 'filter_func' function). However,
since we support DAGs, we cannot simply skip over descendants since
they may still be accessible through a different ancestry chain and
need to be revisited once all their parents are visited.

* For topological sort, we need the get_parents accessor function in
order to determine whether all of a node's parents have been visited.
This means the underlying implementation of the graph needs to have
an efficient way to get a node's parents, perhaps with back pointers
to each node's parents.  This requires additional storage space, which
could be eliminated if DAGs are not supported.


"""
from collections import deque


def traverse_topologically(
    start_node, get_parents, get_children, get_result=None, filter_func=None, yield_descendants_of_unyielded=False,
):
    """
    Generator for yielding nodes of a tree (or directed acyclic graph)
    in a topological sort.  The tree is traversed using the
    get_parents and get_children accessors.  The get_result function is
    used to compute the yielded result value.  The filter_func function is
    used to limit which nodes are actually yielded.

    Arguments:
        start_node (any hashable type) - The starting node for the
        traversal.

        get_parents (F(node)->[node]) - Function that returns a list of
            parent nodes for a given node.

        get_children (F(node)->[node]) - Function that returns a list of
            children nodes for a given node.

        get_result (F(node)->any type) - Function that computes and
            returns the resulting value to be yielded for the given
            node.  If None, the identity function is assumed.

        filter_func (F(node)->boolean) - Function that returns
            whether or not to yield the given node.
            If None, the True function is assumed.

        yield_descendants_of_unyielded (boolean) -
            If False, descendants of an unyielded node are not
                yielded.
            If True, descendants of an unyielded node are yielded even
                if none of their parents were yielded.

            Note: In case of a DAG, a descendant is yielded if *any* of
            its parents are yielded.

    Yields:
        get_result(node): The result of the next node in the traversal.
    """
    return _traverse_generic(
        start_node,
        get_parents=get_parents,
        get_children=get_children,
        get_result=get_result,
        filter_func=filter_func,
        yield_descendants_of_unyielded=yield_descendants_of_unyielded,
    )


def traverse_pre_order(
    start_node, get_children, get_result=None, filter_func=None,
):
    """
    Generator for yielding nodes of a tree (or directed acyclic graph)
    in a pre-order sort.

    Arguments:
        See description in traverse_topologically.
"""
    return _traverse_generic(
        start_node,
        # There's no need to get_parents
        get_parents=None,
        get_children=get_children,
        get_result=get_result,
        filter_func=filter_func,
    )


def traverse_post_order(
    start_node, get_children, get_result=None, filter_func=None
):
    """
    Generator for yielding nodes of a tree (or directed acyclic graph)
    in a post-order sort.

    Arguments:
        See description in traverse_topologically.
    """
    class _Node(object):
        """
        Wrapper class for nodes that keeps a children iterator.
        """
        def __init__(self, node, get_children):
            self.node = node
            self.children = iter(get_children(node))

    # If get_result or filter_func aren't provided, make them no-ops.
    get_result = get_result or (lambda node_: node_)
    filter_func = filter_func or (lambda __: True)

    # Use deque for the stack, which is O(1) for pop and append.
    # Use the _Node class to keep track of iterated children.
    stack = deque([_Node(start_node, get_children)])

    # Keep track of which nodes have been visited.
    visited = set()

    while stack:
        # Peek at the current node at the top of the stack.
        current = stack[len(stack) - 1]

        # Verify the node wasn't already visited and the node
        # satisfies the filter_func.
        if current.node in visited or not filter_func(current.node):
            # Since already visited or filtered out, remove from the
            # stack and continue with the next node.
            stack.pop()
            continue

        # See if there are any additional children for this node.
        try:
            next_child = current.children.next()

        except StopIteration:
            # Since there are no children left, visit the node and
            # remove it from the stack.
            yield get_result(current.node)
            visited.add(current.node)
            stack.pop()

        else:
            # If so, add the child to the top of the stack.
            stack.append(_Node(next_child, get_children))


def _traverse_generic(
    start_node, get_parents, get_children, get_result=None, filter_func=None, yield_descendants_of_unyielded=False,
):
    """
    Helper function to avoid duplicating functionality between
    traverse_depth_first and traverse_topologically.

    If get_parents is None, do a pre-order traversal.
    Else, do a topological traversal.

    The topological traversal has a worse time complexity than
    pre-order does, as it needs to check whether each node's
    parents have been visited.

    Arguments:
        See description in traverse_topologically.
    """

    # If get_result or filter_func aren't provided, make them no-ops.
    get_result = get_result or (lambda node_: node_)
    filter_func = filter_func or (lambda __: True)

    # Use deque for the stack, which is O(1) for pop and append.
    stack = deque([start_node])

    # Keep track of which nodes have been visited and whether they
    # were in fact yielded.
    yield_results = {}  # dict(node:boolean)

    # While there are more nodes on the stack...
    while stack:

        # Take a node off the top of the stack.
        current_node = stack.pop()

        # If we're doing a topological traversal, then make sure all
        # the node's parents have been visited. If they haven't,
        # then skip the node for now; we'll encounter it again later
        # through another one of its parents.
        if get_parents and current_node != start_node:
            parents = get_parents(current_node)

            # If all of the parents have not yet been visited, continue.
            if not all(parent in yield_results for parent in parents):
                continue

            # If none of the parents have yielded, continue, unless
            # specified otherwise (via yield_descendants_of_unyielded).
            elif not yield_descendants_of_unyielded and not any(yield_results[parent] for parent in parents):
                continue

        # If the current node has already been visited, continue.
        if current_node not in yield_results:

            if get_parents:
                # For a topological sort, it's important that we visit the
                # children even if the parent isn't yielded in case a
                # child has multiple parents and this is its last parent.
                unvisited_children = list(get_children(current_node))

            else:
                # For a pre-order sort, filter out already visited
                # children.
                unvisited_children = list(
                    child
                    for child in get_children(current_node)
                    if child not in yield_results
                )

            # Add the node's unvisited children to the stack in reverse
            # order so they are traversed in their original order.
            unvisited_children.reverse()
            stack.extend(unvisited_children)

            # Yield the result of the node if the node satisfies the
            # filter_func.
            should_yield_node = filter_func(current_node)
            if should_yield_node:
                yield get_result(current_node)

            # Keep track of whether or not the node was yielded so we
            # know whether or not to yield its children.
            yield_results[current_node] = should_yield_node
