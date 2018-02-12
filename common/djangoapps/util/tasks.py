"""
This file contains celery tasks not connected to any Django application.
"""
import logging

# from celery.exceptions import MaxRetriesExceededError
from celery.task import task
from django.core import management

log = logging.getLogger('edx.celery.task')


@task()
def run_clearsessions():
    """
    Call the `clearsessions` management command to clean out expired sessions.
    """
    management.call_command('clearsessions')
