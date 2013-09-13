"""
Module for code that should run during LMS startup
"""
import logging

from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=W0104

from django_startup import autostartup

log = logging.getLogger(__name__)

def run():
    """
    Executed during django startup
    """
    autostartup()
