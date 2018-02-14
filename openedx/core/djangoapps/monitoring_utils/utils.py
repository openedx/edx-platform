"""
Monitoring utilities which aren't used by the application by default, but can
be used as needed to troubleshoot problems.
"""

import os

import objgraph
from django.conf import settings

indices = {}

MAX_CONSOLE_ROWS = 10
MAX_GRAPHED_OBJECT_TYPES = 5
REFS_DEPTH = 3
BACK_REFS_DEPTH = 8
MAX_OBJECTS_PER_TYPE = 5
IGNORED_TYPES = ('set',)


def show_memory_leaks(
        label=u'memory_leaks',
        max_console_rows=MAX_CONSOLE_ROWS,
        max_graphed_object_types=MAX_GRAPHED_OBJECT_TYPES,
        refs_depth=REFS_DEPTH,
        back_refs_depth=BACK_REFS_DEPTH,
        max_objects_per_type=MAX_OBJECTS_PER_TYPE,
        ignored_types=IGNORED_TYPES):
    """
    Call this function to get data about memory leaks; what objects are being
    leaked, where did they come from, and what do they contain?  The leaks
    are measured from the last call to ``objgraph.get_new_ids()`` (which is
    called within this function).  Some data is printed to stdout, and more
    details are available in graphs stored in ``test_root/log/memory_graphs``.
    Subsequent calls with the same label are indicated by an increasing index
    in the filename.

    Args:
        label (unicode): The start of the filename for each graph
        max_console_rows (int): The max number of object types for which to
            show data on the console
        max_graphed_object_types (int): The max number of object types for
            which to generate reference graphs
        refs_depth (int): Maximum depth of forward reference graphs
        back_refs_depth (int): Maximum depth of backward reference graphs
        max_objects_per_type (int): Max number of objects per type to use as
            starting points in the reference graphs
        ignored_types (iterable): Object type names for which graphs should
            not be generated even if the new object count is high.  "set" is
            ignored by default because many sets are created in the course of
            tracking the number of new objects of each type.
    """
    new_ids = objgraph.get_new_ids(limit=max_console_rows)
    index = indices.setdefault(label, 1)
    indices[label] += 1
    sorted_by_count = sorted(new_ids.items(), key=lambda entry: len(entry[1]), reverse=True)

    dir_path = settings.REPO_ROOT / 'test_root' / 'log' / 'memory_graphs'
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    for item in sorted_by_count[:max_graphed_object_types]:
        type_name = item[0]
        object_ids = new_ids[type_name]
        if type_name in ignored_types or len(object_ids) == 0:
            continue
        objects = objgraph.at_addrs(object_ids)[:max_objects_per_type]
        data = {'dir': dir_path, 'label': label, 'index': index, 'type_name': type_name}
        objgraph.show_backrefs(objects, max_depth=back_refs_depth,
                               filename=u'{dir}/{label}_{index}_{type_name}_backrefs.dot'.format(**data))
        objgraph.show_refs(objects, max_depth=refs_depth,
                           filename=u'{dir}/{label}_{index}_{type_name}_refs.dot'.format(**data))
