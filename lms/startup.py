"""
Module for code that should run during LMS startup (deprecated)
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
    django_db_models_options.patch()

    django.setup()
