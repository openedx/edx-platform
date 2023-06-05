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

    from openedx.core.djangoapps.coursegraph import tasks
