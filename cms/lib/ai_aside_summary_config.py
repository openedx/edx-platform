"""
This file contains AiAsideSummaryConfig class that take a `course_key` and return if:
    * the waffle flag is enabled in ai_aside
    * is the summary is enabled for a given unit_key
    * change the settings for a given unit_key
"""


class AiAsideSummaryConfig:
    """
    Configuration for the AI Aside summary configuration.
    """

    def __init__(self, course_key):
        self.course_key = course_key

    def __str__(self):
        """
        Return user-friendly string.
        """
        return f"AIAside summary configuration for {self.course_key} course"

    def is_enabled(self):
        """
        Define if the waffle flag is enabled for the current course_key
        """
        try:
            from ai_aside.config_api.api import is_summary_config_enabled
            return is_summary_config_enabled(self.course_key)
        except (ModuleNotFoundError, ImportError):
            return False

    def is_summary_enabled(self, unit_key=None):
        """
        Define if the summary configuration is enabled in ai_aside
        """
        try:
            from ai_aside.config_api.api import is_course_settings_present, is_summary_enabled
            if not is_course_settings_present(self.course_key):
                return None
            return is_summary_enabled(self.course_key, unit_key)
        except (ModuleNotFoundError, ImportError):
            return None

    def set_summary_settings(self, unit_key, settings=None):
        """
        Define the settings for a given unit_key in ai_aside
        """
        if settings is None:
            return None

        try:
            from ai_aside.config_api.api import set_unit_settings
            return set_unit_settings(self.course_key, unit_key, settings)
        except (ModuleNotFoundError, ImportError):
            return None
