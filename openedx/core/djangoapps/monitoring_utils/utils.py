"""
Monitoring utilities which aren't used by the application by default, but can
be used as needed to troubleshoot problems.
"""
from __future__ import absolute_import, print_function

import gc
import itertools
import logging
import operator
import os
import socket
import sys
import tempfile
from StringIO import StringIO
from collections import defaultdict

from django.conf import settings
from django.core.servers.basehttp import WSGIServer as DjangoWSGIServer
from django.utils.lru_cache import lru_cache

import gunicorn.util
from objgraph import (
    _long_typename,
    _short_typename,
    at_addrs,
    show_backrefs,
    show_refs,
)

from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace

indices = defaultdict(itertools.count)

# The directory in which graph files will be created.
GRAPH_DIRECTORY_PATH = settings.MEMORY_GRAPH_DIRECTORY

# The max number of object types for which to show data on the console
MAX_CONSOLE_ROWS = 30

# The max number of object types for which to generate reference graphs
MAX_GRAPHED_OBJECT_TYPES = 5

# Maximum depth of forward reference graphs
REFS_DEPTH = 3

# Maximum depth of backward reference graphs
BACK_REFS_DEPTH = 8

# Max number of objects per type to use as starting points in the reference graphs
MAX_OBJECTS_PER_TYPE = 10

# Object type names for which table rows and graphs should not be generated if
# the new object count is below the given threshold.  "set" is ignored by
# default because many sets are created in the course of tracking the number
# of new objects of each type.  "ApdexStats", "SplitResult", and "TimeStats"
# are New Relic data which sometimes outlives the duration of the request but
# usually doesn't stick around long-term.
IGNORE_THRESHOLDS = {
    'ApdexStats': 10,
    'SplitResult': 50,
    'TimeStats': 500,
    'set': 10000,
}

WAFFLE_NAMESPACE = 'monitoring_utils'

log = logging.getLogger(__name__)


def show_memory_leaks(
        label=u'memory_leaks',
        max_console_rows=MAX_CONSOLE_ROWS,
        max_graphed_object_types=MAX_GRAPHED_OBJECT_TYPES,
        refs_depth=REFS_DEPTH,
        back_refs_depth=BACK_REFS_DEPTH,
        max_objects_per_type=MAX_OBJECTS_PER_TYPE,
        ignore_thresholds=None,
        graph_directory_path=GRAPH_DIRECTORY_PATH,
        memory_table_buffer=None,
        skip_first_graphs=True):
    """
    Call this function to get data about memory leaks; what objects are being
    leaked, where did they come from, and what do they contain?  The leaks
    are measured from the last call to ``get_new_ids()`` (which is called
    within this function).  Some data is printed to stdout, and more details
    are available in graphs stored at the paths printed to stdout.  Subsequent
    calls with the same label are indicated by an increasing index in the
    filename.

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
        ignore_thresholds (dict): Object type names for which table rows and
            graphs should not be generated if the new object count is below
            the corresponding number.
        graph_directory_path (unicode): The directory in which graph files
            will be created.  It will be created if it doesn't already exist.
        memory_table_buffer (StringIO): Storage for the generated table of
            memory statistics.  Ideally, create this before starting to
            count newly allocated objects.
        skip_first_graphs (bool): True if the first call to this function for
            a given label should not produce graphs (the default behavior).
            The first call to a given block of code often initializes an
            assortment of objects which aren't really leaked memory.
    """
    if graph_directory_path is None:
        graph_directory_path = MemoryUsageData.graph_directory_path()
    if ignore_thresholds is None:
        ignore_thresholds = IGNORE_THRESHOLDS
    if memory_table_buffer is None:
        memory_table_buffer = StringIO()
    new_ids = get_new_ids(limit=max_console_rows, ignore_thresholds=ignore_thresholds,
                          output=memory_table_buffer)
    memory_table_text = memory_table_buffer.getvalue()
    log.info('\n' + memory_table_text)

    if not os.path.exists(graph_directory_path):
        os.makedirs(graph_directory_path)
    label = label.replace(':', '_')
    index = indices[label].next() + 1
    data = {'label': label, 'index': index}
    path = os.path.join(graph_directory_path, u'{label}_{index}.txt'.format(**data))
    with open(path, 'w') as f:
        f.write(memory_table_text)

    if index == 1 and skip_first_graphs:
        return

    graphed_types = 0
    sorted_by_count = sorted(new_ids.items(), key=lambda entry: len(entry[1]), reverse=True)
    for item in sorted_by_count:
        type_name = item[0]
        object_ids = new_ids[type_name]
        if not object_ids:
            continue
        objects = at_addrs(list(object_ids)[:max_objects_per_type])
        data['type_name'] = type_name

        if back_refs_depth > 0:
            path = os.path.join(graph_directory_path, u'{label}_{index}_{type_name}_backrefs.dot'.format(**data))
            show_backrefs(objects, max_depth=back_refs_depth, filename=path)
            log.info('Generated memory graph at {}'.format(path))

        if refs_depth > 0:
            path = os.path.join(graph_directory_path, u'{label}_{index}_{type_name}_refs.dot'.format(**data))
            show_refs(objects, max_depth=refs_depth, filename=path)
            log.info('Generated memory graph at {}'.format(path))

        graphed_types += 1
        if graphed_types >= max_graphed_object_types:
            break


