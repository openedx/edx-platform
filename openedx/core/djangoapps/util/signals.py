"""
Signal handler for exceptions.
"""
# pylint: disable=unused-argument


import logging

from celery.signals import task_postrun
from django.conf import settings
from django.core.signals import got_request_exception
from django.dispatch import receiver
from edx_django_utils.cache import RequestCache


@receiver(got_request_exception)
def record_request_exception(sender, **kwargs):
    """
    Logs the stack trace whenever an exception
    occurs in processing a request.
    """
    logging.exception("Uncaught exception from {sender}".format(
        sender=sender
    ))


@task_postrun.connect
def _clear_request_cache(**kwargs):
    """
    Once a celery task completes, clear the request cache to
    prevent memory leaks.

    When the celery task is eagerly, it is executed locally
    while sharing the thread and its request cache with the
    active Django Request. In that case, do not clear the cache.
    """
    if getattr(settings, 'CLEAR_REQUEST_CACHE_ON_TASK_COMPLETION', True) and not getattr(settings, 'CELERY_ALWAYS_EAGER', False):
        RequestCache.clear_all_namespaces()
