"""
Contextual utilities for knowing where app is running and being instantiated.

Separating these from other utilities to avoid breaking plugin architecture
code which is easy to do if you have a bad import during plugin instantiation.
Stevedore swallows errors and you are none the wiser :(...
So, don't add imports to this that will fail before Django has fully loaded.
"""

import os
import sys


def is_lms():
    """Utility function: return True if running in the LMS."""
    return os.getenv("SERVICE_VARIANT") == 'lms'


def is_lms_test():
    """
    Utility function: return False if this is in a test.

    It's ugly but needed to run in LMS tests and not in CMS tests,
    to keep SQL query counts as expected.
    """
    argstr = ' '.join(sys.argv)
    return (
        'pytest ' in argstr and
        'cms/' not in argstr
    )


def is_not_runserver():
    """Utility function: return False if not runserver command."""
    return 'runserver' not in sys.argv
