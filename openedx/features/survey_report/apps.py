"""
Survey Report App Configuration.
"""
from django.apps import AppConfig


class SurveyReportConfig(AppConfig):
    """
    Configuration for the survey report Django app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'openedx.features.survey_report'
