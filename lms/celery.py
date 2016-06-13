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


class Router(object):

    def route_for_task(self, task, args=None, kwargs=None):
        desired_env = kwargs.pop('desired_queue_env', None)
        if desired_env:
            return self.ensure_queue_env(desired_env)
        return None

    def ensure_queue_env(self, desired_env):
        queues = getattr(settings, 'CELERY_QUEUES', None)
        return next(
            (
                queue
                for queue in queues
                if '.{}.'.format(desired_env) in queue
            ),
            None
        )
