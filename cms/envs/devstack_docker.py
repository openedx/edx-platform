""" Overrides for Docker-based devstack. """

from .devstack import *  # pylint: disable=wildcard-import, unused-wildcard-import

# Docker does not support the syslog socket at /dev/log. Rely on the console.
LOGGING['handlers']['local'] = LOGGING['handlers']['tracking'] = {
    'class': 'logging.NullHandler',
}

LOGGING['loggers']['tracking']['handlers'] = ['console']

LMS_ROOT_URL = 'http://edx.devstack.lms:18000'

FEATURES.update({
    'ENABLE_COURSEWARE_INDEX': False,
    'ENABLE_LIBRARY_INDEX': False,
})
