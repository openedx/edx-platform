# -*- coding: utf-8 -*-
"""
Settings for Bok Choy tests that are used when running Studio in Docker-based devstack.
"""

# noinspection PyUnresolvedReferences
from .bok_choy import *  # pylint: disable=wildcard-import

CMS_BASE = '{}:{}'.format(os.environ['BOK_CHOY_HOSTNAME'], os.environ['BOK_CHOY_CMS_PORT'])
LMS_BASE = '{}:{}'.format(os.environ['BOK_CHOY_HOSTNAME'], os.environ['BOK_CHOY_LMS_PORT'])
LMS_ROOT_URL = 'http://{}'.format(LMS_BASE)

# Docker does not support the syslog socket at /dev/log. Rely on the console.
LOGGING['handlers']['local'] = LOGGING['handlers']['tracking'] = {
    'class': 'logging.NullHandler',
}

LOGGING['loggers']['tracking']['handlers'] = ['console']
