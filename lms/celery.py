"""
Import celery, load its settings from the django settings
and auto discover tasks in all installed django apps.

Taken from: http://celery.readthedocs.org/en/latest/django/first-steps-with-django.html
"""
from __future__ import absolute_import

import os

from celery import Celery
from django.conf import settings


try:
    from openedx.core.lib.celery.routers import AlternateEnvironmentRouter
except ImportError as e:
    import logging
    import subprocess

    log = logging.getLogger(__name__)

    log.debug('OPENEDX MODULE: {}'.format(str(openedx)))
    log.error('OPENEDX MODULE: {}'.format(str(openedx)))

    import openedx
    contents = subprocess.check_output('ls -l {}'.format(openedx.__path__))
    log.debug('OPENEDX MODULE PATH: {}'.format(contents))
    log.error('OPENEDX MODULE PATH: {}'.format(contents))

    raise

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')

APP = Celery('proj')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
APP.config_from_object('django.conf:settings')
APP.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


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
