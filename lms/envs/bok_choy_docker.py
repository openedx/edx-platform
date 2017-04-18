# -*- coding: utf-8 -*-
""" Bok-choy settings for Docker-based devstack. """

# noinspection PyUnresolvedReferences
from .bok_choy import *  # pylint: disable=wildcard-import

CONTENTSTORE['DOC_STORE_CONFIG']['host'] = 'edx.devstack.mongo'

# Docker does not support the syslog socket at /dev/log. Rely on the console.
LOGGING['handlers']['local'] = LOGGING['handlers']['tracking'] = {
    'class': 'logging.NullHandler',
}

LOGGING['loggers']['tracking']['handlers'] = ['console']

