"""
Module for code that should run during LMS startup
"""
import logging

from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=W0104

from django_startup import autostartup
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)

def run():
    """
    Executed during django startup
    """
    autostartup()

    # Trigger a forced initialization of our modulestores since this can take a while to complete
    # and we want this done before HTTP requests are accepted.
    if settings.INIT_MODULESTORE_ON_STARTUP:
        for store_name in settings.MODULESTORE:
            modulestore(store_name)
