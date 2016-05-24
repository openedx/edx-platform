"""
A cache that is cleared after every request.

This module requires that :class:`request_cache.middleware.RequestCache`
is installed in order to clear the cache after each request.
"""

import logging
from urlparse import urlparse

from celery.signals import task_postrun
import crum
from django.conf import settings
from django.test.client import RequestFactory

from request_cache import middleware


log = logging.getLogger(__name__)


@task_postrun.connect
def clear_request_cache(**kwargs):  # pylint: disable=unused-argument
    """
    Once a celery task completes, clear the request cache to
    prevent memory leaks.
    """
    middleware.RequestCache.clear_request_cache()


def get_cache(name):
    """
    Return the request cache named ``name``.

    Arguments:
        name (str): The name of the request cache to load

    Returns: dict
    """
    return middleware.RequestCache.get_request_cache(name)


def get_request():
    """
    Return the current request.

    Deprecated: Please use crum to retrieve current requests.
    """
    return crum.get_current_request()


def get_request_or_stub():
    """
    Return the current request or a stub request.

    If called outside the context of a request, construct a fake
    request that can be used to build an absolute URI.

    This is useful in cases where we need to pass in a request object
    but don't have an active request (for example, in test cases).
    """
    request = crum.get_current_request()

    if request is None:
        log.warning(
            "Could not retrieve the current request. "
            "A stub request will be created instead using settings.SITE_NAME. "
            "This should be used *only* in test cases, never in production!"
        )

        # The settings SITE_NAME may contain a port number, so we need to
        # parse the full URL.
        full_url = "http://{site_name}".format(site_name=settings.SITE_NAME)
        parsed_url = urlparse(full_url)

        # Construct the fake request.  This can be used to construct absolute
        # URIs to other paths.
        return RequestFactory(
            SERVER_NAME=parsed_url.hostname,
            SERVER_PORT=parsed_url.port or 80,
        ).get("/")

    else:
        return request
