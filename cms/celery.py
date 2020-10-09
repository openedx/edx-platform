"""
Import celery, load its settings from the django settings
and auto discover tasks in all installed django apps.

Taken from: https://celery.readthedocs.org/en/latest/django/first-steps-with-django.html
"""


import os

from celery import Celery
from django.conf import settings

from openedx.core.lib.celery.routers import ensure_queue_env

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')

APP = Celery('proj')

APP.conf.task_protocol = 1
# Using a string here means the worker will not have to
# pickle the object when using Windows.
APP.config_from_object('django.conf:settings')
APP.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


def route_task(name, args, kwargs, options, task=None, **kw):  # pylint: disable=unused-argument
    """
    Celery-defined method allowing for custom routing logic.

    If None is returned from this method, default routing logic is used.
    """
    # Defines alternate environment tasks, as a dict of form { task_name: alternate_queue }
    alternate_env_tasks = {
        'completion_aggregator.tasks.update_aggregators': 'lms',
        'openedx.core.djangoapps.content.block_structure.tasks.update_course_in_cache': 'lms',
        'openedx.core.djangoapps.content.block_structure.tasks.update_course_in_cache_v2': 'lms',
    }

    # Defines the task -> alternate worker queue to be used when routing.
    explicit_queues = {
        'lms.djangoapps.grades.tasks.compute_all_grades_for_course': {
            'queue': settings.POLICY_CHANGE_GRADES_ROUTING_KEY},
    }
    if name in explicit_queues:
        return explicit_queues[name]

    alternate_env = alternate_env_tasks.get(name, None)
    if alternate_env:
        return ensure_queue_env(alternate_env)

    return None
