""" Utility functions related to HTTP requests """
from functools import wraps
import logging
import re
import time

from django.conf import settings
from django.db import IntegrityError, transaction

from microsite_configuration import microsite
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey


log = logging.getLogger(__name__)

COURSE_REGEX = re.compile(r'^.*?/courses/{}'.format(settings.COURSE_ID_PATTERN))


def safe_get_host(request):
    """
    Get the host name for this request, as safely as possible.

    If ALLOWED_HOSTS is properly set, this calls request.get_host;
    otherwise, this returns whatever settings.SITE_NAME is set to.

    This ensures we will never accept an untrusted value of get_host()
    """
    if isinstance(settings.ALLOWED_HOSTS, (list, tuple)) and '*' not in settings.ALLOWED_HOSTS:
        return request.get_host()
    else:
        return microsite.get_value('site_domain', settings.SITE_NAME)


def course_id_from_url(url):
    """
    Extracts the course_id from the given `url`.
    """
    if not url:
        return None

    match = COURSE_REGEX.match(url)

    if match is None:
        return None

    course_id = match.group('course_id')

    if course_id is None:
        return None

    try:
        return SlashSeparatedCourseKey.from_deprecated_string(course_id)
    except InvalidKeyError:
        return None


def retry_on_exception(exceptions=(IntegrityError,), delay=0, tries=3, transaction_func=transaction.commit_on_success):
    """
    Retry the decorated function on exception.

    By default transaction.commit_on_success is used around the function.

    Args:
        exceptions (tuple of Exceptions): exceptions to catch.
        delay (float): seconds to wait before retrying.
        tries (integer): the number of times to try the function.
        transaction_func (function): the django transaction function to wrap the decorated function in.
    """

    def retry_on_exception_decorator(func):  # pylint: disable=missing-docstring

        func_path = '{0}.{1}'.format(func.__module__, func.__name__)

        @wraps(func)
        def wrapper(*args, **kwargs):  # pylint: disable=missing-docstring

            for attempt in xrange(1, tries + 1):
                try:
                    with transaction_func():
                        return func(*args, **kwargs)
                except exceptions:
                    if attempt == tries:
                        log.exception('Error in %s on try %d. Raising.', func_path, attempt)
                        raise
                    else:
                        log.exception('Error in %s on try %d. Retrying.', func_path, attempt)

                if delay > 0:
                    time.sleep(delay)
        return wrapper

    return retry_on_exception_decorator
