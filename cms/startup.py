"""
Module with code executed during Studio startup
"""
from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=W0104

from django_startup import autostartup


def run():
    """
    Executed during django startup
    """
    autostartup()
