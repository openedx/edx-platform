"""
Coursegraph Application Configuration

Signal handlers are connected here.
"""


from django.apps import AppConfig


class CoursegraphConfig(AppConfig):
    """
    AppConfig for courseware app
    """
    name = 'openedx.core.djangoapps.coursegraph'

    # In Django 3.2, app configuration is automatically selected from apps.py
    # submodule in case of single config class in apps.py module, to disable
    # this feature we need to set `default = False` in AppConfig of that app
    # https://docs.djangoproject.com/en/3.2/ref/applications/#configuring-applications
    default = False

    from openedx.core.djangoapps.coursegraph import tasks
