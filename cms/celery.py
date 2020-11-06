"""
Import celery, load its settings from the django settings
and auto discover tasks in all installed django apps.

Taken from: https://celery.readthedocs.org/en/latest/django/first-steps-with-django.html
"""


import os

from celery import Celery

from openedx.core.lib.celery.routers import route_task_queue

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cms.envs.production')

APP = Celery('proj')

APP.conf.task_protocol = 1
# Using a string here means the worker will not have to
# pickle the object when using Windows.
APP.config_from_object('django.conf:settings')
APP.autodiscover_tasks()

# Import after autodiscovery has had a chance to connect to the import_module signal
# so celery doesn't miss any apps getting installed.
from django.conf import settings  # pylint: disable=wrong-import-position,wrong-import-order


def route_task(name, args, kwargs, options, task=None, **kw):  # pylint: disable=unused-argument
    """
    Celery-defined method allowing for custom routing logic.

    If None is returned from this method, default routing logic is used.
    """

    return route_task_queue(name, settings.EXPLICIT_QUEUES, settings.ALTERNATE_ENV_TASKS)
