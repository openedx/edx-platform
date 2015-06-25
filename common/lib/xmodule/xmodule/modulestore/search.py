''' useful functions for finding content and its position '''
from logging import getLogger

from .exceptions import (ItemNotFoundError, NoPathToItem)

LOGGER = getLogger(__name__)


def path_to_location(modulestore, usage_key):
    '''
    Try to find a course_id/chapter/section[/position] path to location in
    modulestore.  The courseware insists that the first level in the course is
    chapter, but any kind of module can be a "section".

    Args:
        modulestore: which store holds the relevant objects
        usage_key: :class:`UsageKey` the id of the location to which to generate the path

    Raises
        ItemNotFoundError if the location doesn't exist.
        NoPathToItem if the location exists, but isn't accessible via
            a chapter/section path in the course(s) being searched.

    Returns:
        a tuple (course_id, chapter, section, position) suitable for the
        courseware index view.

    If the section is a sequential or vertical, position will be the children index
    of this location under that sequence.
    '''

    def flatten(xs):
        '''Convert lisp-style (a, (b, (c, ()))) list into a python list.
        Not a general flatten function. '''
        p = []
        while xs != ():
            p.append(xs[0])
            xs = xs[1]
        return p

    def find_path_to_course():
        '''Find a path up the location graph to a node with the
        specified category.

        If no path exists, return None.

        If a path exists, return it as a list with target location first, and
        the starting location last.
        '''
        # Standard DFS

        # To keep track of where we came from, the work queue has
        # tuples (location, path-so-far).  To avoid lots of
        # copying, the path-so-far is stored as a lisp-style
        # list--nested hd::tl tuples, and flattened at the end.
        queue = [(usage_key, ())]
        while len(queue) > 0:
            (next_usage, path) = queue.pop()  # Takes from the end

            # get_parent_location raises ItemNotFoundError if location isn't found
            parent = modulestore.get_parent_location(next_usage)

            # print 'Processing loc={0}, path={1}'.format(next_usage, path)
            if next_usage.block_type == "course":
                # Found it!
                path = (next_usage, path)
                return flatten(path)
            elif parent is None:
                # Orphaned item.
                return None

            # otherwise, add parent locations at the end
            newpath = (next_usage, path)
            queue.append((parent, newpath))

    with modulestore.bulk_operations(usage_key.course_key):
        if not modulestore.has_item(usage_key):
            raise ItemNotFoundError(usage_key)

        path = find_path_to_course()
        if path is None:
            raise NoPathToItem(usage_key)

        n = len(path)
        course_id = path[0].course_key
        # pull out the location names
        chapter = path[1].name if n > 1 else None
        section = path[2].name if n > 2 else None
        # Figure out the position
        position = None

        # This block of code will find the position of a module within a nested tree
        # of modules. If a problem is on tab 2 of a sequence that's on tab 3 of a
        # sequence, the resulting position is 3_2. However, no positional modules
        # (e.g. sequential and videosequence) currently deal with this form of
        # representing nested positions. This needs to happen before jumping to a
        # module nested in more than one positional module will work.
        if n > 3:
            position_list = []
            for path_index in range(2, n - 1):
                category = path[path_index].block_type
                if category == 'sequential' or category == 'videosequence':
                    section_desc = modulestore.get_item(path[path_index])
                    # this calls get_children rather than just children b/c old mongo includes private children
                    # in children but not in get_children
                    child_locs = [c.location for c in section_desc.get_children()]
                    # positions are 1-indexed, and should be strings to be consistent with
                    # url parsing.
                    position_list.append(str(child_locs.index(path[path_index + 1]) + 1))
            position = "_".join(position_list)

        return (course_id, chapter, section, position)


def navigation_index(position):
    """
    Get the navigation index from the position argument (where the position argument was recieved from a call to
    path_to_location)

    Argument:
    position - result of position returned from call to path_to_location. This is an underscore (_) separated string of
    vertical 1-indexed positions. If the course is built in Studio then you'll never see verticals as children of
    verticals, and so extremely often one will only see the first vertical as an integer position. This specific action
    is to allow navigation / breadcrumbs to locate the topmost item because this is the location actually required by
    the LMS code

    Returns:
    1-based integer of the position of the desired item within the vertical
    """
    if position is None:
        return None

    try:
        navigation_position = int(position.split('_', 1)[0])
    except (ValueError, TypeError):
        LOGGER.exception(u'Bad position %r passed to navigation_index, will assume first position', position)
        navigation_position = 1

    return navigation_position
