"""
A tiny app that checks for a status message.
"""

from django.conf import settings
from django.core.cache import cache
import json
import logging
import os

log = logging.getLogger(__name__)


def get_site_status_msg(course_id):
    """
    Look for a file settings.STATUS_MESSAGE_PATH.  If found, read it,
    parse as json, and do the following:

    * if there is a key 'global', include that in the result list.
    * if course is not None, and there is a key for course.id, add that to the result list.
    * return "<br/>".join(result)

    Otherwise, return None.

    If something goes wrong, returns None.  ("is there a status msg?" logic is
    not allowed to break the entire site).
    """
    try:
        # first check for msg in cache
        msg = cache.get('site_status_msg')
        if msg is not None:
            return msg

        if os.path.isfile(settings.STATUS_MESSAGE_PATH):
            with open(settings.STATUS_MESSAGE_PATH) as f:
                content = f.read()
        else:
            return None

        status_dict = json.loads(content)
        msg = status_dict.get('global', None)
        if course_id in status_dict:
            msg = msg + "<br>" if msg else ''
            msg += status_dict[course_id]

        # set msg to cache, with expiry 5 mins
        cache.set('site_status_msg', msg, 60 * 5)
        return msg
    except:
        log.exception("Error while getting a status message.")
        return None
