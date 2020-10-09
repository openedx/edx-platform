"""
Custom routers used by both lms and cms when routing tasks to worker queues.

For more, see https://celery.readthedocs.io/en/latest/userguide/routing.html#routers
"""

import logging
from abc import ABCMeta, abstractproperty

from django.conf import settings
import six

log = logging.getLogger(__name__)


def ensure_queue_env(desired_env):
    """
    Helper method to get the desired type of queue.

    If no such queue is defined, default routing logic is used.
    """
    queues = getattr(settings, 'CELERY_QUEUES', None)
    return next(
        (
            queue
            for queue in queues
            if '.{}.'.format(desired_env) in queue
        ),
        None
    )
