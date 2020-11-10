"""
Import celery, load its settings from the django settings
and auto discover tasks in all installed django apps.

Taken from: https://celery.readthedocs.org/en/latest/django/first-steps-with-django.html
"""

import os

from celery import Celery

from openedx.core.lib.celery.routers import route_task_queue

# Set the default Django settings module for the 'celery' program
# and then instantiate the Celery singleton.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.envs.production')
from openedx.core.lib.celery import APP  # pylint: disable=wrong-import-position,unused-import


def route_task(name, args, kwargs, options, task=None, **kw):  # pylint: disable=unused-argument
    """
    Celery-defined method allowing for custom routing logic.

    If None is returned from this method, default routing logic is used.
    """

    return route_task_queue(name)
