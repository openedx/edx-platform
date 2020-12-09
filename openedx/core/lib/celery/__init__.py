"""
Common celery utilities.
"""

import threading

SINGLETON_LOCK = threading.Lock()
# Variant of edxapp that we're running celery for. If None, celery has
# not been instantiated; if a string ("lms" or "cms"), celery has been
# instantiated for that variant.
SINGLETON_VARIANT = None


def assert_celery_uninstantiated(variant):
    """
    Raise if celery is already instantiated for the other variant of edxapp.

    Specifically, raise if this function is called multiple times with
    different variant values. Safe to call multiple times with same variant.
    """
    global SINGLETON_VARIANT
    with SINGLETON_LOCK:
        if SINGLETON_VARIANT is None:
            SINGLETON_VARIANT = variant
        elif SINGLETON_VARIANT != variant:
            raise Exception(
                f"Conflicting assertions for celery singleton; "
                f"already asserted variant='{SINGLETON_VARIANT}', "
                f"attempted to assert variant='{variant}'"
            )
