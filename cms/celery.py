"""
Import celery, load its settings from the django settings
and auto discover tasks in all installed django apps.

Taken from: https://celery.readthedocs.org/en/latest/django/first-steps-with-django.html
"""
from __future__ import absolute_import

import beeline
import logging
import os

from celery import Celery
from celery.signals import worker_process_init, task_prerun, task_postrun
from django.conf import settings

from openedx.core.lib.celery.routers import AlternateEnvironmentRouter

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
        # The tasks below will be routed to the default lms queue.
        return {
            'completion_aggregator.tasks.update_aggregators': 'lms',
            'openedx.core.djangoapps.content.block_structure.tasks.update_course_in_cache': 'lms',
            'openedx.core.djangoapps.content.block_structure.tasks.update_course_in_cache_v2': 'lms',
        }

    @property
    def explicit_queues(self):
        """
        Defines specific queues for tasks to run in (typically outside of the cms environment),
        as a dict of form { task_name: queue_name }.
        """
        return {
            'lms.djangoapps.grades.tasks.compute_all_grades_for_course': settings.POLICY_CHANGE_GRADES_ROUTING_KEY,
        }


# honeycomb setup
@worker_process_init.connect
def initialize_honeycomb(**kwargs):
    if settings.HONEYCOMB_WRITEKEY and settings.HONEYCOMB_DATASET:
        logging.info('beeline initialization in process pid {}'.format(os.getpid()))
        beeline.init(
            writekey=settings.HONEYCOMB_WRITEKEY,
            dataset=settings.HONEYCOMB_DATASET,
            service_name='cms-celery'
        )


@task_prerun.connect
def start_celery_trace(task_id, task, args, kwargs, **rest_args):
    queue_name = task.request.delivery_info.get("exchange", None)
    task.request.trace = beeline.start_trace(
        context={
            "name": "celery",
            "celery.task_id": task_id,
            "celery.args": args,
            "celery.kwargs": kwargs,
            "celery.task_name": task.name,
            "celery.queue": queue_name,
        }
    )


# optional: finish and send the trace at the end of each task
@task_postrun.connect
def end_celery_trace(task, state, **kwargs):
    beeline.add_field("celery.status", state)
    beeline.finish_trace(task.request.trace)
