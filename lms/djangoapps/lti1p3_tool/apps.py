"""
Configuration for the lti1p3_tool Django application.
"""
from __future__ import absolute_import

from django.apps import AppConfig


class Lti1p3ToolConfig(AppConfig):
    """
    Configuration class for the lti1p3_tool Django application.
    """
    name = 'lti1p3_tool'
    verbose_name = "LTI1.3 Tool"

    def ready(self):
        # Import the tasks module to ensure that signal handlers are registered.
        from . import signals  # pylint: disable=unused-variable