class MemoryUsageData(object):
    """
    Memory analysis data and configuration options for the current request.
    Do *NOT* use this in production; it slows down most requests by about an
    order of magnitude, even the ones which aren't being specifically studied.

    Call ``MemoryUsageData.analyze()`` from a view and enable the appropriate
    waffle switch(es) to start generating memory leak diagnostic information:

    * monitoring_utils.log_memory_tables - Log a table of data on object types
      for which the total number in memory increased during the request.
      Enabling this switch disables Django Debug Toolbar, since it leaks
      many objects with every request.

    * monitoring_utils.create_memory_graphs - Also generate reference graphs
      for some of the apparently leaked objects.

    When using this in development via Django's runserver command, be sure to
    pass it the ``--nothreading`` option to avoid concurrent memory changes
    while serving static assets.  In devstack, do this in docker-compose.yml.

    To use this feature on a sandbox, you also need to append
    ``openedx.core.djangoapps.monitoring_utils.apps.MonitoringUtilsConfig`` to
    the end of the ``INSTALLED_APPS`` Django setting.  This is present by
    default for devstack and load test environments, but absent from the
    ``aws`` settings module to avoid a little overhead at the start of each
    request even when the Waffle switches are disabled (mainly just to load
    the switch from the database).

    Configuration options for the depth of the graphs, how many leaked
    objects of each type to graph, and so forth are currently set as constants
    in ``monitoring_utils.utils``.  The graphs are saved as GraphViz .dot
    files in the directory specified by the ``MEMORY_GRAPH_DIRECTORY`` Django
    setting.  These can be viewed directly using xdot (Linux) or ZGRViewer
    (macOS), or converted to a standard image format such as PNG or SVG using
    GraphViz.
    """
    graphs_are_enabled = False
    tables_are_enabled = False
    table_buffer = None
    view_name = None
    gunicorn_is_patched = False

    @classmethod
    def start_counting(cls):
        """
        Prepare to collect memory usage data for a new request.
        """
        if cls._is_switch_enabled(u'log_memory_tables'):
            if not cls.gunicorn_is_patched:
                cls._patch_gunicorn()
            cls.tables_are_enabled = True
            cls.table_buffer = StringIO()
            cls.graphs_are_enabled = cls._is_switch_enabled(u'create_memory_graphs')
            cls._set_memory_leak_baseline()

    @classmethod
    def analyze(cls, request):
        """
        Call this anywhere in a view to record memory usage data at the end
        of the request.
        """
        cls.view_name = request.resolver_match.view_name

    @classmethod
    def stop_counting(cls):
        """
        Stop collecting memory usage data for the current request, and
        generate any requested output for it.
        """
        if cls.tables_are_enabled and cls.view_name:
            if cls.graphs_are_enabled:
                show_memory_leaks(cls.view_name, memory_table_buffer=cls.table_buffer)
            else:
                show_memory_leaks(cls.view_name, refs_depth=0,
                                  back_refs_depth=0, memory_table_buffer=cls.table_buffer)
        cls._reset()

    @classmethod
    @lru_cache()
    def graph_directory_path(cls):
        """
        Get the default temporary directory for the current process in which
        to store memory reference graphs.
        """
        if settings.ROOT_URLCONF == 'lms.urls':
            service = 'lms'
        else:
            service = 'cms'
        return os.path.join(tempfile.mkdtemp(prefix='memory_graphs'),
                            '{service}_{pid}'.format(service=service, pid=os.getpid()))

    @staticmethod
    def _is_switch_enabled(name):
        return WaffleSwitchNamespace(name=WAFFLE_NAMESPACE).is_enabled(name)

    @classmethod
    def _patch_gunicorn(cls):
        """
        Patch gunicorn to record memory usage data when appropriate.  Django's
        ``request_finished`` signal and gunicorn's ``post_request`` hook
        aren't called late enough to be useful for this; the response is still
        in scope, so none of the objects attached to it can be garbage
        collected yet.
        """
        gunicorn.util.close = gunicorn_util_close
        cls.gunicorn_is_patched = True

    @classmethod
    def _reset(cls):
        """
        Reset all the attributes to their default values in preparation for a
        new request.
        """
        cls.graphs_are_enabled = False
        cls.tables_are_enabled = False
        cls.table_buffer = None
        cls.view_name = None

    @classmethod
    def _set_memory_leak_baseline(cls):
        """
        Reset the starting point from which the next call to
        ``objgraph.get_new_ids()`` will count newly created objects.
        """
        with open(os.devnull, 'w') as devnull:
            get_new_ids(output=devnull)


