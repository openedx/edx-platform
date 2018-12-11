"""
Django Celery tasks for service status app
"""

import time

from djcelery import celery


@celery.task
def delayed_ping(value, delay):
    """A simple tasks that replies to a message after a especified amount
    of seconds.
    """
    if value == 'ping':
        result = 'pong'
    else:
        result = 'got: {0}'.format(value)

    time.sleep(delay)

    return result
