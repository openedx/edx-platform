"""
Contains the Acceptance tests.
"""
from __future__ import absolute_import

import logging

# Silence noisy loggers
LOG_OVERRIDES = [
    ('requests.packages.urllib3.connectionpool', logging.ERROR),
    ('django.db.backends', logging.ERROR),
    ('stevedore.extension', logging.ERROR),
]

for log_name, log_level in LOG_OVERRIDES:
    logging.getLogger(log_name).setLevel(log_level)
