"""
Custom routers used by both lms and cms when routing tasks to worker queues.

For more, see https://celery.readthedocs.io/en/latest/userguide/routing.html#routers
"""

import logging


log = logging.getLogger(__name__)


def route_task_queue(name):
    """
    Helper method allowing for custom routing logic.

    If None is returned from this method, default routing logic is used.
    """
    from django.conf import settings  # pylint: disable=import-outside-toplevel

    if name in settings.EXPLICIT_QUEUES:
        return settings.EXPLICIT_QUEUES[name]

    alternate_env = settings.ALTERNATE_ENV_TASKS.get(name, None)
    if alternate_env:
        return ensure_queue_env(alternate_env)


def ensure_queue_env(desired_env):
    """
    Helper method to get the desired type of queue.

    If no such queue is defined, default routing logic is used.
    """
    from django.conf import settings  # pylint: disable=import-outside-toplevel

    queues = getattr(settings, 'CELERY_QUEUES', None)
    return next(
        (
            queue
            for queue in queues
            if '.{}.'.format(desired_env) in queue
        ),
        None
    )
