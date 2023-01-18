"""
Contextual utilities for knowing where app is running and being instantiated.

Separating these from other utilities to avoid breaking plugin architecture
code which is easy to do if you have a bad import during plugin instantiation.
Stevedore swallows errors and you are none the wiser :(...
So, don't add imports to this that will fail before Django has fully loaded.
"""

import inspect
import os
import sys


def is_lms():
    """Utility function: return True if running in the LMS."""
    return os.getenv("SERVICE_VARIANT") == 'lms'


def is_self_test():
    """
    Utility function: return True if this is in an LMS test from within the
    openedx.core.djangoapps.appsembler.eventtracking.test_tahoeusermetadata module.

    It's ugly but needed to only run in its own tests, to keep SQL query counts as expected
    in other tests.
    """
    callstack = inspect.stack()
    stack_filenames = [fi.filename for fi in callstack]
    is_own_package_test = any(
        ['appsembler/eventtracking/tests/' in fi for fi in stack_filenames]
    )
    return is_own_package_test


def is_not_runserver():
    """Utility function: return True if not a runserver command."""
    return 'runserver' not in sys.argv
