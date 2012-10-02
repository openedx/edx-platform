"""
A tiny app that checks for a status message.
"""

from django.conf import settings
import logging
import os
import sys

log = logging.getLogger(__name__)

def get_site_status_msg():
    """
    Look for a file settings.STATUS_MESSAGE_PATH.  If found, return the
    contents.  Otherwise, return None.

    If something goes wrong, returns None.  ("is there a status msg?" logic is
    not allowed to break the entire site).
    """
    try:
        content = None
        if os.path.isfile(settings.STATUS_MESSAGE_PATH):
            with open(settings.STATUS_MESSAGE_PATH) as f:
                content = f.read()

        return content
    except:
        log.debug("Error while getting a status message: {0}".format(sys.exc_info()))
        return None
