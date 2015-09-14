"""
...
"""
from collections import deque


def _traverse_generic(
    start_node, get_parents, get_children, get_result=None, predicate=None, yield_descendants_of_unyielded=False
):
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
        yield_descendants_of_unyielded -
           if False, all descendants of an unyielded node are not yielded.
           if True, descendants of an unyielded node are yielded even if none of their parents were yielded.
    """
    # If get_result or predicate aren't provided, just make them to no-ops.
    get_result = get_result or (lambda node_: node_)
    predicate = predicate or (lambda __: True)

    # For our stack, we use the deque type, which is O(1) for pop and append.
    stack = deque([start_node])
    yield_results = {}

    # While there are more nodes on the stack...
    while stack:

        # Take a node off the top of the stack.
        curr_node = stack.pop()

        # If we're doing a topological traversal, then make sure all the node's
        # parents have been visited. If they haven't, then skip the node for
        # now; we'll encounter it again later through another one of its
        # parents.
        if get_parents and curr_node != start_node:
            parents = get_parents(curr_node)
            all_parents_visited = all(parent in yield_results for parent in parents)
            any_parent_yielded = any(yield_results[parent] for parent in parents) if all_parents_visited else False
            if not all_parents_visited or (not yield_descendants_of_unyielded and not any_parent_yielded):
                continue

        if curr_node not in yield_results:
            # Add its unvisited children to the stack in reverse order so that
            # they are popped off in their original order.
            # It's important that we visit the children even if the parent isn't yielded
            # in case a child has multiple parents and this is its last parent.
            unvisited_children = list(get_children(curr_node))

            # If we're not doing a topological traversal, check whether the child has been visited.
            if not get_parents:
                unvisited_children = list(
                    child
                    for child in unvisited_children
                    if child not in yield_results
                )
            unvisited_children.reverse()
            stack.extend(unvisited_children)

            # Return the result if it satisfies the predicate.
            # Keep track of the result so we know whether to yield its children.
            should_yield_node = predicate(curr_node)
            yield_results[curr_node] = should_yield_node
            if should_yield_node:
                yield get_result(curr_node)


def traverse_topologically(start_node, get_parents, get_children, **kwargs):
    return _traverse_generic(
        start_node,
        get_parents=get_parents,
        get_children=get_children,
        **kwargs
    )


def traverse_pre_order(start_node, get_children, **kwargs):
    return _traverse_generic(
        start_node,
        get_parents=None,
        get_children=get_children,
        **kwargs
    )


class BlockAndChildIndexStackItem(object):
    """
    Class for items in the stack.
    """
    def __init__(self, block):
        self.block = block
        self.children = None
        self.child_index = 0

    def next_child(self, get_children):
        """
        Returns the next child of the block for this item in the stack.
        """
        if self.children is None:
            self.children = get_children(self.block)

        child = None
        if self.child_index < len(self.children):
            child = self.children[self.child_index]
            self.child_index += 1
        return child


def traverse_post_order(start_node, get_children, get_result=None, predicate=None):
    # If get_result or predicate aren't provided, just make them to no-ops.
    get_result = get_result or (lambda node_: node_)
    predicate = predicate or (lambda __: True)

    # For our stack, we use the deque type, which is O(1) for pop and append.
    stack = deque([BlockAndChildIndexStackItem(start_node)])
    visited = set()

    while stack:
        # peek at the next item in the stack
        current_stack_item = stack[len(stack)-1]

        # verify the block wasn't already visited and the block satisfies the predicate
        if current_stack_item.block in visited or not predicate(current_stack_item.block):
            stack.pop()
            continue

        next_child = current_stack_item.next_child(get_children)
        if next_child:
            stack.append(BlockAndChildIndexStackItem(next_child))
        else:
            yield get_result(current_stack_item.block)
            visited.add(current_stack_item.block)
            stack.pop()
