"""
Module for code that should run during Studio startup (deprecated)
"""

import django
from django.conf import settings

from openedx.core.djangoapps.monkey_patch import django_db_models_options

# Force settings to run so that the python path is modified

settings.INSTALLED_APPS  # pylint: disable=pointless-statement


def run():
    """
    Executed during django startup

    NOTE: DO **NOT** add additional code to this method or this file! The Platform Team
          is moving all startup code to more standard locations using Django best practices.
    """
    # TODO: Remove Django 1.11 upgrade shim
    # SHIM: We should be able to get rid of this monkey patch post-upgrade
    if django.VERSION[0] == 1 and django.VERSION[1] < 10:
        django_db_models_options.patch()

    django.setup()
