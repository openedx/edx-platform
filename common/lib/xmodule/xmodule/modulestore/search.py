from itertools import repeat
from .exceptions import (ItemNotFoundError, NoPathToItem)


def path_to_location(modulestore, usage_key):
    '''
    Try to find a course_id/chapter/section[/position] path to location in
    modulestore.  The courseware insists that the first level in the course is
    chapter, but any kind of module can be a "section".

    location: something that can be passed to Location
    course_id: Search for paths in this course.

    raise ItemNotFoundError if the location doesn't exist.

    raise NoPathToItem if the location exists, but isn't accessible via
    a chapter/section path in the course(s) being searched.

    Return a tuple (course_id, chapter, section, position) suitable for the
    courseware index view.

    A location may be accessible via many paths. This method may
    return any valid path.

    If the section is a sequential or vertical, position will be the position
    of this location in that sequence.  Otherwise, position will
    be None. TODO (vshnayder): Not true yet.
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

            # get_parent_locations should raise ItemNotFoundError if location
            # isn't found so we don't have to do it explicitly.  Call this
            # first to make sure the location is there (even if it's a course, and
            # we would otherwise immediately exit).
            parents = modulestore.get_parent_locations(next_usage)

            # print 'Processing loc={0}, path={1}'.format(next_usage, path)
            if next_usage.definition_key.block_type == "course":
                # Found it!
                path = (next_usage, path)
                return flatten(path)

            # otherwise, add parent locations at the end
            newpath = (next_usage, path)
            queue.extend(zip(parents, repeat(newpath)))

        # If we're here, there is no path
        return None

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
            category = path[path_index].definition_key.block_type
            if category == 'sequential' or category == 'videosequence':
                section_desc = modulestore.get_item(path[path_index])
                child_locs = [c.location for c in section_desc.get_children()]
                # positions are 1-indexed, and should be strings to be consistent with
                # url parsing.
                position_list.append(str(child_locs.index(path[path_index + 1]) + 1))
        position = "_".join(position_list)

    return (course_id, chapter, section, position)
