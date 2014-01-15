"""
Module with code executed during Studio startup
"""
from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=W0104

from django_startup import autostartup


# TODO: Remove this code once Studio/CMS runs via wsgi in all environments
INITIALIZED = False


def run():
    """
    Executed during django startup
    """
    global INITIALIZED
    if INITIALIZED:
        return

    INITIALIZED = True
    autostartup()
