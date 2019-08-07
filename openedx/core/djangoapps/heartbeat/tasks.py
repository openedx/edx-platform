"""
A trivial task for health checks
"""
from __future__ import absolute_import

from celery.task import task


@task()
def sample_task():
    return True
