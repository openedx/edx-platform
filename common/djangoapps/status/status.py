"""
A tiny app that checks for a status message.
"""

from django.conf import settings
import logging
import os
import sys

from util.cache import cache

log = logging.getLogger(__name__)

def get_site_status_msg():
    """
    Look for a file settings.STATUS_MESSAGE_PATH.  If found, return the
    contents.  Otherwise, return None.  Caches result for 10 seconds, per-machine.

    If something goes wrong, returns None.  ("is there a status msg?" logic is
    not allowed to break the entire site).
    """
    cache_time = 10
    try:
        key = ','.join([settings.HOSTNAME, settings.STATUS_MESSAGE_PATH])
        content = cache.get(key)
        if content == '':
            # cached that there isn't a status message
            return None

        if content is None:
            # nothing in the cache, so check the filesystem
            if os.path.isfile(settings.STATUS_MESSAGE_PATH):
                with open(settings.STATUS_MESSAGE_PATH) as f:
                    content = f.read()
            else:
                # remember that there isn't anything there
                cache.set(key, '', cache_time)
                content = None

        return content
    except:
        log.debug("Error while getting a status message: {0}".format(sys.exc_info()))
        return None
