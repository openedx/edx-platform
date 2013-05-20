"""
Django Views for service status app
"""

import json
import time

from django.http import HttpResponse

from dogapi import dog_stats_api

from service_status import tasks
from djcelery import celery
from celery.exceptions import TimeoutError


def index(_):
    """
    An empty view
    """
    return HttpResponse()


@dog_stats_api.timed('status.service.celery.status')
def celery_status(_):
    """
    A view that returns Celery stats
    """
    stats = celery.control.inspect().stats() or {}
    return HttpResponse(json.dumps(stats, indent=4),
                        mimetype="application/json")


@dog_stats_api.timed('status.service.celery.ping')
def celery_ping(_):
    """
    A Simple view that checks if Celery can process a simple task
    """
    start = time.time()
    result = tasks.delayed_ping.apply_async(('ping', 0.1))
    task_id = result.id

    # Wait until we get the result
    try:
        value = result.get(timeout=4.0)
        success = True
    except TimeoutError:
        value = None
        success = False

    output = {
        'success': success,
        'task_id': task_id,
        'value': value,
        'time': time.time() - start,
    }

    return HttpResponse(json.dumps(output, indent=4),
                        mimetype="application/json")
