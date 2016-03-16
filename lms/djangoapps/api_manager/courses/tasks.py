"""
This file contains celery tasks for api_manager courses
"""

import sys

from celery.task import task  # pylint: disable=import-error,no-name-in-module
from django.conf import settings
from django.core.cache import cache


@task(name=u'lms.djangoapps.api_manager.courses.tasks.cache_static_tab_content')
def cache_static_tab_contents(cache_key, contents):
    """
    Caches course static tab contents.
    """
    cache_expiration = getattr(settings, 'STATIC_TAB_CONTENTS_CACHE_TTL', 60 * 5)
    contents_max_size_limit = getattr(settings, 'STATIC_TAB_CONTENTS_CACHE_MAX_SIZE_LIMIT', 4000)

    if not sys.getsizeof(contents) > contents_max_size_limit:
        cache.set(cache_key, contents, cache_expiration)
