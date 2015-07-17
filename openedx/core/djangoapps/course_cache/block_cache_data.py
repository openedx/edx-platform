"""
...
"""
from collections import namedtuple

from openedx.core.lib.graph_traversals import traverse_topologically


class UserCourseInfo(object):
    """
    Information for a user in relation to a specific course.
    """

    def __init__(self, has_staff_access):
        """
        Arguments:
            has_staff_access (bool)
        """
        self.has_staff_access = has_staff_access


class CourseBlockStructure(object):
    """
    A wrapper around a doubly-linked directed acyclic graph of XBlock UsageKeys.
    """

    # parents and children are of type set[UsageKey].
    AdjacencyInfo = namedtuple('AdjacencyInfo', 'parents children')

    def __init__(self, root_block_key, root_block_is_course_root, adj):
        """
        Arguments:
            adj (dict[UsageKey: AdjacencyInfo])
        """
        self.root_block_key = root_block_key
        self.root_block_is_course_root = root_block_is_course_root
        self._adj = adj

    def get_block_keys(self):
        """
        Returns:
            list[usage_key]
        """
        return self._adj.keys()

    def get_parents(self, usage_key):
        """
        Arguments:
            usage_key (UsageKey)

        Returns:
            set[UsageKey]
        """
        return self._adj[usage_key].parents

    def get_children(self, usage_key):
        """
        Arguments:
            usage_key (UsageKey)

        Returns:
            set[UsageKey]
        """
        return self._adj[usage_key].children

    def get_sub_structure(self, root_block_key):
        """
        Arguments:
            root_block_key (UsageKey)

        Returns:
            CourseBlockStructure
        """
        if root_block_key == self.root_block_key:
            return self
        nodes = set(traverse_topologically(
            start_node=self.root_block_key,
            get_parents=self.get_parents,
            get_children=self.get_children
        ))
        adj = {
            usage_key: (
                children,
                set(parent for parent in self.get_parents(usage_key) if (parent in nodes))
            )
            for usage_key, (parents, children) in self._adj
            if usage_key in nodes
        }
        return CourseBlockStructure(root_block_key, False, adj)

    def _remove_block(self, usage_key, remove_orphans):
        """
        Arguments:
            usage_key (UsageKey)
            remove_orphans (bool): If True, recursively remove all blocks that
                become orphans as a result of this block removal, along with
                all blocks that subsequently become orphans, and so on. Note
                that this incurs a significant performance hit.

        Raises:
            KeyError if block does not exist in course structure.
        """
        adj = self._adj

        # For all this block's children, remove self from list of their parents.
        for child in adj[usage_key].children:
            adj[child].parents.remove(usage_key)

            # If this is the child's only parent, then the child is now an
            # orphan. If requested, recursively remove it as well.
            if remove_orphans and not adj[child].parents:
                self._remove_block(child, remove_orphans)

        # For all this block's parents, remove self from list of their children.
        for parent_key in adj[usage_key].parents:
            adj[parent_key].children.remove(usage_key)

        # Remove adjacency list entry
        del adj[usage_key]

    def remove_block(self, usage_key):
        """
        Arguments:
            usage_key (UsageKey)

        Raises:
            KeyError if block does not exist in course structure.
        """
        # This is just a wrapper around _remove_block because we don't want to
        # expose the remove_orphans option.
        self._remove_block(usage_key, remove_orphans=True)

    def remove_block_if(self, removal_condition):
        """
        Arguments:
            removal_condition (UsageKey -> bool)
        """
        adj = self._adj

        traversal = traverse_topologically(
            start_node=self.root_block_key,
            get_parents=self.get_parents,
            get_children=self.get_children
        )
        for usage_key in traversal:
            is_orphan = not adj[usage_key].parents
            if is_orphan or removal_condition(usage_key):
                # Because we're doing a topological sort, removing blocks can
                # only create orphans *later* in the traversal. So, we save time
                # by passing remove_orphans=False and handling orphan removal
                # ourselves.
                self._remove_block(usage_key, remove_orphans=False)


class CourseBlockData(object):
    """
    ...
    """

    def __init__(self, block_fields, transformation_data):
        """
        Arguments:
            block_fields (dict[str: *])
            transformation_data (dict[str: dict]):
                Dictionary mapping transformations' IDs to their collected data.
                {
                    'builtin.visibility': { 'visible_to_staff_only': ... }
                    'another_trans_id': { 'key1': value, 'key2': value2 ... }
                    ...
                }
        """
        self._block_fields = block_fields
        self._transformation_data = transformation_data

    def get_block_field(self, field_name):
        """
        Arguments:
            field_name: str

        Returns:
            *
        """
        return self._block_fields[field_name]

    def get_transformation_data(self, transformation_id, key):
        """
        Arguments:
            transformation_id: str
            key: str

        Returns:
            *
        """
        if transformation_id in self._transformation_data:
            return self._transformation_data[transformation_id][key]
        else:
            raise KeyError(
                "Data for transformation with ID {} not found.".format(
                    transformation_id
                )
            )
