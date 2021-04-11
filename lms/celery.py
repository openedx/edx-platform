"""
Import celery, load its settings from the django settings
and auto discover tasks in all installed django apps.

Taken from: https://celery.readthedocs.org/en/latest/django/first-steps-with-django.html
"""


import os

from openedx.core.lib.celery.routers import AlternateEnvironmentRouter

# Set the default Django settings module for the 'celery' program
# and then instantiate the Celery singleton.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.envs.production')
from openedx.core.lib.celery import APP  # pylint: disable=wrong-import-position,unused-import


class Router(AlternateEnvironmentRouter):
    """
    An implementation of AlternateEnvironmentRouter, for routing tasks to non-cms queues.
    """

    @property
    def alternate_env_tasks(self):
        """
        Defines alternate environment tasks, as a dict of form { task_name: alternate_queue }
        """
        return {}