def gunicorn_util_close(sock):
    """
    Replacement for gunicorn.util.close() which does memory usage analysis if
    the relevant Waffle switch was active at the start of the request.

    This monkeypatch is appropriate for gunicorn==0.17.4 and should be updated
    as needed when upgrading gunicorn.
    """
    try:
        sock.close()
    except socket.error:
        pass
    MemoryUsageData.stop_counting()


class WSGIServer(DjangoWSGIServer):
    """
    A WSGI server to be used by Django's runserver management command so that
    memory usage can be analyzed after the response is garbage collected.
    Specified by the ``WSGI_SERVER`` Django setting in the devstack settings
    files.
    """
    def close_request(self, request):
        MemoryUsageData.stop_counting()


# The following is copied and modified from objgraph, since it doesn't yet
# provide good hooks for customizing this operation

def get_new_ids(skip_update=False, limit=10, sortby='deltas',  # pylint: disable=dangerous-default-value
                shortnames=None, ignore_thresholds=IGNORE_THRESHOLDS,
                output=None, _state={}):
    """Find and display new objects allocated since last call.

    Shows the increase in object counts since last call to this
    function and returns the memory address ids for new objects.

    Returns a dictionary mapping object type names to sets of object IDs
    that have been created since the last time this function was called.

    ``skip_update`` (bool): If True, returns the same dictionary that
    was returned during the previous call without updating the internal
    state or examining the objects currently in memory.

    ``limit`` (int): The maximum number of rows that you want to print
    data for.  Use 0 to suppress the printing.  Use None to print everything.

    ``sortby`` (str): This is the column that you want to sort by in
    descending order.  Possible values are: 'old', 'current', 'new',
    'deltas'

    ``shortnames`` (bool): If True, classes with the same name but
    defined in different modules will be lumped together.  If False,
    all type names will be qualified with the module name.  If None (default),
    ``get_new_ids`` will remember the value from previous calls, so it's
    enough to prime this once.  By default the primed value is True.

    ``_state`` (dict): Stores old, current, and new_ids in memory.
    It is used by the function to store the internal state between calls.
    Never pass in this argument unless you know what you're doing.

    The caveats documented in :func:`growth` apply.

    When one gets new_ids from :func:`get_new_ids`, one can use
    :func:`at_addrs` to get a list of those objects. Then one can iterate over
    the new objects, print out what they are, and call :func:`show_backrefs` or
    :func:`show_chain` to see where they are referenced.

    Example:

        >>> _ = get_new_ids() # store current objects in _state
        >>> _ = get_new_ids() # current_ids become old_ids in _state
        >>> a = [0, 1, 2] # list we don't know about
        >>> b = [3, 4, 5] # list we don't know about
        >>> new_ids = get_new_ids(limit=3) # we see new lists
        ======================================================================
        Type                    Old_ids  Current_ids      New_ids Count_Deltas
        ======================================================================
        list                        324          326           +3           +2
        dict                       1125         1125           +0           +0
        wrapper_descriptor         1001         1001           +0           +0
        ======================================================================
        >>> new_lists = at_addrs(new_ids['list'])
        >>> a in new_lists
        True
        >>> b in new_lists
        True
    """
    if ignore_thresholds is None:
        ignore_thresholds = IGNORE_THRESHOLDS
    _initialize_state(_state)
    new_ids = _state['new']
    if skip_update:
        return new_ids
    old_ids = _state['old']
    current_ids = _state['current']
    if shortnames is None:
        shortnames = _state['shortnames']
    else:
        _state['shortnames'] = shortnames
    gc.collect()
    objects = gc.get_objects()
    for class_name in old_ids:
        old_ids[class_name].clear()
    for class_name, ids_set in current_ids.items():
        old_ids[class_name].update(ids_set)
    for class_name in current_ids:
        current_ids[class_name].clear()
    for o in objects:
        if shortnames:
            class_name = _short_typename(o)
        else:
            class_name = _long_typename(o)
        id_number = id(o)
        current_ids[class_name].add(id_number)
    for class_name in new_ids:
        new_ids[class_name].clear()
    rows = []
    keys_to_remove = []
    for class_name in current_ids:
        num_old = len(old_ids[class_name])
        num_current = len(current_ids[class_name])
        if num_old == 0 and num_current == 0:
            # remove the key from our dicts if we don't have any old or
            # current class_name objects
            keys_to_remove.append(class_name)
            continue
        new_ids_set = current_ids[class_name] - old_ids[class_name]
        new_ids[class_name].update(new_ids_set)
        num_new = len(new_ids_set)
        num_delta = num_current - num_old
        if num_delta < 1 or (class_name in ignore_thresholds and num_current < ignore_thresholds[class_name]):
            # ignore types with no net increase or whose overall count isn't large enough to worry us
            if class_name in new_ids:
                del new_ids[class_name]
            continue
        row = (class_name, num_old, num_current, num_new, num_delta)
        rows.append(row)
    for key in keys_to_remove:
        del old_ids[key]
        del current_ids[key]
        if key in new_ids:
            del new_ids[key]
    index_by_sortby = {'old': 1, 'current': 2, 'new': 3, 'deltas': 4}
    rows.sort(key=operator.itemgetter(index_by_sortby[sortby], 0),
              reverse=True)
    _show_results(rows, limit, output)
    return new_ids


