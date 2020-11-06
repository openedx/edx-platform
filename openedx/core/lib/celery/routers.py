"""
Custom routers used by both lms and cms when routing tasks to worker queues.

For more, see https://celery.readthedocs.io/en/latest/userguide/routing.html#routers
"""

import logging
from abc import ABCMeta, abstractproperty

from django.conf import settings
import six

log = logging.getLogger(__name__)


def route_task_queue(name, explicit_queues, alternate_env_tasks):
    """
    Helper method allowing for custom routing logic.

    If None is returned from this method, default routing logic is used.
    """
    if name in explicit_queues:
        return explicit_queues[name]

    alternate_env = alternate_env_tasks.get(name, None)
    if alternate_env:
        return ensure_queue_env(alternate_env)


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
