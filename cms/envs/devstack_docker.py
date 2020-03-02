""" Overrides for Docker-based devstack. """

from .devstack import *  # pylint: disable=wildcard-import, unused-wildcard-import

# Docker does not support the syslog socket at /dev/log. Rely on the console.
LOGGING['handlers']['local'] = LOGGING['handlers']['tracking'] = {
    'class': 'logging.NullHandler',
}

LOGGING['loggers']['tracking']['handlers'] = ['console']

LMS_BASE = 'localhost:18000'
CMS_BASE = 'localhost:18010'
LMS_ROOT_URL = 'http://{}'.format(LMS_BASE)

FEATURES.update({
    'ENABLE_COURSEWARE_INDEX': False,
    'ENABLE_LIBRARY_INDEX': False,
    'ENABLE_DISCUSSION_SERVICE': True,
})

CREDENTIALS_SERVICE_USERNAME = 'credentials_worker'

JWT_AUTH.update({
    'JWT_ISSUER': '{}/oauth2'.format(LMS_ROOT_URL),
    'JWT_SECRET_KEY': 'lms-secret',
    'JWT_AUDIENCE': 'lms-key',
})
