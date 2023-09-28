"""
Django Celery tasks for service status app
"""


import time

from celery import current_app as celery
from edx_django_utils.monitoring import set_code_owner_attribute


@celery.task
@set_code_owner_attribute
def delayed_ping(value, delay):
    """A simple tasks that replies to a message after a especified amount
    of seconds.
    """
    if value == 'ping':
        result = 'pong'
    else:
        result = f'got: {value}'

    time.sleep(delay)

    return result
