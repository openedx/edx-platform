"""
Coursegraph Application Configuration

Signal handlers are connected here.
"""
import warnings

from django.apps import AppConfig


class CoursegraphConfig(AppConfig):
    """
    AppConfig for courseware app
    """
    name = 'cms.djangoapps.coursegraph'

    from cms.djangoapps.coursegraph import tasks

    def ready(self) -> None:
        warnings.warn(
            "Neo4j support is going to be dropped after Sumac release,"
            "to read more here is a github issue https://github.com/openedx/edx-platform/issues/34342",
            DeprecationWarning,
            stacklevel=2
        )
