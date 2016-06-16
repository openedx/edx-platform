"""
Custom routers used by both lms and cms when routing tasks to worker queues.

For more, see http://celery.readthedocs.io/en/latest/userguide/routing.html#routers
"""
from abc import ABCMeta, abstractproperty
from django.conf import settings


class AlternateEnvironmentRouter(object):
    """
    A custom Router class for use in routing celery tasks to non-default queues.
    """
    # this is an abstract base class, implementations must provide alternate_env_tasks
    __metaclass__ = ABCMeta

    @abstractproperty
    def alternate_env_tasks(self):
        """
        Defines the task -> alternate worker environment queue to be used when routing.

        Subclasses must override this property with their own specific mappings.
        """
        return {}

    def route_for_task(self, task, args=None, kwargs=None):  # pylint: disable=unused-argument
        """
        Celery-defined method allowing for custom routing logic.

        If None is returned from this method, default routing logic is used.
        """
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
