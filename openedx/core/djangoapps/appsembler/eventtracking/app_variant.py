"""
Contextual utilities for knowing where app is running and being instantiated.

Separating these from other utilities to avoid breaking plugin architecture
code which is easy to do if you have a bad import during plugin instantiation.
Stevedore swallows errors and you are none the wiser :(...
So, don't add imports to this that will fail before Django has fully loaded.
"""

import os
import sys


def is_celery_worker():
    """Utility function: return False if not a Celery worker."""
    # Use this instead of common.djangoapps.track.shim.is_celery_worker
    # ... as that relies on settings which is only lazy-loaded when
    # ... plugin apps are instantiated.
    return os.getenv('CELERY_WORKER_RUNNING', False)


def is_not_lms():
    """Utility function: return False if not running in the LMS."""
    return os.getenv("SERVICE_VARIANT") != 'lms'


def is_not_runserver():
    """Utility function: return False if not runserver command."""
    return 'runserver' not in sys.argv
