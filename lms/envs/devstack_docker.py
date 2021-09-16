"""
Left over environment file from before the transition of devstack from
vagrant to docker was complete.

This file should no longer be used, and is only around in case something
still refers to it.
"""

from .devstack import *  # pylint: disable=wildcard-import, unused-wildcard-import

OPEN_EDX_FILTERS_CONFIG = {
    "org.openedx.learning.course.enrollment.started.v1": {
        "pipeline": [
            "openedx_basic_hooks.filters.enrollment.avoid_enrollment",
        ],
        "fail_silently": False,
    }
}
