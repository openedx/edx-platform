"""
Import celery, load its settings from the django settings
and auto discover tasks in all installed django apps.

Taken from: http://celery.readthedocs.org/en/latest/django/first-steps-with-django.html
"""
from __future__ import absolute_import

import os

from celery import Celery

from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')

APP = Celery('proj')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
APP.config_from_object('django.conf:settings')
APP.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Some tasks require settings defined on non-lms workers, or they will crash.
# This dict defines those tasks, and the worker environment they should be routed towards.
ALTERNATE_ENV_TASKS = {
}


class Router(object):
    """
    A custom Router class for use in routing celery tasks to non-default queues.
    For more, see http://celery.readthedocs.io/en/latest/userguide/routing.html#routers
    """

    def route_for_task(self, task, args=None, kwargs=None):  # pylint: disable=unused-argument
        """
        Celery-defined method allowing for custom routing logic.

        If None is returned from this method, default routing logic is used.
        """
        alternate_env = ALTERNATE_ENV_TASKS.get(task, None)
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