def _initialize_state(state):
    """
    Initialize the object ID tracking data if it hasn't been done yet.
    """
    if not state:
        state['old'] = defaultdict(set)
        state['current'] = defaultdict(set)
        state['new'] = defaultdict(set)
        state['shortnames'] = True


def _show_results(rows, limit, output):
    """
    Show information about the memory leaked since the previous call to
    ``get_new_ids()``.

    Args:
        rows (list): The data rows to be displayed (if any)
        limit (int): The max number of rows to display
        output (stream): The output stream to send results to
    """
    if output is None:
        output = sys.stdout
    if not rows:
        _show_no_leaks_message(output)
    else:
        _show_leaks_table(rows, limit, output)


def _show_no_leaks_message(output):
    """
    Print a message, indicating that no memory leaks were found, to the given
    output stream.
    """
    print('=' * 51, file=output)
    print('No object types increased their net count in memory', file=output)
    print('=' * 51, file=output)


def _show_leaks_table(rows, limit, output):
    """
    Print a summary table of the leaked objects to the given output stream.
    """
    if limit is not None:
        rows = rows[:limit]
    width = max(len(row[0]) for row in rows)
    print('=' * (width + 13 * 4), file=output)
    print('%-*s%13s%13s%13s%13s' %
          (width, 'Type', 'Old_ids', 'Current_ids', 'New_ids', 'Count_Deltas'),
          file=output)
    print('=' * (width + 13 * 4), file=output)
    for row_class, old, current, new, delta in rows:
        print('%-*s%13d%13d%+13d%+13d' %
              (width, row_class, old, current, new, delta), file=output)
    print('=' * (width + 13 * 4), file=output)
