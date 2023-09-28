"""
Coursegraph Application Configuration

Signal handlers are connected here.
"""


from django.apps import AppConfig


class CoursegraphConfig(AppConfig):
    """
    AppConfig for courseware app
    """
    name = 'cms.djangoapps.coursegraph'

    from cms.djangoapps.coursegraph import tasks
