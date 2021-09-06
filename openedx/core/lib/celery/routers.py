"""
Custom routers used by both lms and cms when routing tasks to worker queues.

For more, see https://celery.readthedocs.io/en/latest/userguide/routing.html#routers
"""

import logging
from abc import ABCMeta, abstractproperty

from django.conf import settings
import six

log = logging.getLogger(__name__)


class AlternateEnvironmentRouter(six.with_metaclass(ABCMeta, object)):
    """
    A custom Router class for use in routing celery tasks to non-default queues.
    """

    @abstractproperty
    def alternate_env_tasks(self):
        """
        Defines the task -> alternate worker environment to be used when routing.

        Subclasses must override this property with their own specific mappings.
        """
        return {}

    @property
    def explicit_queues(self):
        """
        Defines the task -> alternate worker queue to be used when routing.
        """
        return {}

    def route_for_task(self, task, args=None, kwargs=None):  # pylint: disable=unused-argument
        """
        Celery-defined method allowing for custom routing logic.

        If None is returned from this method, default routing logic is used.
        """
        if task in self.explicit_queues:
            return self.explicit_queues[task]

        alternate_env = self.alternate_env_tasks.get(task, None)
        if alternate_env:
            return self.ensure_queue_env(alternate_env)

        return None

    def ensure_queue_env(self, desired_env):
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
