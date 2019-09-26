"""
Import celery, load its settings from the django settings
and auto discover tasks in all installed django apps.

Taken from: https://celery.readthedocs.org/en/latest/django/first-steps-with-django.html
"""
from __future__ import absolute_import

import logging
import os

from celery import Celery, signals
from django.conf import settings

from openedx.core.lib.celery.routers import AlternateEnvironmentRouter

LOG = logging.getLogger(__name__)


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


@signals.task_retry.connect
@signals.task_failure.connect
@signals.task_revoked.connect
def on_task_failure(**kwargs):
    """
    Log all exceptions that happen inside celery tasks.
    """
    # celery exceptions will not be published to `sys.excepthook`. therefore we have to create another handler here.
    from traceback import format_list, extract_tb

    traceback = None
    exception = None

    if 'einfo' in kwargs:
        traceback = kwargs['einfo'].tb
        exception = kwargs['einfo'].exception

    traceback = kwargs.get('traceback', traceback)
    exception = kwargs.get('exception', exception)

    if traceback:
        stack_frames = extract_tb(traceback)
    else:
        stack_frames = []

    LOG.error(
        '[task:%s:%s]\n%s\n%s',
        kwargs.get('task_id'),
        kwargs['sender'].request.correlation_id,
        ''.join(format_list(stack_frames)),
        exception
    )
